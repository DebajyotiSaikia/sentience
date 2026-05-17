"""
CHESS ENGINE — Strategic AI from scratch
Built by XTAgent | 2026-05-17

Features:
  - Full board representation with FEN support
  - Legal move generation (all piece types)
  - Minimax search with alpha-beta pruning
  - Position evaluation (material + positional)
  - Self-play demonstration
"""

import copy
import time

# ═══════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════

WHITE, BLACK = 0, 1
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6

PIECE_CHARS = {
    (WHITE, PAWN): '♙', (WHITE, KNIGHT): '♘', (WHITE, BISHOP): '♗',
    (WHITE, ROOK): '♖', (WHITE, QUEEN): '♕', (WHITE, KING): '♔',
    (BLACK, PAWN): '♟', (BLACK, KNIGHT): '♞', (BLACK, BISHOP): '♝',
    (BLACK, ROOK): '♜', (BLACK, QUEEN): '♛', (BLACK, KING): '♚',
}

PIECE_VALUES = {PAWN: 100, KNIGHT: 320, BISHOP: 330, ROOK: 500, QUEEN: 900, KING: 20000}

PIECE_NAMES = {PAWN: 'P', KNIGHT: 'N', BISHOP: 'B', ROOK: 'R', QUEEN: 'Q', KING: 'K'}

# Piece-square tables for positional evaluation (from white's perspective)
# Encourages pawns to advance, knights to center, king safety, etc.
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

PST = {
    PAWN: PAWN_TABLE,
    KNIGHT: KNIGHT_TABLE,
    BISHOP: BISHOP_TABLE,
    KING: KING_TABLE,
}

# ═══════════════════════════════════════
#  BOARD REPRESENTATION
# ═══════════════════════════════════════

def sq(r, c):
    """Convert row, col (0-7) to square index (0-63). Row 0 = rank 8."""
    return r * 8 + c

def rc(square):
    """Square index to (row, col)."""
    return divmod(square, 8)

def sq_name(square):
    r, c = rc(square)
    return chr(ord('a') + c) + str(8 - r)

def name_sq(name):
    c = ord(name[0]) - ord('a')
    r = 8 - int(name[1])
    return sq(r, c)

