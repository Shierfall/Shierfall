import os
import re
import json
import random
from PIL import Image, ImageDraw, ImageFont

#file and directory configurations
STATE_FILE = "game_state.json"
README_FILE = "README.md"
GIF_DIR = "frames"
GIF_FILE = "checkers_game.gif"

#ensure the frames directory exists
os.makedirs(GIF_DIR, exist_ok=True)

#initial board configuration for standard checkers:
#'r'/'b' for normal pieces, 'R'/'B' for kings, '.' for empty
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
    """Load the game state from the JSON file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "board": [row[:] for row in INITIAL_BOARD],
            "turn": "r",  #'r' for Red, 'b' for Black
            "games_played": 0,
            "red_wins": 0,
            "black_wins": 0,
            "last_move": "",
            "frame_number": 0,
            "red_algo": None,
            "black_algo": None
        }

def save_state(state):
    """Save the current game state to the JSON file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def in_bounds(r, c):
    """Check if the given row and column are within the board boundaries."""
    return 0 <= r < 8 and 0 <= c < 8

def render_board_image(board, last_move, turn):
    """
    Render the current state of the board as an image.

    Parameters:
    - board (list): 2D list representing the board.
    - last_move (str): Description of the last move.
    - turn (str): Current turn ('r' or 'b').

    Returns:
    - PIL.Image: Rendered image of the board.
    """
    cell_size = 60
    board_size = cell_size * 8
    img = Image.new('RGB', (board_size, board_size + 60), color='white')
    draw = ImageDraw.Draw(img)

    #draw the board squares
    for r in range(8):
        for c in range(8):
            top_left = (c * cell_size, r * cell_size)
            bottom_right = ((c + 1) * cell_size, (r + 1) * cell_size)
            fill = '#EEEED2' if (r + c) % 2 == 0 else '#769656'
            draw.rectangle([top_left, bottom_right], fill=fill)

            #draw the pieces
            piece = board[r][c]
            if piece != '.':
                color = 'red' if piece.lower() == 'r' else 'black'
                center = (c * cell_size + cell_size // 2, r * cell_size + cell_size // 2)
                radius = cell_size // 3
                draw.ellipse(
                    [center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius],
                    fill=color
                )
                if piece.isupper():
                    #king indicator
                    font = ImageFont.load_default()
                    text = "K"
                    text_size = draw.textsize(text, font=font)
                    text_position = (center[0] - text_size[0] // 2, center[1] - text_size[1] // 2)
                    draw.text(text_position, text, fill='yellow', font=font)

    #add text for last move and current turn
    font = ImageFont.load_default()
    draw.text((10, board_size + 10), f"Turn: {'Red' if turn == 'r' else 'Black'}", fill='black', font=font)
    draw.text((10, board_size + 30), f"Last Move: {last_move}", fill='black', font=font)

    return img

def save_frame(state):
    """Save the current frame as a PNG image."""
    board = state["board"]
    last_move = state["last_move"]
    turn = state["turn"]
    img = render_board_image(board, last_move, turn)
    frame_number = state.get("frame_number", 0)
    frame_path = os.path.join(GIF_DIR, f"frame_{frame_number:04d}.png")
    img.save(frame_path)
    state["frame_number"] = frame_number + 1
    return state

def create_gif():
    """Create or update the animated GIF from saved frames."""
    frames = []
    frame_files = sorted([f for f in os.listdir(GIF_DIR) if f.startswith("frame_") and f.endswith(".png")])
    for file in frame_files:
        frame = Image.open(os.path.join(GIF_DIR, file))
        frames.append(frame)
    if frames:
        frames[0].save(GIF_FILE, save_all=True, append_images=frames[1:], duration=1000, loop=0)

def cleanup_frames():
    """Remove older frames to limit the number of stored frames."""
    frame_files = sorted([f for f in os.listdir(GIF_DIR) if f.startswith("frame_") and f.endswith(".png")])
    max_frames = 100  #Adjust as needed
    for file in frame_files[:-max_frames]:
        os.remove(os.path.join(GIF_DIR, file))

def update_readme_with_gif(state):
    """Update the README.md with the latest GIF and game statistics."""
    with open(README_FILE, "r") as f:
        content = f.read()

    #update the GIF
    content = re.sub(
        r"(<!-- START_GIF -->)(.*?)(<!-- END_GIF -->)",
        f"<!-- START_GIF -->\n![Checkers Game](./{GIF_FILE})\n<!-- END_GIF -->",
        content,
        flags=re.DOTALL
    )

    #update game info placeholders
    content = re.sub(r"<!-- CURRENT_TURN -->.*", f"<!-- CURRENT_TURN --> {'Red' if state['turn'] == 'r' else 'Black'}", content)
    content = re.sub(r"<!-- LAST_MOVE -->.*", f"<!-- LAST_MOVE --> {state['last_move']}", content)
    content = re.sub(r"<!-- RED_WINS -->.*", f"<!-- RED_WINS --> {state['red_wins']}", content)
    content = re.sub(r"<!-- BLACK_WINS -->.*", f"<!-- BLACK_WINS --> {state['black_wins']}", content)
    content = re.sub(r"<!-- GAMES_PLAYED -->.*", f"<!-- GAMES_PLAYED --> {state['games_played']}", content)

    with open(README_FILE, "w") as f:
        f.write(content)

def play_turn(state):
    """Execute a single turn in the game."""
    board = state["board"]
    turn = state["turn"]
    player = turn
    opp = 'r' if player == 'b' else 'b'

    #select AI algorithm
    if player == 'r':
        algo = state["red_algo"]
    else:
        algo = state["black_algo"]

    #get all legal moves for the current player
    moves = get_all_moves(board, player)

    if not moves:
        #no legal moves, opponent wins
        winner = opp
        if winner == 'r':
            state["red_wins"] += 1
        else:
            state["black_wins"] += 1
        state = reset_game(state)
        return state

    #choose a move based on the selected AI algorithm
    chosen_move = choose_move(moves, algo, board, player)
    if chosen_move:
        state["board"] = apply_move(board, chosen_move)
        #record last move in a readable format
        (sr, sc) = chosen_move["start"]
        (er, ec) = chosen_move["end"]
        cols = "abcdefgh"
        start_square = f"{ cols[sc]}{sr+1}"
        end_square = f"{cols[ec]}{er+1}"
        captures = chosen_move["captures"]
        state["last_move"] = f"{'Red' if player == 'r' else 'Black'} moved {start_square} -> {end_square} (captures: {captures})"

    #check for a winn
    winner = check_winner(state["board"])
    if winner:
        if winner ==  'r':
            state["red_wins"] += 1
        else:
            state["black_wins"] += 1
        state = reset_game(state)
        return state

    #switch turn to the opponent
    state["turn"] = opp
    return state

def reset_game(state):
    """Reset the game to the initial state and assign new AI algorithms."""
    state["board"] = [row[:] for row in INITIAL_BOARD]
    state["turn"] = "r"
    state["games_played"] += 1
    #Randomly assign AI algorithms to both players
    algos = ["random", "aggressive", "defensive", "center", "promotion"]
    state["red_algo"] = random.choice(algos)
    state["black_algo"] = random.choice(algos)
    state["last_move"] = ""
    state["frame_number"] = 0
    #Clear existing frames
    for file in os.listdir(GIF_DIR):
        if file.startswith("frame_") and file.endswith(".png"):
            os.remove(os.path.join(GIF_DIR, file))
    return state

def check_winner(board):
    """Determine if there's a winner."""
    reds = sum(cell.lower() == 'r' for row in board for cell in row)
    blacks = sum(cell.lower() == 'b' for row in board for cell in row)
    if reds == 0:
        return 'b'
    if blacks == 0:
        return 'r'
    return None

def get_all_moves(board, player):
    """Retrieve all possible legal moves for the current player."""
    moves = []
    capturing_moves =  []

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece.lower() != player:
                continue
            piece_moves = get_piece_moves(board, r, c, piece)
            for move in piece_moves:
                if move["captures"] > 0:
                    capturing_moves.append(move)
                else:
                    moves.append(move)

    if capturing_moves:
        return capturing_moves  
    return moves

def get_piece_moves(board, r, c, piece):
    """Generate all legal moves for a specific piece."""
    moves = []
    directions = get_directions(piece)
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            if board[nr][nc] == '.':
                #simple move
                moves.append({
                    "start": (r, c),
                    "end": (nr, nc),
                    "captures": 0
                })
            elif is_opponent(board[nr][nc], piece):
                #possible capture
                jr, jc = nr + dr, nc + dc
                if in_bounds(jr, jc) and board[jr][jc] == '.':
                    moves.append({
                        "start": (r, c),
                        "end": (jr, jc),
                        "captures": 1
                    })
    return moves

def get_directions(piece):
    """Determine movement directions based on the piece type."""
    if piece.lower() == 'r':
        directions = [(-1, -1), (-1, 1)]
    else:
        directions = [(1, -1), (1, 1)]

    if piece.isupper():
        #kings can move both forward and backward
        opposite_directions = [(-dr, -dc) for dr, dc in directions]
        directions += opposite_directions

    return directions

def is_opponent(piece, current_piece):
    """Check if a piece belongs to the opponent."""
    if piece == '.':
        return False
    return (piece.lower() != current_piece.lower())

def apply_move(board, move):
    """Apply a move to the board."""
    sr, sc = move["start"]
    er, ec = move["end"]
    captures = move["captures"]

    piece = board[sr][sc]
    board[sr][sc] = '.'
    board[er][ec] = piece

    if captures > 0:
        #remove the captured piece
        mid_r = (sr + er) // 2
        mid_c = (sc + ec) // 2
        board[mid_r][mid_c] = '.'

    #handle king promotion
    if piece == 'r' and er == 0:
        board[er][ec] = 'R'
    elif piece == 'b' and er == 7:
        board[er][ec] = 'B'

    return board

def choose_move(moves, algorithm, board, player):
    """
    Choose a move based on the specified AI algorithm.

    Parameters:
    - moves (list): List of possible moves.
    - algorithm (str): AI algorithm name.
    - board (list): Current board state.
    - player (str): Current player ('r' or 'b').

    Returns:
    - dict: Selected move or None.
    """
    if not moves:
        return None

    if algorithm == "random":
        return random.choice(moves)

    elif algorithm == "aggressive":
        #prioritize moves with captures
        capturing_moves = [m for m in moves if m["captures"] > 0]
        if capturing_moves:
            #choose the move with the maximum captures
            max_captures = max(m["captures"] for m in capturing_moves)
            top_moves = [m for m in capturing_moves if m["captures"] == max_captures]
            return random.choice(top_moves)
        return random.choice(moves)

    elif algorithm == "defensive":
        #Choose moves that minimize opponent's capturing opportunities
        def safety_score(move):
            temp_board = [row[:] for row in board]
            apply_move(temp_board, move)
            opponent = 'b' if player == 'r' else 'r'
            opponent_moves = get_all_moves(temp_board, opponent)
            opponent_captures = [m for m in opponent_moves if m["captures"] > 0]
            return len(opponent_captures)

        moves_sorted = sorted(moves, key=safety_score)
        return moves_sorted[0] if moves_sorted else None

    elif algorithm == "center":
        #prefer moves towards the center columns (columns 3 and 4)
        def center_distance(move):
            _, ec = move["end"]
            return min(abs(ec - 3), abs(ec - 4))

        moves_sorted = sorted(moves, key=center_distance)
        return moves_sorted[0] if moves_sorted else None

    elif algorithm == "promotion":
        #Prefer moves that advance pieces towards promotion
        if player == 'r':
            def promotion_score(move):
                _, er = move["end"]
                return er  #Lower row number is better for Red
        else:
            def promotion_score(move):
                _, er = move["end"]
                return 7 - er  #Higher row number is better for Black

        moves_sorted = sorted(moves, key=promotion_score, reverse=True)
        return moves_sorted[0] if moves_sorted else None

    else:
        #default to random if unknown algorithm
        return random.choice(moves)

if __name__ == "__main__":
    #Load the current game state
    state = load_state()

    #if algorithms are not assigned, reset the game and assign algorithms
    if state["red_algo"] is None or state["black_algo"] is None:
        state = reset_game(state)
    state = play_turn(state)
    state = save_frame(state)
    save_state(state)
    create_gif()
    cleanup_frames()
    update_readme_with_gif(state)
