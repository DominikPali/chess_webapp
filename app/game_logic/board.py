from pieces import Pawn, Knight, Bishop, Rook, Queen, King
class Board():
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.active_pieces = []
        self.inactive_pieces = []
        self.setup_starting_position()

    def setup_starting_position(self):
        #Setting up the white pieces
        for pos_x in range(8):
            Pawn(x=pos_x, y=1, color="W", board=self)
        for pos_x in [0, 7]:
            Rook(x=pos_x, y=0, color="W", board=self)
        for pos_x in [1, 6]:
            Knight(x=pos_x, y=0, color="W", board=self)
        for pos_x in [2, 5]:
            Bishop(x=pos_x, y=0, color="W", board=self)
        King(x=4, y=0, color="W", board=self)
        Queen(x=3, y=0, color="W", board=self)

        #Setting up the black pieces
        for pos_x in range(8):
            Pawn(x=pos_x, y=6, color="B", board=self)
        for pos_x in [0, 7]:
            Rook(x=pos_x, y=7, color="B", board=self)
        for pos_x in [1, 6]:
            Knight(x=pos_x, y=7, color="B", board=self)
        for pos_x in [2, 5]:
            Bishop(x=pos_x, y=7, color="B", board=self)
        King(x=4, y=7, color="B", board=self)
        Queen(x=3, y=7, color="B", board=self)
    def get_piece_at(self, x, y):
        return self.board[x, y]