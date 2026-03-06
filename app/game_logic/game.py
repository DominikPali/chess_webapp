"""
Chess board controller - hangles game control 
Uses python-chess library for full chess game control
"""

import chess
import sys
from typing import Optional, List

class BoardManager:
    def __init__(self):
        """Initializing new chess game (board) in starting state"""
        self.board = chess.Board()
    
    def get_legal_moves(self) -> List[chess.Move]:
        """
        Analyzes the board and gets all the legal moves on the board 
        
        Returns:
            - List of legal Move objects
        """
        return list(self.board.legal_moves)
    
    def is_legal_move(self, move_san: str) -> bool:
        """
        Checks whether the move in algebraic notation is legal
        
        Args:
            - move_san: Move in Standard Algebraic Notation (string)
        
        Returns:
             - True if move is legal, False if it is not
        """
        try:
            move = self.board.parse_san(move_san)
            return move in self.board.legal_moves
        except (chess.InvalidMoveError, chess.IllegalMoveError, chess.AmbiguousMoveError):
            return False
    
    def apply_move(self, move_san: str) -> bool:
        """
        Executes the move if it is legal
        
        Args:
            - move_san: Move in Standard Algebraic Notation (string)
        
        Returns:
            - True if move was applied successfully, False if not
        """
        try:
            move = self.board.parse_san(move_san)
            if(self.is_legal_move(move_san)):
                self.board.push(move)
                return True
            return False
        except (chess.InvalidMoveError, chess.IllegalMoveError, chess.AmbiguousMoveError):
            return False
    
    def get_ascii_board(self) -> str:
        """
        Gets ASCII representation of the current board
        
        Returns:
            - String representation of the board
        """
        return str(self.board)
    
    def get_fen(self) -> str:
        """
        Get FEN (Forsyth-Edwards Notation) of current position
        
        Returns:
            - FEN string
        """
        return self.board.fen()
    
    def get_pgn(self) -> str:
        """
        Get PGN (Portable Game Notation) of the game.
        
        Returns:
            - PGN string with move history (string)
        """
        game = chess.pgn.Game.from_board(self.board)
        return str(game)
    
    def is_game_over(self) -> bool:
        """
        Check if the game has ended
        
        Returns:
            - True if game is over, False if not
        """
        return self.board.is_game_over()
    
    def get_outcome(self) -> Optional[str]:
        """
        Get the outcome of the game if it's over.
        
        Returns:
            - String describing the outcome, or None if game is not over
        """
        if not self.board.is_game_over():
            return None
        
        outcome = self.board.outcome()
        
        if outcome is None:
            return "Game ended"
        
        if outcome.winner is None:
            # Draw
            if self.board.is_stalemate():
                return "Draw by stalemate"
            elif self.board.is_insufficient_material():
                return "Draw by insufficient material"
            elif self.board.is_seventyfive_moves():
                return "Draw by 75-move rule"
            elif self.board.is_fivefold_repetition():
                return "Draw by fivefold repetition"
            else:
                return "Draw"
        else:
            # Checkmate
            winner = "White" if outcome.winner == chess.WHITE else "Black"
            return f"Checkmate! {winner} wins!"
    
    def is_check(self) -> bool:
        """
        Check if the current player is in check
        
        Returns:
            True if in check, False if not
        """
        return self.board.is_check()
    
    def get_current_turn(self) -> str:
        """
        Get whose turn it is
        
        Returns:
            - 'White' or 'Black' (string)
        """
        return "White" if self.board.turn == chess.WHITE else "Black"
    
    def get_move_count(self) -> int:
        """
        Get the number of moves played
        
        Returns:
             - Number of half-moves (int)
        """
        return len(self.board.move_stack)


class MoveProvider:
    """
    Handles input for moves.
    """
    
    def get_move(self, player: str) -> Optional[str]:
        """
        Get a move from the player via console input.

        Args:
            - player: Name of the player ('White' or 'Black')

        Returns:
            - Move string in algebraic notation, or None if quit requested
        """
        try:
            move = input(f"{player} to move (or 'quit' to exit): ").strip()
            if move.lower() in ['quit', 'exit', 'q']:
                return None
            return move
        except (EOFError, KeyboardInterrupt):
            return None


