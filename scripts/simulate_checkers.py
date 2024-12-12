import os
import json
import random
import re
import logging
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("simulate_checkers.log"),
        logging.StreamHandler()
    ]
)

# File and directory configurations
STATE_FILE = "game_state.json"
README_FILE = "README.md"
GIF_DIR = "frames"
GIF_FILE = "checkers_game.gif"

# Ensure the frames directory exists
os.makedirs(GIF_DIR, exist_ok=True)

# Initial board configuration for standard checkers:
# 'r'/'b' for normal pieces, 'R'/'B' for kings, '.' for empty
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
    """Load the game state from a JSON file."""
    if not os.path.exists(STATE_FILE):
        return reset_state()

    with open(STATE_FILE, "r") as f:
        try:
            state = json.load(f)
            # Ensure all required keys are present
            required_keys = ["games_played", "red_wins", "black_wins", "draws", "ai_stats"]
            if not all(key in state for key in required_keys):
                logging.warning("State file missing required keys. Resetting state.")
                return reset_state()
            # Ensure AI stats contain all strategies
            for player in ["red", "black"]:
                for algo in ["random", "aggressive", "defensive", "center", "promotion"]:
                    if algo not in state["ai_stats"][player]:
                        state["ai_stats"][player][algo] = 0
            return state
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Error loading state file: {e}. Resetting state.")
            return reset_state()


