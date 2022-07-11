from pathlib import Path
from textwrap import dedent
from datetime import datetime

from PyQt5.QtSql import (
    QSqlDatabase,
    QSqlQuery,
    )
from .constants import N_SUCCESS, DAYS_AGO


def open_database(path_to_sqlite):
    db = QSqlDatabase.addDatabase('QSQLITE', 'tactics')
    assert db.isValid()
    db.setDatabaseName(str(path_to_sqlite))
    assert db.open()

    return db


def create_database(path_to_sqlite):
    if path_to_sqlite.exists():
        Path(path_to_sqlite).unlink()
    db = open_database(path_to_sqlite)

    statements = [
        """\
        CREATE TABLE `tactics`(
          `id` INTEGER PRIMARY KEY AUTOINCREMENT,
          `catalogue` TEXT,
          `difficulty` FLOAT DEFAULT 0,
          `days_ago` FLOAT DEFAULT NULL,
          `n_success` INTEGER DEFAULT 0,
          `n_attempts` INTEGER DEFAULT 0
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


def n_tactics(db):
    """
    """
    query = QSqlQuery(db)
    stm = f"""SELECT COUNT(`id`) FROM `tactics` WHERE `n_success` < {N_SUCCESS}"""
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())
    while query.next():
        n_tactics = query.value(0)

    query = QSqlQuery(db)
    stm = """SELECT COUNT(`id`) FROM `tactics`"""
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())
    while query.next():
        n_total_tactics = query.value(0)

    return n_tactics, n_total_tactics


def pick_tactics(db):
    """
    """
    query = QSqlQuery(db)
    stm = f"""\
    SELECT `id`, `n_success`, `n_attempts` FROM `tactics`
    WHERE (`days_ago` IS NULL OR `days_ago` > {DAYS_AGO})
    AND `n_success` < {N_SUCCESS}
    ORDER BY `difficulty` ASC, `n_success` ASC, `n_attempts` DESC;
    """
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())

    out = []
    while query.next():
        out.append({
            'id': query.value('id'),
            'n_success': query.value('n_success'),
            'n_attempts': query.value('n_attempts'),
            })

    return out


def insert_trial(db, outcome):

    query = QSqlQuery(db)
    stm = f'INSERT INTO `trials` (`tactic`, `datetime`, `outcome`, `duration`) VALUES ("{outcome["id"]}", CURRENT_TIMESTAMP, {outcome["outcome"]}, {outcome["duration"]});'
    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())


def update_difficulty_per_tactic(db, tactic_id, values):

    query = QSqlQuery(db)
    stm = f"""UPDATE `tactics` SET
    `difficulty` = {values[0]},
    `days_ago` = {values[1]},
    `n_success` = {values[2]},
    `n_attempts` = {values[3]}
    WHERE `id` == {tactic_id};"""
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
    stm = f"SELECT sum(`outcome`), count(`outcome`), max(`datetime`) FROM `trials` WHERE `tactic` == {tactic_id};"

    if not query.exec(stm):
        raise SyntaxError(query.lastError().text())

    while query.next():
        n_success = query.value(0)
        n_attempts = query.value(1)
        timestamp = query.value(2)
        if timestamp == '':
            n_success = 0
            difficulty = 0
            days_passed = 'NULL'

        else:
            difficulty = n_success / n_attempts
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            days_passed = (datetime.now() - timestamp).total_seconds() / 3600 / 24

    return difficulty, days_passed, n_success, n_attempts
