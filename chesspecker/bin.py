from PyQt5.QtWidgets import QApplication
from shutil import copyfile
from pathlib import Path


from .gui import ChessWoordpecker

sqlite_file = "/home/gio/surfdrive/chess/woodpecker.sqlite"

app = QApplication([])


def main():

    backup_file = Path(sqlite_file).parent / 'woodpecker_backup.sqlite'
    copyfile(sqlite_file, backup_file)

    w = ChessWoordpecker()
    w.open_sqlite(sqlite_file)
    w.show()
    app.exec()


if __name__ == '__main__':
    main()
