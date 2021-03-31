from pathlib import Path
from math import ceil

from chess.pgn import read_game

from .database import yield_tactics, calculate_difficulty, update_difficulty_per_tactic, insert_tactics, pick_tactics


def find_player_color(board):
    """With chesstempo, this is correct, but maybe not in all the cases"""
    return not board.turn


class Tactics():

    def __init__(self, i_tactics, game):
        self.i = i_tactics
        self.game = game
        self.board = game.board()
        self._i_move = 0
        self._moves = list(game.mainline_moves())
        self.player_color = find_player_color(self.board)
        # total number of moves that the player makes
        self.n_player_moves = ceil((len(self._moves) - 1) / 2)

    def move(self):
        """
        Returns
        -------
        bool
            True if there is one more move, False if the tactics is completed
        """
        m = self.next_move
        if m is None:
            return False
        self.board.push(m)
        self._i_move += 1
        return True

    @property
    def next_move(self):
        if self._i_move >= len(self._moves):
            return None
        else:
            return self._moves[self._i_move]

    @property
    def previous_move(self):
        if self._i_move == 0:
            return None
        else:
            return self._moves[self._i_move - 1]


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