class OutputManager:
    """
    Handles all output to the console.
    Provides methods for displaying board state, messages, and results.
    """
    
    @staticmethod
    def print_board(board_str: str, turn: str, move_count: int):
        """
        Print the current board state.

        Args:
            - board_str: ASCII representation of the board
            - turn: Whose turn it is
            - move_count: Number of half-moves played
        """
        print("\n" + "="*50)
        print(f"Move {move_count // 2 + 1} - {turn}'s turn")
        print("="*50)
        print(board_str)
        print()
    
    @staticmethod
    def print_check_warning():
        """Print a warning that the king is in check."""
        print("CHECK!")
        print()
    
    @staticmethod
    def print_move_confirmation(move: str):
        """
        Print confirmation that a move was applied.

        Args:
            - move: The move that was applied
        """
        print(f"✓ Move applied: {move}")
    
    @staticmethod
    def print_error(message: str):
        """
        Print an error message.

        Args:
            - message: Error message to display
        """
        print(f"✗ Error: {message}")
    
    @staticmethod
    def print_game_over(outcome: str, pgn: str):
        """
        Print game over information.

        Args:
            - outcome: Description of the game outcome
            - pgn: PGN notation of the game
        """
        print("\n" + "="*50)
        print("GAME OVER")
        print("="*50)
        print(outcome)
        print("\nGame History (PGN):")
        print("-"*50)
        print(pgn)
        print("="*50)
    
    @staticmethod
    def print_welcome():
        """Print welcome message and instructions."""
        print("\n" + "="*50)
        print("♟️  CHESS GAME CONTROLLER ♟️")
        print("="*50)
        print("\nInstructions:")
        print("- Enter moves in algebraic notation (e.g., e4, Nf3, O-O)")
        print("- Type 'quit' or 'exit' to end the game")
        print("- Illegal moves will be rejected")
        print("\nLet's begin!\n")
    
    @staticmethod
    def print_goodbye():
        """Print goodbye message."""
        print("\nThank you for playing! Goodbye!\n")


class GameController:
    """
    Main game controller that orchestrates the chess game.
    Manages the game loop, coordinates between components, and handles game flow.
    """
    
    def __init__(self):
        """Initialize the game controller with all necessary components."""
        self.board_manager = BoardManager()
        self.move_provider = MoveProvider()
        self.output_manager = OutputManager()
        self.running = False
    
    def start_game(self):
        """
        Start the chess game and run the main game loop.
        """
        self.running = True
        self.output_manager.print_welcome()
        
        # Main game loop
        while self.running and not self.board_manager.is_game_over():
            self._play_turn()
        
        # Game ended
        if self.board_manager.is_game_over():
            self._handle_game_over()
        else:
            self.output_manager.print_goodbye()
    
    def _play_turn(self):
        """
        Execute a single turn in the game.
        Displays board, gets move input, validates, and applies the move.
        """
        # Display current board state
        current_turn = self.board_manager.get_current_turn()
        move_count = self.board_manager.get_move_count()
        board_str = self.board_manager.get_ascii_board()
        
        self.output_manager.print_board(board_str, current_turn, move_count)
        
        # Check if king is in check
        if self.board_manager.is_check():
            self.output_manager.print_check_warning()
        
        # Get move from player
        move_input = self.move_provider.get_move(current_turn)
        
        # Handle quit request
        if move_input is None:
            self.running = False
            return
        
        # Validate and apply move
        if self._validate_and_apply_move(move_input):
            self.output_manager.print_move_confirmation(move_input)
        else:
            self.output_manager.print_error(
                f"Invalid or illegal move: '{move_input}'. Please try again."
            )
    
    def _validate_and_apply_move(self, move_san: str) -> bool:
        """
        Validate move format and legality, then apply if valid.

        Args:
            - move_san: Move in algebraic notation

        Returns:
            - True if move was successfully applied, False otherwise
        """
        if not move_san:
            return False
        
        return self.board_manager.apply_move(move_san)
    
    def _handle_game_over(self):
        """
        Handle game over state - display outcome and game history.
        """
        outcome = self.board_manager.get_outcome()
        pgn = self.board_manager.get_pgn()
        
        # Display final board position
        board_str = self.board_manager.get_ascii_board()
        print("\nFinal Position:")
        print(board_str)
        
        # Display game results
        self.output_manager.print_game_over(outcome, pgn)


def main():
    """
    Main entry point for the chess game.
    """
    try:
        controller = GameController()
        controller.start_game()
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user. Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nAn unexpected error occurred: {e}")
        print("Please report this issue if it persists.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()