def save_state(state):
    """Save the current game state to the JSON file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


def reset_state():
    """Reset the game state to initial values."""
    return {
        "games_played": 0,
        "red_wins": 0,
        "black_wins": 0,
        "draws": 0,
        "ai_stats": {
            "red": {algo: 0 for algo in ["random", "aggressive", "defensive", "center", "promotion"]},
            "black": {algo: 0 for algo in ["random", "aggressive", "defensive", "center", "promotion"]}
        }
    }


def in_bounds(r, c):
    """Check if the given row and column are within the board boundaries."""
    return 0 <= r < 8 and 0 <= c < 8


def serialize_board(board):
    """Convert the board into a tuple of tuples for hashing."""
    return tuple(tuple(row) for row in board)


def has_repetition(board_history, current_board):
    """Check if the current board state has occurred previously."""
    return board_history.count(current_board) >= 3


def render_board_image(board, last_move, turn, game_number):
    """
    Render the current state of the board as an image.

    Parameters:
    - board (list): 2D list representing the board.
    - last_move (str): Description of the last move.
    - turn (str): Current turn ('r' or 'b').
    - game_number (int): The current game number for separation.

    Returns:
    - PIL.Image: Rendered image of the board.
    """
    cell_size = 40
    board_size = cell_size * 8
    img = Image.new('RGB', (board_size, board_size + 100), color='white')
    draw = ImageDraw.Draw(img)

    # Draw the board squares
    for r in range(8):
        for c in range(8):
            top_left = (c * cell_size, r * cell_size)
            bottom_right = ((c + 1) * cell_size, (r + 1) * cell_size)
            fill = '#EEEED2' if (r + c) % 2 == 0 else '#769656'
            draw.rectangle([top_left, bottom_right], fill=fill)

            # Draw the pieces
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
                    # King indicator
                    font = ImageFont.load_default()
                    text = "K"
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
                    text_position = (center[0] - text_size[0] // 2, center[1] - text_size[1] // 2)
                    draw.text(text_position, text, fill='yellow', font=font)

    # Add separation between games
    separation_y = board_size + 40
    draw.line([(0, separation_y), (board_size, separation_y)], fill='gray', width=2)
    draw.text((10, separation_y + 5), f"Game {game_number} Completed", fill='black', font=ImageFont.load_default())

    # Add text for last move and current turn
    font = ImageFont.load_default()
    draw.text((10, board_size + 10), f"Turn: {'Red' if turn == 'r' else 'Black'}", fill='black', font=font)
    draw.text((10, board_size + 30), f"Last Move: {last_move}", fill='black', font=font)

    return img


def save_frame(img, game_number, move_number):
    """Save the current frame as a PNG image."""
    frame_path = os.path.join(GIF_DIR, f"game_{game_number}_move_{move_number:04d}.png")
    try:
        img.save(frame_path)
        logging.info(f"Saved frame: {frame_path}")
    except Exception as e:
        logging.error(f"Error saving frame {frame_path}: {e}")


def create_gif():
    """Create or update the animated GIF from saved frames."""
    frames = []
    frame_files = sorted([
        f for f in os.listdir(GIF_DIR)
        if f.startswith("game_") and f.endswith(".png")
    ])
    for file in frame_files:
        try:
            frame = Image.open(os.path.join(GIF_DIR, file))
            frames.append(frame)
        except Exception as e:
            logging.error(f"Error loading frame {file}: {e}")
    if frames:
        try:
            frames[0].save(GIF_FILE, save_all=True, append_images=frames[1:], duration=500, loop=0)
            logging.info(f"Animated GIF created/updated: {GIF_FILE}")
        except Exception as e:
            logging.error(f"Error creating/updating GIF: {e}")
    else:
        logging.warning("No frames found to create GIF.")


def cleanup_old_frames():
    """Remove older frames to manage repository size."""
    frame_files = sorted([
        f for f in os.listdir(GIF_DIR)
        if f.startswith("game_") and f.endswith(".png")
    ])
    max_frames = 2000  # Adjust as needed (e.g., 20 games * ~100 moves)
    for file in frame_files[:-max_frames]:
        try:
            os.remove(os.path.join(GIF_DIR, file))
            logging.info(f"Removed old frame: {file}")
        except Exception as e:
            logging.error(f"Error removing frame {file}: {e}")


def update_readme(state):
    """Update README.md with the latest GIF and statistics."""
    if not os.path.exists(README_FILE):
        logging.error(f"{README_FILE} does not exist. Please ensure it is present in the repository.")
        return

    with open(README_FILE, "r") as f:
        content = f.read()

    # Update the GIF
    content = re.sub(
        r"(<!-- START_GIF -->)(.*?)(<!-- END_GIF -->)",
        f"<!-- START_GIF -->\n![Checkers Game](./{GIF_FILE})\n<!-- END_GIF -->",
        content,
        flags=re.DOTALL
    )

    # Update game info placeholders
    content = re.sub(r"<!-- GAMES_PLAYED -->.*", f"<!-- GAMES_PLAYED --> {state['games_played']}", content)
    content = re.sub(r"<!-- RED_WINS -->.*", f"<!-- RED_WINS --> {state['red_wins']}", content)
    content = re.sub(r"<!-- BLACK_WINS -->.*", f"<!-- BLACK_WINS --> {state['black_wins']}", content)
    content = re.sub(r"<!-- DRAWS -->.*", f"<!-- DRAWS --> {state['draws']}", content)

    # Update AI statistics
    ai_stats_red = state["ai_stats"]["red"]
    ai_stats_black = state["ai_stats"]["black"]
    ai_stats_text = "\n**AI Strategy Stats:**\n\n" \
                    "Red AI:\n" \
                    f"- Random: {ai_stats_red['random']}\n" \
                    f"- Aggressive: {ai_stats_red['aggressive']}\n" \
                    f"- Defensive: {ai_stats_red['defensive']}\n" \
                    f"- Center-Seeking: {ai_stats_red['center']}\n" \
                    f"- Promotion-Oriented: {ai_stats_red['promotion']}\n\n" \
                    "Black AI:\n" \
                    f"- Random: {ai_stats_black['random']}\n" \
                    f"- Aggressive: {ai_stats_black['aggressive']}\n" \
                    f"- Defensive: {ai_stats_black['defensive']}\n" \
                    f"- Center-Seeking: {ai_stats_black['center']}\n" \
                    f"- Promotion-Oriented: {ai_stats_black['promotion']}\n"

    content = re.sub(r"<!-- AI_STATS -->.*", f"<!-- AI_STATS -->{ai_stats_text}", content, flags=re.DOTALL)

    try:
        with open(README_FILE, "w") as f:
            f.write(content)
        logging.info(f"Updated {README_FILE} with latest GIF and statistics.")
    except Exception as e:
        logging.error(f"Error updating {README_FILE}: {e}")


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
    capturing_moves = []

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
        return capturing_moves  # Must capture if possible
    return moves


def get_piece_moves(board, r, c, piece):
    """Generate all legal moves for a specific piece."""
    moves = []
    directions = get_directions(piece)
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            if board[nr][nc] == '.':
                # Simple move
                moves.append({
                    "start": (r, c),
                    "end": (nr, nc),
                    "captures": 0
                })
            elif is_opponent(board[nr][nc], piece):
                # Possible capture
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
        # Kings can move both forward and backward
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
        # Remove the captured piece
        mid_r = (sr + er) // 2
        mid_c = (sc + ec) // 2
        board[mid_r][mid_c] = '.'

    # Handle king promotion
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
        # Prioritize capturing moves with additional heuristics
        capturing_moves = [m for m in moves if m["captures"] > 0]
        if capturing_moves:
            # Further prioritize based on position or advancement
            capturing_moves.sort(key=lambda m: heuristic_aggressive(m, board, player), reverse=True)
            return capturing_moves[0]
        return random.choice(moves)

    elif algorithm == "defensive":
        # Prioritize moves that minimize opponent's capturing opportunities
        defensive_moves = [m for m in moves if heuristic_defensive(m, board, player)]
        if defensive_moves:
            return defensive_moves[0]
        return random.choice(moves)

    elif algorithm == "center":
        # Prefer moves towards the center columns (columns 3 and 4)
        moves_sorted = sorted(moves, key=lambda m: heuristic_center(m), reverse=True)
        return moves_sorted[0] if moves_sorted else random.choice(moves)

    elif algorithm == "promotion":
        # Prefer moves that advance pieces towards promotion
        if player == 'r':
            moves_sorted = sorted(moves, key=lambda m: heuristic_promotion_red(m), reverse=True)
        else:
            moves_sorted = sorted(moves, key=lambda m: heuristic_promotion_black(m), reverse=True)
        return moves_sorted[0] if moves_sorted else random.choice(moves)

    else:
        # Default to random if unknown algorithm
        return random.choice(moves)


def heuristic_aggressive(move, board, player):
    """Assign a score to a move based on aggressive strategy."""
    score = move["captures"] * 10  # Base score for captures
    _, ec = move["end"]
    # Prefer central columns
    score += (3 - abs(ec - 3.5))
    return score


def heuristic_defensive(move, board, player):
    """Determine if a move is defensive."""
    # Example: Avoid moves that leave pieces vulnerable
    # Placeholder logic: Always True
    # Implement specific defensive heuristics as needed
    return True


def heuristic_center(move):
    """Assign a score based on how central the move is."""
    _, ec = move["end"]
    center = 3.5
    distance = abs(ec - center)
    # Closer to center gets higher score
    return 3.5 - distance


def heuristic_promotion_red(move):
    """Assign a score based on how close Red's piece is to promotion."""
    _, er = move["end"]
    return 7 - er  # Lower row number is better for Red


