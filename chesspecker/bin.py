from PyQt5.QtWidgets import QApplication
from .gui import ChessWoordpecker

sqlite_file = "/home/gio/surfdrive/chess/woodpecker.sqlite"

app = QApplication([])


def main():
    w = ChessWoordpecker()
    w.open_sqlite(sqlite_file)
    w.show()
    app.exec()


if __name__ == '__main__':
    main()
