import os
import re
import json
import random

STATE_FILE = "game_state.json"
README_FILE = "README.md"

#initial board configuration for checkers:
INITIAL_BOARD = [
    ['.', 'b', '.', 'b', '.', 'b', '.', 'b'],
    ['b', '.', 'b', '.', 'b', '.', 'b', '.'],
    ['.', 'b', '.', 'b', '.', 'b', '.', 'b'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['r', '.', 'r', '.', 'r', '.', 'r', '.'],
    ['.', 'r', '.', 'r', '.', 'r', '.', 'r'],
    ['r', '.', 'r', '.', 'r', '.', 'r', '.']
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f )
    else:
        return {
            "board": INITIAL_BOARD,
            "turn": "r",  #'r' or 'b'
            "games_played": 0,
            "red_wins": 0,
            "black_wins": 0,
            "last_move": "",
            "red_algo": None,
            "black_algo": None
        }

def save_state(state):
    #save state to file
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
def render_board(board):
    #render the board as a string
    result = "  a b c d e f g h\n"
    for i, row in enumerate(board):
        row_str = str(i+1) + " " + " ".join(row ) + " "
        result += row_str + "\n"
    return result
def in_bounds(r, c):
    #check if position is within the board
    return 0 <= r < 8 and 0 <= c < 8
def is_opponent(piece, current):
    #check if a piece is opponent's
    if piece == '.':
        return False
    return (piece.islower() and not current.islower()) or (piece.isupper() and not current.isupper())
def get_piece_direction(piece):
    #get movement directions based on piece type
    if piece == '.' or piece == '':
        return []
    if piece.lower() == 'r': #red piece or red king
        if piece.islower():
            return [(-1, -1), (-1, 1)]
        else:
            #king can move both ways
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        #black piece or black king
        if piece.islower():
            return [(1, -1), (1, 1)]
        else:
            #king
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
def must_capture(board, player):
    #check if player must capture
    moves = get_all_moves(board, player)
    return any(m["captures"] for m in moves)
def get_all_moves(board, player):
    #get all possible moves for player
    moves = []
    #first find capturing moves
    for r in range(8):
        for c in range(8):
            if board[r][c] != '.' and (board[r][c].lower() == player):
                #explore jumps
                captures = find_all_jumps(board, r, c)
                moves.extend(captures)

    if len(moves) > 0:
        #capturing moves exist, return only them
        return moves
    #no captures, get regular moves
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != '.' and piece.lower() == player:
                directions = get_piece_direction(piece)
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == '.':
                        moves.append({
                            "start": (r, c),
                            "jump_path": [(nr, nc)],
                            "captures": 0
                        })
    return moves
def find_all_jumps(board, r, c):
    #find all jump sequences from a position
    piece = board[r][c]
    directions = get_piece_direction(piece)
    results = []
    def backtrack(brd, cr, cc, captures, path):
        #recursive backtracking to find jumps
        jumped_any = False
        p = brd[cr][cc]
        dirs = get_piece_direction(p)
        for dr, dc in dirs:
            nr, nc = cr + dr, cc + dc
            jr, jc = cr + 2*dr, cc + 2*dc
            if in_bounds(nr, nc) and in_bounds(jr, jc):
                if is_opponent(brd[nr][nc], p) and brd[jr][jc] == '.':
                    #try this jump
                    new_brd = [row[:] for row in brd]
                    #perform jump
                    new_brd[cr][cc] = '.'
                    new_brd[nr][nc] = '.'
                    new_brd[jr][jc] = p
                    #continue searching
                    backtrack(new_brd, jr, jc, captures+1, path + [(jr, jc)])
                    jumped_any = True
        if not jumped_any:
            #end of jump chain
            if captures > 0:
                results.append({
                    "start": (r, c),
                    "jump_path": path,
                    "captures": captures
                } )
    backtrack([row[:] for row in board], r, c, 0, [] )
    return results

def apply_move(board, move):
    #apply a move to the board
    new_board = [row[:] for row in board]
    sr, sc = move["start"]
    piece = new_board[sr][sc]
    new_board[sr][sc] = '.'
    cr, cc = sr, sc
    for idx, (nr, nc) in enumerate(move["jump_path"]):
        #if jump, remove captured piece
        if abs(nr - cr) == 2:
            #jumped over opponent
            midr = (cr + nr) // 2
            midc = (cc + nc) // 2
            new_board[midr][midc] = '.'
        new_board[nr][nc] =  piece 
        cr, cc = nr, nc

    #check for king promotion
    #red king row = 0, black king row = 7
    end_r = move["jump_path"][-1][0]
    if piece.lower() == 'r' and end_r == 0:
        new_board[end_r][move["jump_path"][-1][1]] = 'R'
    if piece.lower() == 'b' and end_r == 7:
        new_board[end_r][move["jump_path"][-1][1]] = 'B'

    return new_board
 

def check_winner(board):
    #check if there's a winner
    reds = sum(cell.lower() == 'r' for row in board for cell in row)
    blacks = sum(cell.lower() == 'b' for row in board for cell in row)

    if reds == 0:
        return 'b'
    if blacks == 0:
        return 'r'

    #check if current player can move
    return None
def reset_game(state):
    #reset the game state
    state["board"] = [row[:] for row in INITIAL_BOARD]
    state["turn"] = "r"
    state["games_played"] += 1
    #randomly choose algorithms for red and black
    #each from the pool of 5
    algos = ["random", "aggressive", "defensive", "center", "promotion"]
    state["red_algo"] = random.choice(algos)
    state["black_algo"] = random.choice(algos)
    state["last_move"] = ""
    return state
def choose_move(moves, algorithm, board, player):
    #choose a move based on the algorithm
    if not moves:
        return None
    if algorithm == "random":
        return random.choice(moves )
    elif algorithm == "aggressive":
        #prioritize moves by captures (max captures)
        moves.sort(key=lambda m: m["captures"], reverse=True )
        return moves[0]
    elif algorithm == "defensive":
        #defensive: try to reduce risk
        #count how many opponent pieces threaten landing squares
        #very naive: fewer threats is better
        def danger(m):
            end = m["jump_path"][-1]
            return count_threats(board, end,player)
        moves.sort(key=lambda m: danger(m))
        return moves[0]
    elif algorithm == "center":
        #prefer moves closer to center columns (3 or 4)
        def center_score(m):
            end = m["jump_path"][-1]
            #distance from center columns (3.5)
            return abs(end[1] - 3.5)
        moves.sort(key=lambda m: center_score(m))
        return moves[0]
    elif algorithm == "promotion":
        #move that gets closer to king row for player
        def promotion_score(m):
            end = m["jump_path"][-1]
            if player == 'r':
                return end[0]  #smaller is better (closer to top)
            else:
                return 7 - end[0] #closer to bottom
        moves.sort(key=lambda m: promotion_score(m))
        return moves[0]
    else: 
        return random.choice(moves)

def count_threats(board, pos, player):
    #count how many opponent pieces could jump onto pos next turn
    #heuristic for defensive AI
    (r, c) = pos
    opp = 'b' if player == 'r' else 'r'
    opp_moves = get_all_moves(board, opp) 
    count = 0 
    for om in opp_moves: 
        if om["jump_path"][-1] ==  pos: 
            count  += 1 
    return count

def update_readme(state):
    #update the README file with current game state
    with open(README_FILE, "r") as f: 
        content = f.read()

    board_str = render_board(state["board"])
    content = re.sub(r"(<!-- START_BOARD -->)(.*?)(<!-- END_BOARD -->)",
                     f"<!-- START_BOARD -->\n```\n{board_str}```\n<!-- END_BOARD -->",  
                     content, flags=re.DOTALL) 

    content = re.sub(r"<!-- CURRENT_TURN -->.*", f"<!-- CURRENT_TURN --> {state['turn']}", content) 
    content = re.sub(r"<!-- LAST_MOVE -->.*", f"<!-- LAST_MOVE --> {state['last_move']}", content)
    content = re.sub(r"<!-- RED_WINS -->.*", f"<!-- RED_WINS --> {state['red_wins']}", content)  
    content = re.sub(r"<!-- BLACK_WINS -->.*", f"<!-- BLACK_WINS --> {state['black_wins']}", content)  
    content = re.sub(r"<!-- GAMES_PLAYED -->.*", f"<!-- GAMES_PLAYED --> {state['games_played']}", content) 

    with open(README_FILE, "w") as f: 
        f.write(content)
 
def play_turn(state):
    #execute a single turn in the game
    board = state["board"]
    turn = state["turn"] 
    player = turn
    opp = 'r' if  player == 'b' else  'b' 

    if player == 'r':
        alg = state["red_algo"] 
    else:
        alg = state["black_algo"]
 
    moves = get_all_moves(board, player)
    if not moves: 
        #current player cannot move, opponent wins
        winner = opp
        if winner == 'r':
            state["red_wins"] += 1
        else:
            state["black_wins"] += 1
        state = reset_game(state) 
        return state

    chosen_move = choose_move(moves, alg, board, player) 
    if chosen_move:
        new_board = apply_move(board, chosen_move)
        state["board"] = new_board
        #record last move 
        (sr, sc) = chosen_move["start"]
        (er, ec) = chosen_move["jump_path"][-1]
        cols = "abcdefgh" 
        start_square = f"{cols[sc]}{sr+1}" 
        end_square = f"{cols[ec]}{er+1}"
        state["last_move"] = f"{player.upper()} moved {start_square} -> {end_square} (captures: {chosen_move['captures']})"

    #check winner
    winner = check_winner(state["board"])
    if winner:
        if winner == 'r':
            state["red_wins"] += 1
        else:
            state["black_wins"] += 1
        state = reset_game(state)
        return state

    #switch turn
    state["turn"] = opp
    return state

if __name__ == "__main__":
    state = load_state()
    #if new game (no algo chosen), choose now
    if state["red_algo"] is None or state["black_algo" ] is None: 
        state = reset_game(state)

    #simulate a few moves each run
    for _ in range(5):
        state = play_turn(state)
    save_state(state)
    update_readme(state)
