from pathlib import Path

from chess.pgn import read_game

from .database import yield_tactics, calculate_difficulty, update_difficulty_per_tactic, insert_tactics, pick_tactics


def update_difficulty(db):
    for tactic_id in yield_tactics(db):
        values = calculate_difficulty(db, tactic_id)
        update_difficulty_per_tactic(db, tactic_id, values)


def read_tactics(tactics_path, tactics_id):
    """there should be only one game per pgn"""
    tactics_file = tactics_path / f'{tactics_id:08}.pgn'
    with tactics_file.open() as f:
        game = read_game(f)
    return game


def import_tactics(db, pgn_file):
    with pgn_file.open() as f:
        while True:
            game = read_game(f)
            if game is None:
                break
            insert_tactics(db, game)


def select_tactics(db):
    update_difficulty(db)
    tactics_id = pick_tactics(db)

    db_path = Path(db.databaseName())
    tactics_path = db_path.parent / 'tactics'
    game = read_tactics(tactics_path, tactics_id)

    return tactics_id, game
