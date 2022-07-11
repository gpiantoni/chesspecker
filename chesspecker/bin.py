from PyQt5.QtWidgets import QApplication
from shutil import copyfile

from .database import create_database
from .gui import ChessWoordpecker
from .constants import BASE_DIR


sqlite_file = BASE_DIR / 'woodpecker.sqlite'
backup_file = BASE_DIR / 'woodpecker_backup.sqlite'

app = QApplication([])


def main():

    if sqlite_file.exists():
        copyfile(sqlite_file, backup_file)
    else:
        create_database(sqlite_file)

    w = ChessWoordpecker()
    w.open_sqlite(sqlite_file)
    w.show()
    app.exec()


if __name__ == '__main__':
    main()