def heuristic_promotion_black(move):
    """Assign a score based on how close Black's piece is to promotion."""
    _, er = move["end"]
    return er  # Higher row number is better for Black


def play_game(game_number, state):
    """
    Play a single game of Checkers.

    Parameters:
    - game_number (int): The current game number.
    - state (dict): The cumulative game state.

    Returns:
    - None
    """
    board = [row[:] for row in INITIAL_BOARD]
    turn = "r"  # 'r' for Red, 'b' for Black

    # Assign AI algorithms for this game
    algos = ["random", "aggressive", "defensive", "center", "promotion"]
    red_algo = random.choice(algos)
    black_algo = random.choice(algos)
    state["ai_stats"]["red"][red_algo] += 1
    state["ai_stats"]["black"][black_algo] += 1
    logging.info(f"Game {game_number}: Red AI - {red_algo}, Black AI - {black_algo}")

    move_number = 0
    last_move = ""
    max_moves = 70  # Set the move limit to 70
    board_history = []

    # Serialize initial board and add to history
    serialized = serialize_board(board)
    board_history.append(serialized)

    while move_number < max_moves:
        player = turn
        opp = 'b' if player == 'r' else 'r'
        algo = red_algo if player == 'r' else black_algo

        # Get all legal moves for the current player
        moves = get_all_moves(board, player)

        if not moves:
            # No legal moves, opponent wins
            winner = opp
            if winner == 'r':
                state["red_wins"] += 1
            else:
                state["black_wins"] += 1
            logging.info(f"Game {game_number}: {'Red' if winner == 'r' else 'Black'} wins (no legal moves).")
            break

        # Choose a move based on the AI algorithm
        chosen_move = choose_move(moves, algo, board, player)
        if chosen_move:
            board = apply_move(board, chosen_move)
            # Record last move in a readable format
            (sr, sc) = chosen_move["start"]
            (er, ec) = chosen_move["end"]
            cols = "abcdefgh"
            start_square = f"{cols[sc]}{sr+1}"
            end_square = f"{cols[ec]}{er+1}"
            captures = chosen_move["captures"]
            last_move = f"{'Red' if player == 'r' else 'Black'} moved {start_square} -> {end_square} (captures: {captures})"
            logging.info(f"Game {game_number}, Move {move_number + 1}: {last_move}")

        # Save frame
        img = render_board_image(board, last_move, turn, game_number)
        save_frame(img, game_number, move_number)

        # Serialize current board and check for repetition
        serialized = serialize_board(board)
        board_history.append(serialized)
        repetition_count = board_history.count(serialized)
        if repetition_count >= 3:
            logging.info(f"Game {game_number}: Repetition detected {repetition_count} times. Declaring a draw.")
            state["draws"] += 1
            break

        # Check for a winner after the move
        winner = check_winner(board)
        if winner:
            if winner == 'r':
                state["red_wins"] += 1
            else:
                state["black_wins"] += 1
            logging.info(f"Game {game_number}: {'Red' if winner == 'r' else 'Black'} wins.")
            break

        # Switch turn to the opponent
        turn = opp
        move_number += 1

    else:
        # Max moves reached without a clear winner
        red_pieces = sum(row.count('r') + row.count('R') for row in board)
        black_pieces = sum(row.count('b') + row.count('B') for row in board)
        if red_pieces > black_pieces:
            winner = 'r'
            state["red_wins"] += 1
            logging.info(f"Game {game_number}: Move limit reached. Red wins with more pieces ({red_pieces} vs {black_pieces}).")
        elif black_pieces > red_pieces:
            winner = 'b'
            state["black_wins"] += 1
            logging.info(f"Game {game_number}: Move limit reached. Black wins with more pieces ({black_pieces} vs {red_pieces}).")
        else:
            logging.info(f"Game {game_number}: Move limit reached. The game is a draw ({red_pieces} vs {black_pieces}).")
            state["draws"] += 1

        # Save the final frame
        img = render_board_image(board, last_move, turn, game_number)
        save_frame(img, game_number, move_number)


