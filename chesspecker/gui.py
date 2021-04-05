from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    )
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QSize, Qt
from time import time

from chess import svg

from .tactics import Tactics, select_tactics
from .database import open_database, insert_trial, n_tactics


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

        h_general = QHBoxLayout()
        self.l_id = QLabel('')
        self.l_id.setAlignment(Qt.AlignRight)
        h_general.addWidget(self.l_id)
        self.l_tactics = QLabel('')
        self.l_tactics.setAlignment(Qt.AlignRight)
        h_general.addWidget(self.l_tactics)
        self.l_success = QLabel('0')
        self.l_success.setAlignment(Qt.AlignRight)
        h_general.addWidget(self.l_success)
        self.l_session = QLabel('0')
        self.l_session.setAlignment(Qt.AlignRight)
        h_general.addWidget(self.l_session)
        self.l_total = QLabel('0')
        self.l_total.setAlignment(Qt.AlignRight)
        h_general.addWidget(self.l_total)

        self.w_svg = SvgBoard()  # set size

        l_form = QFormLayout()
        self.w_line = QLineEdit()
        self.w_line.returnPressed.connect(self.moved)
        self.w_line.setEnabled(False)
        l_form.addRow('Your move: ', self.w_line)

        self.w_next = QPushButton('Next')
        self.w_next.setAutoDefault(True)
        self.w_next.clicked.connect(self.tactics_next)
        self.l_stream = QLabel('')
        l_form.addRow(self.w_next, self.l_stream)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.w_svg)
        layout.addLayout(l_form)
        layout.addLayout(h_general)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_sqlite(self, sqlite_file):
        pass

    def open_sqlite(self, sqlite_file):
        self.db = open_database(sqlite_file)

        n_current, n_total = n_tactics(self.db)
        self.l_total.setText(f'{n_current: 3d}/ {n_total: 3d}')

    def tactics_next(self):
        self.w_line.setText('')

        tactics, game = select_tactics(self.db)

        self.tactics = Tactics(tactics, game)
        self.t = time()

        if self.tactics.board.turn != self.tactics.player_color:
            self.tactics.move()

        self.w_line.setEnabled(True)
        self.w_line.setFocus()
        self.show_move()
        self.l_id.setText('')
        self.l_tactics.setText('')

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
            if self.tactics.next_move is None:
                self.finished(1)

        else:
            self.finished(1)

    def show_move(self):
        svg_board = svg.board(self.tactics.board, orientation=self.tactics.player_color, lastmove=self.tactics.previous_move)
        svg_bytes = bytearray(svg_board, encoding='utf-8')
        self.w_svg.renderer.load(svg_bytes)
        self.w_svg.renderer.setAspectRatioMode(Qt.KeepAspectRatio)

    def finished(self, outcome):
        self.w_line.setEnabled(False)
        val = int(self.l_session.text()) + 1
        self.l_session.setText(str(val))

        if outcome == 0:
            self.l_stream.setText(self.l_stream.text() + '-')
            duration = 0
        else:
            self.l_stream.setText(self.l_stream.text() + '+')
            val = int(self.l_success.text()) + 1
            self.l_success.setText(str(val))
            duration = (time() - self.t) / self.tactics.n_player_moves

        self.l_id.setText(f'Tactics #{self.tactics.info["id"]}')
        success = self.tactics.info['n_success'] + outcome
        attempts = self.tactics.info['n_attempts'] + 1
        self.l_tactics.setText(f'{success: 4d} /{attempts: 4d}')

        outcome = {
            'id': self.tactics.info['id'],
            'duration': duration,
            'outcome': outcome,
            }
        insert_trial(self.db, outcome)
