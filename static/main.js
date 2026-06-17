// Front-end logic for NotationLearner — drives the play page, room multiplayer, analysis board, and board toggle.

// Thin wrapper around fetch that sends/receives JSON and returns the parsed response body.
async function apiCall(url, method, body) {
  const options = {
    method: method || "GET",
    headers: { "Content-Type": "application/json" }
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  return await response.json();
}

// Wires up the entire play page: game setup, bot/friend modes, move submission, polling, and end-game handling.
function initPlayPage() {
  const setupDiv = document.getElementById("game-setup");
  const gameArea = document.getElementById("game-area");
  if (!setupDiv || !gameArea) return;

  let selectedOpponent = "Stockfish";
  let selectedColor = "white";
  let selectedBotElo = 1500;
  let hintsEnabled = false;
  let gameResult = null;

  let roomCode = window.ROOM_CODE || null;
  let roomMyColor = null;
  let roomPollInterval = null;
  let lastMoveCount = 0;

  const roomWaiting = document.getElementById("room-waiting");

  const botEloSection = document.getElementById("bot-elo-section");
  const botEloSlider = document.getElementById("bot-elo-slider");
  const botEloValue = document.getElementById("bot-elo-value");
  const hintToggleSection = document.getElementById("hint-toggle-section");
  const hintTogglePregame = document.getElementById("hint-toggle-pregame");

  // Show or hide the bot-only controls (ELO slider, hint toggle) depending on whether the opponent is Stockfish.
  function updateBotOnlyVisibility() {
    const show = selectedOpponent === "Stockfish";
    if (botEloSection) botEloSection.style.display = show ? "block" : "none";
    if (hintToggleSection) hintToggleSection.style.display = show ? "block" : "none";
  }

  if (botEloSlider) {
    botEloSlider.addEventListener("input", function() {
      selectedBotElo = parseInt(this.value, 10);
      if (botEloValue) botEloValue.textContent = selectedBotElo;
    });
  }
  updateBotOnlyVisibility();

  document.querySelectorAll(".nl-setup-opt").forEach(function(btn) {
    btn.addEventListener("click", function() {
      document.querySelectorAll(".nl-setup-opt").forEach(function(b) {
        b.classList.remove("active");
      });
      btn.classList.add("active");
      selectedOpponent = btn.dataset.opponent;
      updateBotOnlyVisibility();
    });
  });

  document.querySelectorAll(".nl-color-opt").forEach(function(btn) {
    btn.addEventListener("click", function() {
      document.querySelectorAll(".nl-color-opt").forEach(function(b) {
        b.classList.remove("active");
      });
      btn.classList.add("active");
      selectedColor = btn.dataset.color;
    });
  });

  document.getElementById("btn-start-game").addEventListener("click", async function() {
    if (selectedOpponent === "Friend") {

      const data = await apiCall("/api/room/create", "POST", { color: selectedColor });
      if (data.success) {
        roomCode = data.code;
        roomMyColor = data.color;
        setupDiv.style.display = "none";
        roomWaiting.style.display = "flex";
        document.getElementById("room-code-display").textContent = roomCode;

        startWaitingPoll();
      }
    } else {

      hintsEnabled =
        selectedOpponent === "Stockfish" &&
        !!(hintTogglePregame && hintTogglePregame.checked);
      const data = await apiCall("/api/game/new", "POST", {
        opponent: selectedOpponent,
        color: selectedColor,
        bot_elo: selectedBotElo
      });
      if (data.success) {
        setupDiv.style.display = "none";
        gameArea.style.display = "block";
        const hintPanel = document.getElementById("hint-panel");
        if (hintPanel) hintPanel.style.display = hintsEnabled ? "block" : "none";
        updateBoard(data);
        if (data.moves_list) updateMoveHistory(data.moves_list);
        if (data.bot_error) showMessage(data.bot_error);
        document.getElementById("move-input").focus();
        if (data.bot_pending) {
          scheduleBotMove();
        }
      }
    }
  });

  document.getElementById("btn-join-game").addEventListener("click", async function() {
    const codeInput = document.getElementById("join-code-input");
    const code = codeInput.value.trim().toUpperCase();
    const joinError = document.getElementById("join-error");
    joinError.style.display = "none";

    if (!code) {
      joinError.textContent = "Please enter a game code.";
      joinError.style.display = "block";
      return;
    }

    const data = await apiCall("/api/room/join", "POST", { code: code });
    if (data.success) {

      window.location.href = "/play/" + data.code;
    } else {
      joinError.textContent = data.error;
      joinError.style.display = "block";
    }
  });

  document.getElementById("join-code-input").addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      document.getElementById("btn-join-game").click();
    }
  });

  document.getElementById("btn-cancel-room").addEventListener("click", function() {
    stopRoomPoll();
    roomWaiting.style.display = "none";
    setupDiv.style.display = "flex";
    roomCode = null;
    roomMyColor = null;
  });

  // Stop polling and show the game-over overlay when the server reports the room expired through inactivity.
  function handleRoomExpired() {
    stopRoomPoll();
    roomWaiting.style.display = "none";
    gameArea.style.display = "block";
    showGameOver("Game expired due to inactivity.", null);
  }

  // Poll the room every 2s while waiting for an opponent, switching to the live game once the room is active.
  function startWaitingPoll() {
    roomPollInterval = setInterval(async function() {
      const data = await apiCall("/api/room/state/" + roomCode, "GET");
      if (!data.success && data.expired) {
        handleRoomExpired();
        return;
      }
      if (data.success && data.status === "active") {

        stopRoomPoll();
        roomMyColor = data.my_color;
        roomWaiting.style.display = "none";
        gameArea.style.display = "block";
        lastMoveCount = data.move_count;
        updateBoard(data);
        updateMoveHistory(data.moves_list || []);
        updateTurnIndicator(data);
        document.getElementById("move-input").focus();

        startRoomGamePoll();
      }
    }, 2000);
  }

  // Cancel any active room polling interval and clear its handle.
  function stopRoomPoll() {
    if (roomPollInterval) {
      clearInterval(roomPollInterval);
      roomPollInterval = null;
    }
  }

  // Poll the active room every 1.5s, refreshing the board on opponent moves and detecting game-over/resignation.
  function startRoomGamePoll() {
    roomPollInterval = setInterval(async function() {
      const data = await apiCall("/api/room/state/" + roomCode, "GET");
      if (!data.success && data.expired) {
        handleRoomExpired();
        return;
      }
      if (data.success) {
        if (data.move_count !== lastMoveCount) {
          lastMoveCount = data.move_count;
          updateBoard(data);
          updateMoveHistory(data.moves_list || []);
          updateTurnIndicator(data);

          if (data.is_game_over) {
            gameResult = data.result;
            let msg = "Game over.";
            if (data.result === "1-0") msg = "Checkmate! White wins!";
            else if (data.result === "0-1") msg = "Checkmate! Black wins!";
            else msg = "Draw.";
            showGameOver(msg, data.result);
            stopRoomPoll();
          }
        }

        if (data.status === "finished" && !data.is_game_over) {
          gameResult = data.result;
          showGameOver("Opponent resigned. You win!", data.result);
          stopRoomPoll();
        }
      }
    }, 1500);
  }

  // Update the status text in a room game to show whose turn it is and whether we're waiting on the opponent.
  function updateTurnIndicator(data) {
    if (roomCode && data.is_my_turn !== undefined) {
      var statusText = data.turn + " to move";
      if (!data.is_my_turn) {
        statusText += " (waiting for opponent)";
      }
      document.getElementById("game-status").textContent = statusText;
    }
  }

  document.getElementById("move-form").addEventListener("submit", async function(e) {
    e.preventDefault();
    const input = document.getElementById("move-input");
    const moveStr = input.value.trim();
    if (!moveStr) return;

    hideError();
    hideMessage();

    var data;
    if (roomCode) {

      data = await apiCall("/api/room/move/" + roomCode, "POST", { move: moveStr });
    } else {

      data = await apiCall("/api/game/move", "POST", { move: moveStr });
    }

    if (!data.success && data.expired) {
      handleRoomExpired();
      return;
    }

    if (data.success) {
      input.value = "";
      lastMoveCount = data.move_count;
      updateBoard(data);
      updateMoveHistory(data.moves_list);

      if (data.bot_error) {
        showMessage(data.bot_error);
      } else if (data.message) {
        showMessage(data.message);
      }

      if (data.is_game_over) {
        gameResult = data.result;
        showGameOver(data.message, data.result);
        if (roomCode) stopRoomPoll();
      } else if (data.bot_pending) {
        scheduleBotMove();
      }
    } else {
      showError(data.error);
    }
    input.focus();
  });

  // After the player moves, disable input and request the bot's reply after a short randomised "thinking" delay.
  function scheduleBotMove() {
    const input = document.getElementById("move-input");
    const status = document.getElementById("game-status");
    input.disabled = true;
    if (status) status.textContent = "Bot is thinking…";

    const delayMs = 500 + Math.floor(Math.random() * 700);
    setTimeout(async function() {
      const data = await apiCall("/api/game/bot-move", "POST");
      if (data.success) {
        lastMoveCount = data.move_count;
        updateBoard(data);
        updateMoveHistory(data.moves_list);
        if (data.message) showMessage(data.message);
        if (data.is_game_over) {
          gameResult = data.result;
          showGameOver(data.message, data.result);
        }
      } else {
        showMessage(data.error || "Bot move failed.");
      }
      input.disabled = false;
      input.focus();
    }, delayMs);
  }

  const getHintBtn = document.getElementById("btn-get-hint");
  if (getHintBtn) {
    getHintBtn.addEventListener("click", async function() {
      const resultDiv = document.getElementById("hint-result");
      resultDiv.innerHTML = '<span class="nl-hint-loading">Thinking...</span>';
      const data = await apiCall("/api/game/hint", "GET");
      if (data.success) {
        resultDiv.innerHTML =
          '<div class="nl-hint-move">Suggested: <strong>' + data.hint_move + '</strong></div>' +
          '<div class="nl-hint-eval">Evaluation: ' + data.evaluation + '</div>';
      } else {
        resultDiv.innerHTML = '<div class="nl-hint-error">' + data.error + '</div>';
      }
    });
  }

  document.getElementById("help-toggle").addEventListener("click", function() {
    const content = document.getElementById("help-content");
    const chevron = this.querySelector(".nl-chevron");
    if (content.style.display === "none") {
      content.style.display = "block";
      chevron.classList.remove("bi-chevron-down");
      chevron.classList.add("bi-chevron-up");
    } else {
      content.style.display = "none";
      chevron.classList.remove("bi-chevron-up");
      chevron.classList.add("bi-chevron-down");
    }
  });

  document.getElementById("btn-resign").addEventListener("click", async function() {
    if (!confirm("Are you sure you want to resign?")) return;

    var data;
    if (roomCode) {
      data = await apiCall("/api/room/resign/" + roomCode, "POST");
    } else {
      data = await apiCall("/api/game/resign", "POST");
    }
    if (data.success) {
      gameResult = data.result;
      showGameOver(data.message, data.result);
      if (roomCode) stopRoomPoll();
    }
  });

  document.getElementById("btn-new-game").addEventListener("click", function() {
    if (!confirm("Start a new game? Current game will be lost.")) return;
    if (roomCode) stopRoomPoll();
    roomCode = null;
    roomMyColor = null;
    gameArea.style.display = "none";
    setupDiv.style.display = "flex";
    resetUI();
  });

  document.getElementById("btn-save-game").addEventListener("click", async function() {
    var data;
    if (roomCode) {
      data = await apiCall("/api/room/save/" + roomCode, "POST");
    } else {
      data = await apiCall("/api/game/save", "POST", { result: gameResult });
    }
    if (data.success) {
      alert("Game saved! Redirecting to your profile...");
      window.location.href = "/profile";
    } else {
      alert("Error saving game: " + data.error);
    }
  });

  document.getElementById("btn-play-again").addEventListener("click", function() {
    document.getElementById("game-over-overlay").style.display = "none";
    if (roomCode) stopRoomPoll();
    roomCode = null;
    roomMyColor = null;
    gameArea.style.display = "none";
    setupDiv.style.display = "flex";
    resetUI();
  });

  if (roomCode) {

    initRoomGame();
  } else {
    checkExistingGame();
  }

  // Bootstrap a room loaded directly via /play/<code>, choosing the waiting/active/finished view from its status.
  async function initRoomGame() {
    const data = await apiCall("/api/room/state/" + roomCode, "GET");
    if (!data.success) {

      return;
    }
    roomMyColor = data.my_color;

    if (data.status === "waiting") {

      setupDiv.style.display = "none";
      roomWaiting.style.display = "flex";
      document.getElementById("room-code-display").textContent = roomCode;
      startWaitingPoll();
    } else if (data.status === "active") {
      setupDiv.style.display = "none";
      gameArea.style.display = "block";
      lastMoveCount = data.move_count;
      updateBoard(data);
      updateMoveHistory(data.moves_list || []);
      updateTurnIndicator(data);
      document.getElementById("move-input").focus();
      startRoomGamePoll();
    } else if (data.status === "finished") {
      setupDiv.style.display = "none";
      gameArea.style.display = "block";
      updateBoard(data);
      updateMoveHistory(data.moves_list || []);
      gameResult = data.result;
      showGameOver("Game finished.", data.result);
    }
  }

  // On load, resume a single-player game already in progress in the session so a page refresh doesn't lose it.
  async function checkExistingGame() {
    const data = await apiCall("/api/game/state", "GET");
    if (data.success && data.active) {
      setupDiv.style.display = "none";
      gameArea.style.display = "block";
      updateBoard(data);
      updateMoveHistory(data.moves_list || []);
    }
  }

  // Swap in the latest board SVG and update the status text and move-number label from a response payload.
  function updateBoard(data) {
    document.getElementById("board-container").innerHTML = data.svg;
    document.getElementById("game-status").textContent =
      data.is_game_over ? "Game Over" : data.turn + " to move";
    var moveNum = Math.floor(data.move_count / 2) + 1;
    document.getElementById("game-move-count").textContent = "Move " + moveNum;
  }

  // Render the move list into a paired White/Black history table and scroll it to the most recent move.
  function updateMoveHistory(movesList) {
    const container = document.getElementById("move-history");
    if (!movesList || movesList.length === 0) {
      container.innerHTML = '<p class="nl-empty-state">No moves yet.</p>';
      return;
    }
    let html = '<table class="nl-history-table"><thead><tr><th>#</th><th>White</th><th>Black</th></tr></thead><tbody>';
    for (let i = 0; i < movesList.length; i += 2) {
      const num = Math.floor(i / 2) + 1;
      const white = movesList[i] || "";
      const black = movesList[i + 1] || "";
      html += "<tr><td>" + num + ".</td><td>" + white + "</td><td>" + black + "</td></tr>";
    }
    html += "</tbody></table>";
    container.innerHTML = html;
    container.scrollTop = container.scrollHeight;
  }

  // Display an inline error message below the move input (e.g. illegal/invalid notation).
  function showError(msg) {
    const el = document.getElementById("move-error");
    el.textContent = msg;
    el.style.display = "block";
  }

  // Hide the inline move-error message.
  function hideError() {
    document.getElementById("move-error").style.display = "none";
  }

  // Display an informational message below the move input (e.g. check announcements, bot notices).
  function showMessage(msg) {
    const el = document.getElementById("move-message");
    el.textContent = msg;
    el.style.display = "block";
  }

  // Hide the inline informational message.
  function hideMessage() {
    document.getElementById("move-message").style.display = "none";
  }

  // Show the end-of-game overlay with the outcome message and lock the move input.
  function showGameOver(message, result) {
    document.getElementById("game-over-title").textContent = "Game Over";
    document.getElementById("game-over-message").textContent = message;
    document.getElementById("game-over-overlay").style.display = "flex";
    document.getElementById("move-input").disabled = true;
  }

  // Clear the board, history, inputs, hints, and overlays back to the pre-game state when starting over.
  function resetUI() {
    document.getElementById("move-history").innerHTML = '<p class="nl-empty-state">No moves yet.</p>';
    document.getElementById("board-container").innerHTML = "";
    document.getElementById("move-input").value = "";
    document.getElementById("move-input").disabled = false;
    document.getElementById("game-over-overlay").style.display = "none";
    const hintResult = document.getElementById("hint-result");
    if (hintResult) hintResult.innerHTML = "";
    const hintPanel = document.getElementById("hint-panel");
    if (hintPanel) hintPanel.style.display = "none";
    hideError();
    hideMessage();
    gameResult = null;
    lastMoveCount = 0;
  }
}

