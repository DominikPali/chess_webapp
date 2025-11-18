from board import board

class Piece():
    def __init__(self, x, y, color, board):
        self.x = x
        self.y = y
        self.color = color
        self.board = board
        self.board[x][y] = self


class Pawn(Piece):
    def calculate_semi_legal_moves(self):
        moves = []

        return moves


class Knight(Piece):
    def calculate_semi_legal_moves(self):
        possible_moves = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
        moves = []
        for delta_X, delta_Y in possible_moves:
            displacement_X = self.x + delta_X
            displacement_Y = self.y + delta_Y
            if (0 <= displacement_X <= 7) and (0 <= displacement_Y <= 7): ##Checks whether the considered move is still in range of the board
                piece_at = self.board.get_piece_at(displacement_X, displacement_Y)
                if piece_at is None:
                    moves.append((delta_X, delta_Y))
                else:
                    if piece_at.color != self.color:
                        moves.append((delta_X, delta_Y))
        return moves


class Bishop(Piece):
    #As the bishop moves diagonally the program will check possible moves using a loop (it will end when it finds and obstacle on the path)
    possible_path_directions = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
    path_positions = [(0, 0) for _ in range(4)]
    while len(possible_path_directions) != 0:
        pass # Finish writing logic for the semi_legal movement of all pieces


class Rook(Piece):
    pass


class Queen(Piece):
    pass


class King(Piece):
    pass
