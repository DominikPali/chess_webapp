async function api(url, method = "GET", body = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json"
    }
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  return response.json();
}

function initPlayPage() {
  const root = document.getElementById("game-page");
  if (!root) {
    return;
  }

  const setupPanel = document.getElementById("setup-panel");
  const boardPanel = document.getElementById("board-panel");
  const boardBox = document.getElementById("board-box");
  const statusText = document.getElementById("status-text");
  const moveCount = document.getElementById("move-count");
  const messageText = document.getElementById("message-text");
  const historyBox = document.getElementById("history-box");
  const moveForm = document.getElementById("move-form");
  const moveInput = document.getElementById("move-input");
  const formError = document.getElementById("form-error");
  const saveGameButton = document.getElementById("save-game");

  function showSetup() {
    setupPanel.hidden = false;
    boardPanel.hidden = true;
    boardBox.innerHTML = "";
    historyBox.innerHTML = '<p class="muted-text">No moves yet.</p>';
    messageText.textContent = "";
    formError.hidden = true;
    formError.textContent = "";
    moveInput.value = "";
    moveInput.disabled = false;
    saveGameButton.hidden = true;
  }

  function showBoard() {
    setupPanel.hidden = true;
    boardPanel.hidden = false;
  }

  function renderHistory(moves) {
    if (!moves || moves.length === 0) {
      historyBox.innerHTML = '<p class="muted-text">No moves yet.</p>';
      return;
    }
    let html = '<table class="history-table"><thead><tr><th>#</th><th>White</th><th>Black</th></tr></thead><tbody>';
    for (let i = 0; i < moves.length; i += 2) {
      const moveNumber = Math.floor(i / 2) + 1;
      const whiteMove = moves[i] || "";
      const blackMove = moves[i + 1] || "";
      html += `<tr><td>${moveNumber}.</td><td>${whiteMove}</td><td>${blackMove}</td></tr>`;
    }
    html += "</tbody></table>";
    historyBox.innerHTML = html;
  }

  function renderState(data) {
    showBoard();
    boardBox.innerHTML = data.svg || "";
    statusText.textContent = data.is_game_over ? "Game finished" : `${data.turn} to move`;
    moveCount.textContent = `Move ${Math.floor(data.move_count / 2) + 1}`;
    messageText.textContent = data.message || "";
    renderHistory(data.moves_list || []);
    formError.hidden = true;
    formError.textContent = "";
    const finished = Boolean(data.is_game_over || data.result);
    moveInput.disabled = finished || !data.is_my_turn;
    if (!finished && data.is_my_turn) {
      moveInput.focus();
    }
    saveGameButton.hidden = !finished;
  }

  async function loadCurrentGame() {
    const data = await api("/api/game/state");
    if (data.success && data.svg) {
      renderState(data);
    } else {
      showSetup();
    }
  }

  document.getElementById("start-game").addEventListener("click", async function () {
    const selected = document.querySelector('input[name="player-color"]:checked');
    const color = selected ? selected.value : "white";
    const data = await api("/api/game/new", "POST", { color });
    if (data.success) {
      renderState(data);
    }
  });

  moveForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const move = moveInput.value.trim();
    if (!move) {
      return;
    }
    const data = await api("/api/game/move", "POST", { move });
    if (data.success) {
      moveInput.value = "";
      renderState(data);
    } else {
      formError.hidden = false;
      formError.textContent = data.error || "Move could not be played.";
    }
  });

  document.getElementById("resign-game").addEventListener("click", async function () {
    const data = await api("/api/game/resign", "POST");
    if (data.success) {
      const state = await api("/api/game/state");
      if (state.success && state.svg) {
        state.message = data.message;
        state.result = data.result;
        state.is_game_over = true;
        renderState(state);
      }
    }
  });

  document.getElementById("new-game").addEventListener("click", function () {
    showSetup();
  });

  saveGameButton.addEventListener("click", async function () {
    const data = await api("/api/game/save", "POST");
    if (data.success) {
      window.location.href = "/profile";
    } else {
      formError.hidden = false;
      formError.textContent = data.error || "Game could not be saved.";
    }
  });

  loadCurrentGame();
}

document.addEventListener("DOMContentLoaded", function () {
  initPlayPage();
});