// Wires up the analysis page: loads a saved game and lets the user step through positions with engine evaluation.
function initAnalysePage() {
  if (typeof window.ANALYSE_GAME_ID === "undefined") return;

  const gameId = window.ANALYSE_GAME_ID;
  let gameData = null;
  let currentMoveIndex = -1;

  loadGame();

  // Fetch the saved game's moves and metadata, then render the starting position, move list, and initial analysis.
  async function loadGame() {
    const data = await apiCall("/api/analyse/" + gameId, "GET");
    if (!data.success) {
      alert("Could not load game data.");
      return;
    }
    gameData = data;
    currentMoveIndex = -1;

    document.getElementById("analyse-board").innerHTML = data.start_svg;
    updatePositionLabel();
    renderMoveList();
    fetchBestMove(data.start_fen);
  }

  document.getElementById("btn-start").addEventListener("click", function() {
    goToMove(-1);
  });

  document.getElementById("btn-prev").addEventListener("click", function() {
    if (currentMoveIndex > -1) {
      goToMove(currentMoveIndex - 1);
    }
  });

  document.getElementById("btn-next").addEventListener("click", function() {
    if (gameData && currentMoveIndex < gameData.moves.length - 1) {
      goToMove(currentMoveIndex + 1);
    }
  });

  document.getElementById("btn-end").addEventListener("click", function() {
    if (gameData) {
      goToMove(gameData.moves.length - 1);
    }
  });

  document.addEventListener("keydown", function(e) {
    if (e.key === "ArrowLeft") {
      document.getElementById("btn-prev").click();
    } else if (e.key === "ArrowRight") {
      document.getElementById("btn-next").click();
    } else if (e.key === "Home") {
      document.getElementById("btn-start").click();
    } else if (e.key === "End") {
      document.getElementById("btn-end").click();
    }
  });

  // Jump to a given move index: fetch that position's board SVG, update labels/highlight, and re-run analysis.
  async function goToMove(index) {
    if (!gameData) return;

    currentMoveIndex = index;
    let fen;
    if (index === -1) {
      fen = gameData.start_fen;
    } else {
      fen = gameData.moves[index].fen_after;
    }

    const data = await apiCall("/api/analyse/svg", "POST", {
      fen: fen,
      orientation: gameData.color,
    });
    if (data.success) {
      document.getElementById("analyse-board").innerHTML = data.svg;
    }
    updatePositionLabel();
    highlightCurrentMove();
    fetchBestMove(fen);
  }

  // Update the evaluation bar width and numeric label from a normalised score (-1..1) and optional mate count.
  function renderEval(scoreNorm, mateIn) {
    const fill = document.getElementById("analyse-eval-fill");
    const number = document.getElementById("analyse-eval-number");
    if (!fill || !number) return;

    if (scoreNorm === null || scoreNorm === undefined) {
      fill.style.width = "50%";
      number.textContent = "—";
      return;
    }
    const clamped = Math.max(-1, Math.min(1, scoreNorm));
    fill.style.width = ((clamped + 1) / 2 * 100).toFixed(1) + "%";
    let label = (clamped >= 0 ? "+" : "") + clamped.toFixed(2);
    if (mateIn !== null && mateIn !== undefined) {
      label += " (Mate in " + Math.abs(mateIn) + ")";
    }
    number.textContent = label;
  }

  // Ask the server for Stockfish's best move and evaluation of a FEN, then render them into the analysis panel.
  async function fetchBestMove(fen) {
    const container = document.getElementById("analyse-bestmove");
    if (!container) return;
    container.innerHTML = '<span class="nl-hint-loading">Analysing...</span>';
    renderEval(null);

    const data = await apiCall("/api/analyse/bestmove", "POST", { fen: fen });
    if (data.success) {
      renderEval(data.score_norm, data.mate_in);
      if (data.best_move) {
        container.innerHTML =
          '<div class="nl-hint-move"><i class="bi bi-cpu me-1"></i> Best move: <strong>' + data.best_move + '</strong></div>' +
          '<div class="nl-hint-eval">Evaluation: ' + data.evaluation + '</div>';
      } else {
        container.innerHTML = '<span class="nl-hint-loading">' + (data.evaluation || "No analysis available.") + '</span>';
      }
    } else {
      renderEval(null);
      container.innerHTML = '<div class="nl-hint-error">' + (data.error || "Stockfish not available.") + '</div>';
    }
  }

  // Set the position label to "Start" or the move number/colour/notation of the currently viewed move.
  function updatePositionLabel() {
    const label = document.getElementById("analyse-position");
    if (currentMoveIndex === -1) {
      label.textContent = "Start";
    } else {
      const m = gameData.moves[currentMoveIndex];
      const moveNum = Math.floor(currentMoveIndex / 2) + 1;
      const colorLabel = m.color === "white" ? "" : "...";
      label.textContent = moveNum + "." + colorLabel + " " + m.notation;
    }
  }

  // Build the clickable move-history table for the analysed game, wiring each cell to jump to that position.
  function renderMoveList() {
    const container = document.getElementById("analyse-moves");
    if (!gameData || gameData.moves.length === 0) {
      container.innerHTML = '<p class="nl-empty-state">No moves in this game.</p>';
      return;
    }
    let html = '<table class="nl-history-table"><thead><tr><th>#</th><th>White</th><th>Black</th></tr></thead><tbody>';
    for (let i = 0; i < gameData.moves.length; i += 2) {
      const num = Math.floor(i / 2) + 1;
      const whiteMove = gameData.moves[i];
      const blackMove = gameData.moves[i + 1];
      html += "<tr>";
      html += "<td>" + num + ".</td>";
      html += '<td class="nl-analyse-move" data-index="' + i + '">' + (whiteMove ? whiteMove.notation : "") + "</td>";
      html += '<td class="nl-analyse-move" data-index="' + (i + 1) + '">' + (blackMove ? blackMove.notation : "") + "</td>";
      html += "</tr>";
    }
    html += "</tbody></table>";
    container.innerHTML = html;

    container.querySelectorAll(".nl-analyse-move").forEach(function(td) {
      td.addEventListener("click", function() {
        const idx = parseInt(this.dataset.index, 10);
        if (gameData.moves[idx]) {
          goToMove(idx);
        }
      });
    });
  }

  // Highlight the move-list cell matching the current position and scroll it into view, clearing prior highlights.
  function highlightCurrentMove() {
    document.querySelectorAll(".nl-analyse-move").forEach(function(el) {
      el.classList.remove("nl-analyse-move--active");
    });
    if (currentMoveIndex >= 0) {
      const active = document.querySelector('.nl-analyse-move[data-index="' + currentMoveIndex + '"]');
      if (active) {
        active.classList.add("nl-analyse-move--active");
        active.scrollIntoView({ block: "nearest" });
      }
    }
  }
}