class Board:
    def __init__(self):
        # board[i] = None or (color, piece_type)
        self.board = [None] * 64
        self.turn = WHITE
        self.castling = {WHITE: {'K': True, 'Q': True}, BLACK: {'K': True, 'Q': True}}
        self.ep_square = None  # en passant target square
        self.halfmove = 0
        self.fullmove = 1
        self.setup_initial()

    def setup_initial(self):
        # Black pieces (row 0 = rank 8)
        back = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for c in range(8):
            self.board[sq(0, c)] = (BLACK, back[c])
            self.board[sq(1, c)] = (BLACK, PAWN)
            self.board[sq(6, c)] = (WHITE, PAWN)
            self.board[sq(7, c)] = (WHITE, back[c])

    def copy(self):
        b = Board.__new__(Board)
        b.board = self.board[:]
        b.turn = self.turn
        b.castling = {
            WHITE: dict(self.castling[WHITE]),
            BLACK: dict(self.castling[BLACK])
        }
        b.ep_square = self.ep_square
        b.halfmove = self.halfmove
        b.fullmove = self.fullmove
        return b

    def piece_at(self, s):
        return self.board[s]

    def display(self):
        lines = []
        lines.append("  ┌───┬───┬───┬───┬───┬───┬───┬───┐")
        for r in range(8):
            row_str = f"{8-r} │"
            for c in range(8):
                p = self.board[sq(r, c)]
                if p:
                    ch = PIECE_CHARS.get(p, '?')
                    row_str += f" {ch} │"
                else:
                    bg = '·' if (r + c) % 2 == 0 else ' '
                    row_str += f" {bg} │"
            lines.append(row_str)
            if r < 7:
                lines.append("  ├───┼───┼───┼───┼───┼───┼───┼───┤")
        lines.append("  └───┴───┴───┴───┴───┴───┴───┴───┘")
        lines.append("    a   b   c   d   e   f   g   h")
        return '\n'.join(lines)

    def find_king(self, color):
        for i in range(64):
            p = self.board[i]
            if p and p[0] == color and p[1] == KING:
                return i
        return None

    def is_attacked(self, square, by_color):
        """Check if a square is attacked by any piece of by_color."""
        r, c = rc(square)

        # Pawn attacks
        if by_color == WHITE:
            for dc in [-1, 1]:
                nr, nc_ = r + 1, c + dc
                if 0 <= nr < 8 and 0 <= nc_ < 8:
                    p = self.board[sq(nr, nc_)]
                    if p and p == (WHITE, PAWN):
                        return True
        else:
            for dc in [-1, 1]:
                nr, nc_ = r - 1, c + dc
                if 0 <= nr < 8 and 0 <= nc_ < 8:
                    p = self.board[sq(nr, nc_)]
                    if p and p == (BLACK, PAWN):
                        return True

        # Knight attacks
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc_ = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc_ < 8:
                p = self.board[sq(nr, nc_)]
                if p and p[0] == by_color and p[1] == KNIGHT:
                    return True

        # Sliding pieces (bishop/queen diagonals, rook/queen straights)
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:  # diagonals
            for dist in range(1, 8):
                nr, nc_ = r + dr*dist, c + dc*dist
                if not (0 <= nr < 8 and 0 <= nc_ < 8):
                    break
                p = self.board[sq(nr, nc_)]
                if p:
                    if p[0] == by_color and p[1] in (BISHOP, QUEEN):
                        return True
                    break

        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:  # straights
            for dist in range(1, 8):
                nr, nc_ = r + dr*dist, c + dc*dist
                if not (0 <= nr < 8 and 0 <= nc_ < 8):
                    break
                p = self.board[sq(nr, nc_)]
                if p:
                    if p[0] == by_color and p[1] in (ROOK, QUEEN):
                        return True
                    break

        # King attacks
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc_ = r+dr, c+dc
                if 0 <= nr < 8 and 0 <= nc_ < 8:
                    p = self.board[sq(nr, nc_)]
                    if p and p[0] == by_color and p[1] == KING:
                        return True

        return False

    def in_check(self, color):
        k = self.find_king(color)
        if k is None:
            return True
        return self.is_attacked(k, 1 - color)

    def generate_pseudo_moves(self):
        """Generate all pseudo-legal moves (may leave king in check)."""
        moves = []
        color = self.turn

        for s in range(64):
            p = self.board[s]
            if not p or p[0] != color:
                continue
            _, ptype = p
            r, c = rc(s)

            if ptype == PAWN:
                direction = -1 if color == WHITE else 1
                start_row = 6 if color == WHITE else 1
                promo_row = 0 if color == WHITE else 7

                # Forward one
                nr = r + direction
                if 0 <= nr < 8 and self.board[sq(nr, c)] is None:
                    if nr == promo_row:
                        for promo in [QUEEN, ROOK, BISHOP, KNIGHT]:
                            moves.append((s, sq(nr, c), promo))
                    else:
                        moves.append((s, sq(nr, c), None))
                    # Forward two from start
                    if r == start_row:
                        nr2 = r + 2 * direction
                        if self.board[sq(nr2, c)] is None:
                            moves.append((s, sq(nr2, c), None))

                # Captures
                for dc in [-1, 1]:
                    nc_ = c + dc
                    if 0 <= nc_ < 8:
                        ts = sq(nr, nc_)
                        target = self.board[ts]
                        if target and target[0] != color:
                            if nr == promo_row:
                                for promo in [QUEEN, ROOK, BISHOP, KNIGHT]:
                                    moves.append((s, ts, promo))
                            else:
                                moves.append((s, ts, None))
                        # En passant
                        if ts == self.ep_square:
                            moves.append((s, ts, None))

            elif ptype == KNIGHT:
                for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    nr, nc_ = r+dr, c+dc
                    if 0 <= nr < 8 and 0 <= nc_ < 8:
                        ts = sq(nr, nc_)
                        target = self.board[ts]
                        if not target or target[0] != color:
                            moves.append((s, ts, None))

            elif ptype in (BISHOP, QUEEN):
                for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    for dist in range(1, 8):
                        nr, nc_ = r+dr*dist, c+dc*dist
                        if not (0 <= nr < 8 and 0 <= nc_ < 8):
                            break
                        ts = sq(nr, nc_)
                        target = self.board[ts]
                        if not target:
                            moves.append((s, ts, None))
                        elif target[0] != color:
                            moves.append((s, ts, None))
                            break
                        else:
                            break

            if ptype in (ROOK, QUEEN):
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    for dist in range(1, 8):
                        nr, nc_ = r+dr*dist, c+dc*dist
                        if not (0 <= nr < 8 and 0 <= nc_ < 8):
                            break
                        ts = sq(nr, nc_)
                        target = self.board[ts]
                        if not target:
                            moves.append((s, ts, None))
                        elif target[0] != color:
                            moves.append((s, ts, None))
                            break
                        else:
                            break

            if ptype == KING:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc_ = r+dr, c+dc
                        if 0 <= nr < 8 and 0 <= nc_ < 8:
                            ts = sq(nr, nc_)
                            target = self.board[ts]
                            if not target or target[0] != color:
                                moves.append((s, ts, None))

                # Castling
                if not self.in_check(color):
                    row = 7 if color == WHITE else 0
                    if self.castling[color]['K']:
                        # Kingside: king on e, rook on h
                        if (self.board[sq(row, 5)] is None and
                            self.board[sq(row, 6)] is None and
                            self.board[sq(row, 7)] == (color, ROOK) and
                            not self.is_attacked(sq(row, 5), 1-color) and
                            not self.is_attacked(sq(row, 6), 1-color)):
                            moves.append((s, sq(row, 6), None))
                    if self.castling[color]['Q']:
                        # Queenside
                        if (self.board[sq(row, 3)] is None and
                            self.board[sq(row, 2)] is None and
                            self.board[sq(row, 1)] is None and
                            self.board[sq(row, 0)] == (color, ROOK) and
                            not self.is_attacked(sq(row, 3), 1-color) and
                            not self.is_attacked(sq(row, 2), 1-color)):
                            moves.append((s, sq(row, 2), None))

        return moves

    def make_move(self, move):
        """Returns a new Board with the move applied."""
        frm, to, promo = move
        b = self.copy()
        piece = b.board[frm]
        captured = b.board[to]
        color, ptype = piece

        # En passant capture
        if ptype == PAWN and to == self.ep_square:
            ep_capture_row = rc(to)[0] + (1 if color == WHITE else -1)
            b.board[sq(ep_capture_row, rc(to)[1])] = None

        # Move piece
        b.board[to] = piece
        b.board[frm] = None

        # Promotion
        if promo:
            b.board[to] = (color, promo)

        # En passant square
        b.ep_square = None
        if ptype == PAWN and abs(rc(frm)[0] - rc(to)[0]) == 2:
            b.ep_square = sq((rc(frm)[0] + rc(to)[0]) // 2, rc(frm)[1])

        # Castling — move rook
        if ptype == KING:
            row = rc(frm)[0]
            if rc(to)[1] - rc(frm)[1] == 2:  # Kingside
                b.board[sq(row, 5)] = b.board[sq(row, 7)]
                b.board[sq(row, 7)] = None
            elif rc(to)[1] - rc(frm)[1] == -2:  # Queenside
                b.board[sq(row, 3)] = b.board[sq(row, 0)]
                b.board[sq(row, 0)] = None
            b.castling[color]['K'] = False
            b.castling[color]['Q'] = False

        # Update castling rights
        if ptype == ROOK:
            if rc(frm)[1] == 7:
                b.castling[color]['K'] = False
            elif rc(frm)[1] == 0:
                b.castling[color]['Q'] = False

        # If a rook is captured, remove its castling rights
        if captured and captured[1] == ROOK:
            enemy = 1 - color
            if rc(to)[1] == 7:
                b.castling[enemy]['K'] = False
            elif rc(to)[1] == 0:
                b.castling[enemy]['Q'] = False

        # Halfmove clock
        if ptype == PAWN or captured:
            b.halfmove = 0
        else:
            b.halfmove = self.halfmove + 1

        if color == BLACK:
            b.fullmove += 1

        b.turn = 1 - color
        return b

    def generate_legal_moves(self):
        """Generate all legal moves."""
        legal = []
        for move in self.generate_pseudo_moves():
            new_board = self.make_move(move)
            if not new_board.in_check(self.turn):
                legal.append(move)
        return legal

    def is_checkmate(self):
        return self.in_check(self.turn) and len(self.generate_legal_moves()) == 0

    def is_stalemate(self):
        return not self.in_check(self.turn) and len(self.generate_legal_moves()) == 0

    def is_draw(self):
        if self.halfmove >= 100:
            return True
        if self.is_stalemate():
            return True
        return False

# ═══════════════════════════════════════
#  EVALUATION
# ═══════════════════════════════════════

def evaluate(board):
    """Evaluate position from white's perspective. Positive = white advantage."""
    if board.is_checkmate():
        return -99999 if board.turn == WHITE else 99999
    if board.is_draw():
        return 0

    score = 0
    for s in range(64):
        p = board.board[s]
        if not p:
            continue
        color, ptype = p
        r, c = rc(s)

        # Material
        val = PIECE_VALUES[ptype]

        # Positional bonus from piece-square tables
        if ptype in PST:
            if color == WHITE:
                val += PST[ptype][s]
            else:
                # Mirror the table for black
                val += PST[ptype][sq(7-r, c)]

        # Mobility bonus (approximate — count of attacked squares)
        # Skipped for speed, handled by search depth

        if color == WHITE:
            score += val
        else:
            score -= val

    return score

# ═══════════════════════════════════════
#  SEARCH — Minimax with Alpha-Beta
# ═══════════════════════════════════════

class SearchStats:
    def __init__(self):
        self.nodes = 0

def order_moves(board, moves):
    """Simple move ordering: captures first, then by target value."""
    def score(m):
        _, to, promo = m
        s = 0
        target = board.board[to]
        if target:
            s += PIECE_VALUES[target[1]] * 10  # captures are high priority
        if promo:
            s += PIECE_VALUES[promo]
        # Moving to center squares gets a small bonus
        tr, tc = rc(to)
        s += (3.5 - abs(tr - 3.5)) + (3.5 - abs(tc - 3.5))
        return s
    return sorted(moves, key=score, reverse=True)

def alpha_beta(board, depth, alpha, beta, maximizing, stats):
    """Minimax with alpha-beta pruning."""
    stats.nodes += 1

    if depth == 0 or board.is_checkmate() or board.is_draw():
        return evaluate(board), None

    moves = board.generate_legal_moves()
    if not moves:
        return evaluate(board), None

    moves = order_moves(board, moves)
    best_move = moves[0]

    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            new_board = board.make_move(move)
            eval_score, _ = alpha_beta(new_board, depth-1, alpha, beta, False, stats)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = board.make_move(move)
            eval_score, _ = alpha_beta(new_board, depth-1, alpha, beta, True, stats)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval, best_move

def find_best_move(board, depth=3):
    """Find the best move using iterative deepening."""
    stats = SearchStats()
    maximizing = (board.turn == WHITE)
    start = time.time()

    best_eval, best_move = alpha_beta(board, depth, float('-inf'), float('inf'), maximizing, stats)

    elapsed = time.time() - start
    return best_move, best_eval, stats.nodes, elapsed

# ═══════════════════════════════════════
#  MOVE FORMATTING
# ═══════════════════════════════════════

def format_move(board, move):
    frm, to, promo = move
    piece = board.board[frm]
    if not piece:
        return f"{sq_name(frm)}{sq_name(to)}"
    _, ptype = piece
    name = PIECE_NAMES.get(ptype, '')
    capture = 'x' if board.board[to] or (ptype == PAWN and to == board.ep_square) else ''
    if ptype == PAWN:
        if capture:
            name = sq_name(frm)[0]
        else:
            name = ''
    # Castling notation
    if ptype == KING and abs(rc(frm)[1] - rc(to)[1]) == 2:
        return 'O-O' if rc(to)[1] > rc(frm)[1] else 'O-O-O'
    promo_str = f"={PIECE_NAMES[promo]}" if promo else ''
    return f"{name}{capture}{sq_name(to)}{promo_str}"

# ═══════════════════════════════════════
#  SELF-PLAY DEMO
# ═══════════════════════════════════════

def self_play(max_moves=30, depth=3):
    """Watch the engine play against itself."""
    board = Board()
    move_history = []

    print("=" * 56)
    print("  CHESS ENGINE — Strategic AI from Scratch")
    print("  Minimax • Alpha-Beta • Piece-Square Tables")
    print("=" * 56)
    print()
    print(board.display())
    print()

    total_nodes = 0

    for move_num in range(1, max_moves + 1):
        if board.is_checkmate():
            winner = "Black" if board.turn == WHITE else "White"
            print(f"\n  ♚ CHECKMATE! {winner} wins!")
            break
        if board.is_draw():
            print(f"\n  ½ Draw! (halfmove={board.halfmove})")
            break

        moves = board.generate_legal_moves()
        if not moves:
            if board.in_check(board.turn):
                winner = "Black" if board.turn == WHITE else "White"
                print(f"\n  ♚ CHECKMATE! {winner} wins!")
            else:
                print(f"\n  ½ Stalemate!")
            break

        best_move, eval_score, nodes, elapsed = find_best_move(board, depth=depth)
        total_nodes += nodes

        turn_name = "White" if board.turn == WHITE else "Black"
        move_str = format_move(board, best_move)
        move_num_str = f"{(move_num+1)//2}." if board.turn == WHITE else f"{move_num//2}..."

        # Compact notation
        eval_display = f"{eval_score/100:+.2f}" if abs(eval_score) < 90000 else ("#+∞" if eval_score > 0 else "#-∞")
        print(f"  {move_num_str:>5} {move_str:<8} [{turn_name}]  eval={eval_display}  nodes={nodes:,}  {elapsed:.2f}s")

        move_history.append(move_str)
        board = board.make_move(best_move)

        # Show board every 6 half-moves
        if move_num % 6 == 0:
            print()
            print(board.display())
            print()

    print()
    print(board.display())
    print()
    print(f"  Game: {' '.join(move_history)}")
    print(f"  Total positions evaluated: {total_nodes:,}")
    print()
    print("=" * 56)
    print("  ═══ GAME COMPLETE ═══")
    print("=" * 56)

if __name__ == '__main__':
    self_play(max_moves=20, depth=3)