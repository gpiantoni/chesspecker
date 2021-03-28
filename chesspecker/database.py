from pathlib import Path
from textwrap import dedent
from datetime import datetime

from PyQt5.QtSql import (
    QSqlDatabase,
    QSqlQuery,
    )

RATE = 1
MAX_DUR_PER_MOVE = 20


def open_database(path_to_sqlite):
    db = QSqlDatabase.addDatabase('QSQLITE', 'tactics')
    assert db.isValid()
    db.setDatabaseName(path_to_sqlite)
    assert db.open()

    return db


def create_database(path_to_sqlite):
    Path(path_to_sqlite).unlink()
    db = open_database(path_to_sqlite)

    statements = [
        """\
        CREATE TABLE `tactics`(
          `id` INTEGER PRIMARY KEY AUTOINCREMENT,
          `catalogue` TEXT,
          `difficulty` FLOAT DEFAULT 0
        );""",
        """\
        CREATE TABLE `trials` (
          `id` INTEGER PRIMARY KEY,
          `tactic` INTEGER,
          `datetime` TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
          `outcome` INTEGER,
          `duration` FLOAT,
          FOREIGN KEY("tactic") REFERENCES "tactics"("id")
        );""",
        ]  # duration per move

    for stm in statements:
        query = QSqlQuery(db)

        if not query.exec(dedent(stm)):
            raise SyntaxError(query.lastError().text())


def insert_tactics(db, game):

    catalogue = game.headers['Site']

    query = QSqlQuery(db)
    stm = f'INSERT INTO `tactics` (`catalogue`) VALUES ("{catalogue}");'
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())

    lastId = query.lastInsertId()
    db_path = Path(db.databaseName())
    tactics_path = db_path.parent / 'tactics'
    tactics_path.mkdir(exist_ok=True)

    tactics_file = tactics_path / f'{lastId:08}.pgn'
    with tactics_file.open('w') as f:
        f.write(str(game))


def pick_tactics(db):
    """
    - also add no more recent than 20h
    - also exclude more than 10 correct
    """
    query = QSqlQuery(db)
    stm = 'SELECT `id` FROM `tactics` ORDER BY `difficulty` LIMIT 1;'
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())

    while query.next():
        tactics_id = query.value('id')

    return tactics_id


def insert_trial(db, outcome):

    query = QSqlQuery(db)
    stm = f'INSERT INTO `trials` (`tactic`, `datetime`, `outcome`, `duration`) VALUES ("{outcome["id"]}", CURRENT_TIMESTAMP, {outcome["outcome"]}, {outcome["duration"]});'
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())


def update_difficulty_per_tactic(db, tactic_id, difficulty):

    query = QSqlQuery(db)
    stm = f'UPDATE `tactics` SET `difficulty` = {difficulty} WHERE `id` == {tactic_id};'
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())


def yield_tactics(db):

    query = QSqlQuery(db)
    stm = 'SELECT `id` FROM `tactics` ORDER BY `id`;'
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())

    while query.next():
        yield query.value('id')


def calculate_difficulty(db, tactic_id):

    query = QSqlQuery(db)
    # select most recent trial
    stm = f'SELECT `outcome`, `datetime`, `duration` FROM `trials` WHERE `tactic` == {tactic_id} ORDER BY `datetime` ASC;'
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())

    difficulty = []
    while query.next():
        if query.value('outcome') == 0:
            difficulty_per_trial = -1  # penalty per error
        else:
            timestamp = datetime.strptime(query.value('datetime'), '%Y-%m-%d %H:%M:%S')
            days_passed = (datetime.now() - timestamp).total_seconds() / 3600 / 24
            difficulty_per_trial = (MAX_DUR_PER_MOVE - query.value('duration')) - RATE * days_passed
            # do not get penalty for correct answer, but in the worst case it goes to zero
            difficulty_per_trial = max([difficulty_per_trial, 0])

        difficulty.append(difficulty_per_trial)

    return sum(difficulty)