// Wires up the show/hide board button, persisting the user's preference in localStorage across visits.
function initBoardVisibilityToggle() {
  const btn = document.getElementById("btn-toggle-board");
  if (!btn) return;
  const board =
    document.getElementById("board-container") ||
    document.getElementById("analyse-board");
  if (!board) return;

  const STORAGE_KEY = "nl-board-hidden";
  // Apply the hidden/shown state to the board element and sync the button's icon, label, and aria-pressed.
  const apply = (hidden) => {
    board.classList.toggle("nl-board-container--hidden", hidden);
    btn.setAttribute("aria-pressed", String(hidden));
    const icon = btn.querySelector("i");
    const label = btn.querySelector(".nl-board-toggle-label");
    if (icon) icon.className = hidden ? "bi bi-eye" : "bi bi-eye-slash";
    if (label) label.textContent = hidden ? "Show board" : "Hide board";
  };

  apply(localStorage.getItem(STORAGE_KEY) === "1");
  btn.addEventListener("click", () => {
    const next = !board.classList.contains("nl-board-container--hidden");
    localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
    apply(next);
  });
}

// On page load, initialise whichever of the three features is present in the current page's DOM.
document.addEventListener("DOMContentLoaded", function() {
  initPlayPage();
  initAnalysePage();
  initBoardVisibilityToggle();
});
