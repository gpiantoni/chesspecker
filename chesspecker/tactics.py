from pathlib import Path
from math import ceil
from collections import defaultdict
from itertools import count

from chess.pgn import read_game

from .database import yield_tactics, calculate_difficulty, update_difficulty_per_tactic, insert_tactics, pick_tactics, n_tactics

PGN_FILE = '/home/gio/surfdrive/chess/errors.pgn'


def find_player_color(board):
    """With chesstempo, this is correct, but maybe not in all the cases"""
    return not board.turn


class Tactics():

    def __init__(self, info, game):
        self.info = info
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


def import_tactics(db, pgn_file, max_new_tactics=None):
    current_tactics = read_current_fens(db)

    out = []
    with open(pgn_file) as f:

        for i in count():
            game = read_game(f)
            if game is None:
                break

            if max_new_tactics is not None and i < max_new_tactics:

                if game.board().fen() in current_tactics:
                    print(f'Tactics {game.board().fen()} already exists')

                else:
                    insert_tactics(db, game)

            else:
                out.append(str(game))

    with open(pgn_file, 'w') as f:
        f.write('\n\n'.join(out))


def select_tactics(db):
    update_difficulty(db)
    tactics = pick_tactics(db)

    db_path = Path(db.databaseName())
    tactics_path = db_path.parent / 'tactics'
    game = read_tactics(tactics_path, tactics['id'])

    return tactics, game


def read_current_fens(db):
    db_path = Path(db.databaseName())
    tactics_path = db_path.parent / 'tactics'
    all_fens = [read_tactics(tactics_path, i).board().fen() for i in yield_tactics(db)]

    D = defaultdict(list)
    for i, item in enumerate(all_fens):
        D[item].append(i)
    D = {k: v for k, v in D.items() if len(v) > 1}
    if D:
        print('duplicated tactics')
        print(D)

    return all_fens


def topup_tactics(db, ideal_n_tactics):
    current_tactics = n_tactics(db)[0]
    if current_tactics < ideal_n_tactics:
        difference = ideal_n_tactics - current_tactics
        import_tactics(db, PGN_FILE, difference)
        print(f'Importing {difference} tactics')
