from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLineEdit, QFormLayout, QPushButton
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QSize, Qt
from time import time

from chess import svg

from .tactics import Tactics, select_tactics
from .database import open_database, insert_trial


size = 800


class SvgBoard(QSvgWidget):
    def __init__(self):
        super().__init__()
        self.renderer = self.renderer()
        svg_bytes = bytearray(svg.board(), encoding='utf-8')
        self.renderer.load(svg_bytes)
        self.renderer.setAspectRatioMode(Qt.KeepAspectRatio)

    def sizeHint(self):
        return QSize(size, size)


class ChessWoordpecker(QMainWindow):
    """when closing, close database"""
    tactics = None

    def __init__(self):
        super().__init__()

        self.w_svg = SvgBoard()  # set size

        l_form = QFormLayout()
        self.w_line = QLineEdit()
        self.w_line.returnPressed.connect(self.moved)
        self.w_line.setEnabled(False)
        l_form.addRow('Your move: ', self.w_line)

        self.w_next = QPushButton('Next')
        self.w_next.setAutoDefault(True)
        self.w_next.clicked.connect(self.tactics_next)
        self.w_replay = QPushButton('Replay (todo)')
        self.w_replay.setEnabled(False)
        l_form.addRow(self.w_next, self.w_replay)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.w_svg)
        layout.addLayout(l_form)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_sqlite(self, sqlite_file):
        pass

    def open_sqlite(self, sqlite_file):
        self.db = open_database(sqlite_file)

    def tactics_next(self):
        self.w_line.setText('')

        i_tactics, game = select_tactics(self.db)

        self.tactics = Tactics(i_tactics, game)
        self.t = time()

        if self.tactics.board.turn != self.tactics.player_color:
            self.tactics.move()

        self.w_line.setEnabled(True)
        self.w_line.setFocus()
        self.show_move()

    def moved(self):
        user = self.w_line.text()
        try:
            user_move = self.tactics.board.parse_san(user)
        except ValueError:
            self.w_line.setText(f'Illegal move ({user})')
            return

        if self.tactics.next_move != user_move:
            self.w_line.setText(f'Incorrect ({user})')
            self.finished(0)
            return

        # player's move
        self.tactics.move()
        self.show_move()

        # opponent's move
        if self.tactics.move():
            self.w_line.setText('')
            self.show_move()
        else:
            self.finished(1)

    def show_move(self):
        svg_board = svg.board(self.tactics.board, orientation=self.tactics.player_color, lastmove=self.tactics.previous_move)
        svg_bytes = bytearray(svg_board, encoding='utf-8')
        self.w_svg.renderer.load(svg_bytes)
        self.w_svg.renderer.setAspectRatioMode(Qt.KeepAspectRatio)

    def finished(self, outcome):
        self.w_line.setEnabled(False)
        if outcome == 0:
            duration = 0
        else:
            # how to calculate number of moves
            duration = (time() - self.t) / self.tactics.n_player_moves
        outcome = {
            'id': self.tactics.i,
            'duration': duration,
            'outcome': outcome,
            }
        insert_trial(self.db, outcome)