def play_turn(state):
    """
    Execute a set number of games of Checkers.

    Parameters:
    - state (dict): The cumulative game state.

    Returns:
    - None
    """
    num_games = 20
    for game_number in range(state["games_played"] + 1, state["games_played"] + num_games + 1):
        play_game(game_number, state)


def update_readme(state):
    """Update README.md with the latest GIF and statistics."""
    if not os.path.exists(README_FILE):
        logging.error(f"{README_FILE} does not exist. Please ensure it is present in the repository.")
        return

    with open(README_FILE, "r") as f:
        content = f.read()

    # Update the GIF
    content = re.sub(
        r"(<!-- START_GIF -->)(.*?)(<!-- END_GIF -->)",
        f"<!-- START_GIF -->\n![Checkers Game](./{GIF_FILE})\n<!-- END_GIF -->",
        content,
        flags=re.DOTALL
    )

    # Update game info placeholders
    content = re.sub(r"<!-- GAMES_PLAYED -->.*", f"<!-- GAMES_PLAYED --> {state['games_played']}", content)
    content = re.sub(r"<!-- RED_WINS -->.*", f"<!-- RED_WINS --> {state['red_wins']}", content)
    content = re.sub(r"<!-- BLACK_WINS -->.*", f"<!-- BLACK_WINS --> {state['black_wins']}", content)
    content = re.sub(r"<!-- DRAWS -->.*", f"<!-- DRAWS --> {state['draws']}", content)

    # Update AI statistics
    ai_stats_red = state["ai_stats"]["red"]
    ai_stats_black = state["ai_stats"]["black"]
    ai_stats_text = "\n**AI Strategy Stats:**\n\n" \
                    "Red AI:\n" \
                    f"- Random: {ai_stats_red['random']}\n" \
                    f"- Aggressive: {ai_stats_red['aggressive']}\n" \
                    f"- Defensive: {ai_stats_red['defensive']}\n" \
                    f"- Center-Seeking: {ai_stats_red['center']}\n" \
                    f"- Promotion-Oriented: {ai_stats_red['promotion']}\n\n" \
                    "Black AI:\n" \
                    f"- Random: {ai_stats_black['random']}\n" \
                    f"- Aggressive: {ai_stats_black['aggressive']}\n" \
                    f"- Defensive: {ai_stats_black['defensive']}\n" \
                    f"- Center-Seeking: {ai_stats_black['center']}\n" \
                    f"- Promotion-Oriented: {ai_stats_black['promotion']}\n"

    content = re.sub(r"<!-- AI_STATS -->.*", f"<!-- AI_STATS -->{ai_stats_text}", content, flags=re.DOTALL)

    try:
        with open(README_FILE, "w") as f:
            f.write(content)
        logging.info(f"Updated {README_FILE} with latest GIF and statistics.")
    except Exception as e:
        logging.error(f"Error updating {README_FILE}: {e}")


def main():
    """Main function to execute the simulation."""
    try:
        state = load_state()
        play_turn(state)
        save_state(state)
        create_gif()
        cleanup_old_frames()
        update_readme(state)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
