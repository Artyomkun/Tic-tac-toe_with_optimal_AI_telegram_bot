import json
import random
import os
import logging
import time
import asyncio
from copy import deepcopy
import sys
from filelock import FileLock, Timeout
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

WEB3_URL = "https://tic-tac-toewithoptimalaitelegrambot-production.up.railway.app/"

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN or not isinstance(BOT_TOKEN, str) or len(BOT_TOKEN.split(':')) != 2:
    print("❌ Ошибка: Неверный или отсутствует BOT_TOKEN.")
    sys.exit(1)
else:
    print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")

# Настройки
settings = {
    "logs_enabled": True,
    "language": "ru",
    "ai_delay": 0.3,
    "adaptivity_level": 0.7,
    "difficulty": "medium",
}

ai_memory = {}
human_memory = {}
ai_logs = []
stats = {
    "AI": {"wins": 0, "losses": 0, "draws": 0},
    "Human": {"wins": 0, "losses": 0, "draws": 0},
}

bot_state = {}  # Changed from list to dictionary
user_data = {}

# Переводы
translations = {
    "ru": {
        "welcome_message": "Добро пожаловать в Крестики-Нолики! 🎮\nВыберите язык:",
        "game_start": "Игра начинается! Вы - {player}, ИИ - {opponent}. Ваш ход!",
        "invalid_move": "Неверный ход! В режиме ИИ против ИИ ходят только ИИ.",
        "player_wins": "{player} побеждает! 🏆",
        "draw": "Ничья! 🤝",
        "play_again": "Сыграть еще?",
        "yes_button": "Да",
        "no_button": "Нет",
        "game_exit": "Игра завершена. До встречи! 👋",
        "difficulty_prompt": "Выберите сложность",
        "invalid_difficulty": "Неверная сложность. Используйте: easy, medium, hard",
        "difficulty_set": "Сложность установлена: {difficulty}",
        "language_prompt": "Выберите язык",
        "language_set": "Язык установлен: {language}",
        "ai_move": "ИИ ({player}) ходит на позицию {move}.",
        "settings_menu": "Выберите настройку",
        "ai_thinking": "ИИ думает...",
        "game_mode_prompt": "Выберите режим игры:",
        "classic_mode": "Классическая игра",
        "player_vs_ai": "Игрок против ИИ",
        "ai_vs_player": "ИИ против игрока",
        "ai_vs_ai": "ИИ против ИИ",
        "choose_symbol": "Выберите символ (X или O):",
        "error_message": "Ошибка! Доска не обновлена. Перезапустите игру (/start).",
        "invalid_symbol": "Неверный символ. Используйте: X или O",
        "your_turn": "Ваш ход!",
        "return_to_menu": "Вернуться в меню",
        "main_menu": "Главное меню",
        "play_again_or_menu": "Хотите сыграть еще раз или вернуться в меню?",
        "play_button": "Играть",
        "profile_button": "Профиль",
        "info_button": "Инфо",
        "feature_coming_soon": "Функция скоро появится",
    },
    "en": {
        "welcome_message": "Welcome to Tic-Tac-Toe! 🎮\nChoose a language:",
        "game_start": "Game starts! You are {player}, AI is {opponent}. Your turn!",
        "invalid_move": "Invalid move! In AI vs AI mode, only AI moves are allowed.",
        "player_wins": "{player} wins! 🏆",
        "draw": "It's a draw! 😊",
        "play_again": "Play again?",
        "yes_button": "Yes",
        "no_button": "No",
        "game_exit": "Game over! See you next time! 😊",
        "difficulty_prompt": "Choose difficulty:",
        "invalid_difficulty": "Invalid difficulty! Use: easy, medium, hard",
        "difficulty_set": "Difficulty set: {difficulty}",
        "language_prompt": "Choose a language:",
        "language_set": "Language set: to {language}",
        "ai_move": "AI ({player}) moves to position {move}.",
        "settings_menu": "Select a setting:",
        "ai_thinking": "AI is thinking...",
        "game_mode_prompt": "Choose a game mode:",
        "classic_mode": "Classic Game",
        "player_vs_ai": "Player vs AI",
        "ai_vs_player": "AI vs Player",
        "ai_vs_ai": "AI vs AI",
        "choose_symbol": "Choose symbol (X or O):",
        "error_message": "Error! Board not showing? Restart the game (/start).",
        "invalid_symbol": "Invalid symbol! Use: X or O",
        "your_turn": "Your turn!",
        "return_to_menu": "Return to menu",
        "main_menu": "Main Menu",
        "play_again_or_menu": "Do you want to play again or return to menu?",
        "play_button": "Play",
        "profile_button": "Profile",
        "info_button": "Info",
        "feature_coming_soon": "Feature coming soon",
    },
    "ja": {
        "welcome_message": "チックタックトーへようこそ！🎮\n言語を選択してください：",
        "game_start": "ゲームが始まります！あなたは{player}、AIは{opponent}です。あなたのターン！",
        "invalid_move": "無効な手です！AI対AIモードではAIのみが手を打てます。",
        "player_wins": "{player}の勝利！🏆",
        "draw": "引き分け！🤝",
        "play_again": "もう一度プレイしますか？",
        "yes_button": "はい",
        "no_button": "いいえ",
        "game_exit": "ゲーム終了！またね！👋",
        "difficulty_prompt": "難易度を選択してください",
        "invalid_difficulty": "無効な難易度です。easy、medium、hardを使用してください",
        "difficulty_set": "難易度が{difficulty}に設定されました",
        "language_prompt": "言語を選択してください",
        "language_set": "言語が{language}に設定されました",
        "ai_move": "AI（{player}）が位置{move}に手を打ちました。",
        "settings_menu": "設定を選択してください",
        "ai_thinking": "AIが考え中...",
        "game_mode_prompt": "ゲームモードを選択してください：",
        "classic_mode": "クラシックゲーム",
        "player_vs_ai": "プレイヤー対AI",
        "ai_vs_player": "AI対プレイヤー",
        "ai_vs_ai": "AI対AI",
        "choose_symbol": "シンボルを選択してください（XまたはO）：",
        "error_message": "エラー！ボードが更新されていません。ゲームを再起動してください（/start）。",
        "invalid_symbol": "無効なシンボルです。XまたはOを使用してください",
        "your_turn": "あなたのターン！",
        "return_to_menu": "メニューに戻る",
        "main_menu": "メインメニュー",
        "play_again_or_menu": "もう一度プレイしますか、それともメニューに戻りますか？",
        "play_button": "プレイ",
        "profile_button": "プロフィール",
        "info_button": "情報",
        "feature_coming_soon": "機能は近日公開予定です",
    }
}

def get_text(context: dict, key: str, **kwargs) -> str:
    lang = context.get("bot_data", {}).get("language", settings["language"])
    if lang not in translations:
        logger.warning(f"Language {lang} not supported, falling back to 'ru'")
        lang = "ru"
        context.get("bot_data", {})["language"] = lang
    text = translations[lang].get(key, translations["ru"].get(key, key))
    return text.format(**kwargs if kwargs else {})

def create_symbol_keyboard(context: dict) -> ReplyKeyboardMarkup:
    keyboard = [["X", "O"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def save_board_state(user_id: int, board: list, move_count: int):
    try:
        state_file = "board_state.json"
        data = {}
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
        data[str(user_id)] = {"board": board, "move_count": move_count, "timestamp": time.time()}
        with open(state_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved board state for user {user_id}: {board}, move_count: {move_count}")
    except Exception as e:
        logger.error(f"Failed to save board state for user {user_id}: {e}")

def load_board_state(user_id: int) -> tuple | None:
    try:
        state_file = "board_state.json"
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
            if str(user_id) in data:
                state = data[str(user_id)]
                board = state["board"]
                move_count = state["move_count"]
                if (isinstance(board, list) and len(board) == 9 and all(c in [" ", "X", "O"] for c in board)):
                    logger.debug(f"Loaded board state for user {user_id}: {board}, move_count: {move_count}")
                    return board, move_count
                else:
                    logger.warning(f"Invalid board state for user {user_id}: {board}")
        return None
    except Exception as e:
        logger.error(f"Failed to load board state for user {user_id}: {e}")
        return None

def clear_board_state(user_id: int):
    try:
        state_file = "board_state.json"
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
            if str(user_id) in data:
                del data[str(user_id)]
                with open(state_file, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"Cleared board state for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to clear board state for user {user_id}: {e}")

def create_board():
    return [" " for _ in range(9)]

def format_board(board: list) -> str:
    display = [board[i] if board[i] in ["X", "O"] else " " for i in range(9)]
    return (
        f"{display[0]} | {display[1]} | {display[2]}\n"
        f"---------\n"
        f"{display[3]} | {display[4]} | {display[5]}\n"
        f"---------\n"
        f"{display[6]} | {display[7]} | {display[8]}"
    )

def create_keyboard(board: list, interactive: bool = True):
    keyboard = [
        [
            board[i * 3 + j] if board[i * 3 + j] in ["X", "O"] else str(i * 3 + j + 1) if interactive else " "
            for j in range(3)
        ]
        for i in range(3)
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_main_menu_keyboard(context: dict):
    keyboard = [
        [get_text(context, "play_button")],
        [get_text(context, "profile_button"), get_text(context, "info_button")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def create_language_keyboard():
    keyboard = [
        ["Русский (ru)"],
        ["English (en)"],
        ["日本語 (ja)"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def create_game_mode_keyboard(context: dict) -> ReplyKeyboardMarkup:
    logger.debug("Creating game mode keyboard")
    keyboard = [
        [get_text(context, "player_vs_ai")],
        [get_text(context, "ai_vs_player")],
        [get_text(context, "ai_vs_ai")],
        ["Web3"]
    ]
    logger.debug(f"Game mode keyboard created: {keyboard}")
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=get_text(context, "game_mode_prompt")
    )

def check_winner(board: list, player: str) -> bool:
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    return any(board[a] == board[b] == board[c] == player for a, b, c in wins)

def is_board_full(board: list) -> bool:
    return " " not in board

def get_available_moves(board: list) -> list:
    return [i for i, spot in enumerate(board) if spot == " "]

def log_move(board: list, move: int, player: str):
    if settings["logs_enabled"]:
        ai_logs.append({"board": board[:], "move": move, "player": player})

def update_stats(winner: str | None):
    if winner == "AI":
        stats["AI"]["wins"] += 1
        stats["Human"]["losses"] += 1
    elif winner == "Human":
        stats["Human"]["wins"] += 1
        stats["AI"]["losses"] += 1
    else:
        stats["AI"]["draws"] += 1
        stats["Human"]["draws"] += 1

def evaluate_board(board: list) -> int | None:
    if check_winner(board, "O"):
        return 1
    elif check_winner(board, "X"):
        return -1
    elif is_board_full(board):
        return 0
    return None

def minimax(board: list, depth: int, is_maximizing: bool, player: str, opponent: str, alpha: float=-float("inf"), beta: float=float("inf")) -> float:
    score = evaluate_board(board)
    if score is not None:
        return score
    if is_maximizing:
        best_score = -float("inf")
        for move in get_available_moves(board):
            board[move] = player
            score = minimax(board, depth + 1, False, player, opponent, alpha, beta)
            board[move] = " "
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = float("inf")
        for move in get_available_moves(board):
            board[move] = opponent
            score = minimax(board, depth + 1, True, player, opponent, alpha, beta)
            board[move] = " "
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score

def ai_move(board: list, player: str, difficulty: str) -> int | None:
    start_time = time.time()
    try:
        if not board or len(board) != 9 or not all(c in [" ", "X", "O"] for c in board):
            logger.error(f"Invalid board state: {board}")
            return None
        
        board_copy = deepcopy(board)
        opponent = "O" if player == "X" else "X"
        available_moves = get_available_moves(board_copy)
        
        if not available_moves:
            logger.warning(f"No available moves for player {player}, board: {board_copy}")
            return None

        if difficulty == "easy":
            move = random.choice(available_moves)
        
        elif difficulty == "medium":
            if random.random() < settings["adaptivity_level"]:
                key = str(tuple(board_copy))
                memory = ai_memory if player == "X" else human_memory
                if key in memory and memory[key]["moves"] and len(memory[key]["moves"]) == len(memory[key]["weights"]):
                    try:
                        move = random.choices(memory[key]["moves"], weights=memory[key]["weights"])[0]
                        if move not in available_moves:
                            logger.warning(f"Invalid move {move} for {player}, board: {board_copy}")
                            move = random.choice(available_moves)
                    except Exception as e:
                        logger.error(f"Error in memory selection for {player}, key: {key}, error: {e}")
                        move = random.choice(available_moves)
                else:
                    move = random.choice(available_moves)
            else:
                move = random.choice(available_moves)
        
        else:  # hard
            key = str(tuple(board_copy))
            if key in ai_memory and ai_memory[key]["moves"] and len(ai_memory[key]["moves"]) == len(ai_memory[key]["weights"]):
                try:
                    move = random.choices(ai_memory[key]["moves"], weights=ai_memory[key]["weights"])[0]
                    if move not in available_moves:
                        logger.warning(f"Invalid move {move} for {player}, board: {board_copy}")
                        move = random.choice(available_moves)
                except Exception as e:
                    logger.error(f"Error in memory selection for hard mode {player}, key: {key}, error: {e}")
                    move = random.choice(available_moves)
            else:
                try:
                    best_score = float("-inf") if player == "O" else float("inf")
                    best_moves = []
                    for move in available_moves:
                        board_copy[move] = player
                        score = minimax(board_copy, 0, player == "X", player, opponent)
                        board_copy[move] = " "
                        if player == "O":
                            if score > best_score:
                                best_score = score
                                best_moves = [move]
                            elif score == best_score:
                                best_moves.append(move)
                        else:
                            if score < best_score:
                                best_score = score
                                best_moves = [move]
                            elif score == best_score:
                                best_moves.append(move)
                    if not best_moves:
                        logger.warning(f"No best moves found for {player}, board: {board_copy}")
                        move = random.choice(available_moves)
                    else:
                        move = random.choice(best_moves)
                        update_memory(board_copy, move, player, "pending")
                except Exception as e:
                    logger.error(f"Error in minimax for {player}, key: {key}, error: {e}")
                    move = random.choice(available_moves)
        
        if move is None or move < 0 or move >= 9 or board_copy[move] != " ":
            logger.error(f"Invalid AI move {move} for {player}, board: {board_copy}")
            return None
        
        logger.debug(f"AI move {move} for {player} took {time.time() - start_time:.2f}s")
        return move
    
    except Exception as e:
        logger.error(f"Unexpected error in ai_move for {player}, board: {board}, error: {e}")
        return None

def update_memory(board: list, move: int, player: str, outcome: str):
    board_key = str(tuple(board))
    memory = ai_memory if player == "O" else human_memory
    if len(memory) > 1000:
        removed_key = list(memory.keys())[0]
        memory.pop(removed_key)
        logger.debug(f"Removed old memory key {removed_key} to limit size")
    if board_key not in memory:
        memory[board_key] = {"moves": [], "weights": []}
    if move not in memory[board_key]["moves"]:
        memory[board_key]["moves"].append(move)
        memory[board_key]["weights"].append(1 if outcome == "win" else 0.5)
    else:
        idx = memory[board_key]["moves"].index(move)
        memory[board_key]["weights"][idx] += 1 if outcome == "win" else 0.5

async def try_update_message(message, text, reply_markup, context, max_retries=3, initial_delay=1):
    if context.get("last_message_text") == text and context.get("last_board_state") == reply_markup:
        logger.debug("Skipped duplicate message update")
        return message

    for attempt in range(max_retries):
        try:
            await message.edit_text(text=text, reply_markup=reply_markup)
            context["last_message_text"] = text
            context["last_board_state"] = reply_markup
            return message
        except Exception as e:
            logger.warning(f"Edit attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(initial_delay * (2 ** attempt))
    try:
        new_message = await message.chat.send_message(text=text, reply_markup=reply_markup)
        context["last_message_text"] = text
        context["last_board_state"] = reply_markup
        logger.info("Sent new message as fallback after edit failed")
        await asyncio.sleep(0.1)  # Задержка для избежания лимитов
        return new_message
    except Exception as e:
        logger.error(f"Failed to send fallback message: {e}")
        return None

async def send_error_message(message, context):
    await message.reply(
        text=get_text(context, "error_message"),
        reply_markup=create_main_menu_keyboard(context)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    logger.debug(f"Processing /start for user {user_id}")
    bot_state.clear()  # Clear previous state
    bot_state["awaiting_language"] = True
    await update.message.reply_text(
        text=get_text({"bot_data": bot_state}, "welcome_message"),
        reply_markup=create_language_keyboard()
    )

async def set_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    args = message.text.split()[1:] if message.text.split() else []
    logger.debug(f"Processing /difficulty for user {message.chat.id}, args: {args}")
    if args and args[0].lower() in ["easy", "medium", "hard"]:
        settings["difficulty"] = args[0].lower()
        await message.reply_text(
            text=get_text({"bot_data": bot_state}, "difficulty_set", difficulty=args[0].lower()),
            reply_markup=create_main_menu_keyboard({"bot_data": bot_state})
        )
    else:
        await message.reply_text(
            text=get_text({"bot_data": bot_state}, "difficulty_prompt") + "\n" + get_text({"bot_data": bot_state}, "invalid_difficulty"),
            reply_markup=create_main_menu_keyboard({"bot_data": bot_state})
        )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    logger.debug(f"Processing /language for user {message.chat.id}")
    bot_state["awaiting_language"] = True
    await message.reply_text(
        text=get_text({"bot_data": bot_state}, "language_prompt"),
        reply_markup=create_language_keyboard()
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    logger.debug(f"Processing /settings for user {message.chat.id}")
    await message.reply_text(
        text=get_text({"bot_data": bot_state}, "settings_menu"),
        reply_markup=create_main_menu_keyboard({"bot_data": bot_state})
    )

async def web3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    logger.debug(f"Processing /web3 for user {user_id}")
    keyboard = [[InlineKeyboardButton("Play Web3", url=f"{WEB3_URL}?user_id={user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Play in Web3:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text.strip().lower() if message.text else ""
    user_data = {"bot_data": bot_state}
    user_id = message.chat.id
    logger.debug(f"Received message: '{text}' from user {user_id}, user_data: {user_data}, bot_state: {bot_state}")

    # Пропуск неизвестных команд
    if text.startswith('/') and not any(cmd in text for cmd in ["start", "difficulty", "language", "settings", "web3"]):
        logger.debug(f"Skipping unknown command: {text}")
        return

    if bot_state.get("awaiting_language"):
        logger.debug(f"Processing language selection: {text}")
        lang_map = {
            "русский (ru)": "ru",
            "english (en)": "en",
            "日本語 (ja)": "ja"
        }
        if text in lang_map:
            bot_state["language"] = lang_map[text]
            bot_state["awaiting_language"] = False
            logger.debug(f"Language set to: {bot_state['language']}")
            await message.reply_text(
                text=get_text(user_data, "language_set", language=bot_state["language"]),
                reply_markup=create_main_menu_keyboard(user_data)
            )
        else:
            await message.reply_text(
                text=get_text(user_data, "language_prompt"),
                reply_markup=create_language_keyboard()
            )
        return

    mode_map = {
        get_text(user_data, "play_button").lower(): "play_button",
        get_text(user_data, "player_vs_ai").lower(): "player_vs_ai",
        get_text(user_data, "ai_vs_player").lower(): "ai_vs_player",
        get_text(user_data, "ai_vs_ai").lower(): "ai_vs_ai",
        "web3": "web3",
        get_text(user_data, "profile_button").lower(): "profile_button",
        get_text(user_data, "info_button").lower(): "info_button"
    }

    if text in mode_map:
        selected_mode = mode_map[text]
        logger.debug(f"Processing button: {selected_mode}, current language: {bot_state.get('language', 'default')}")

        if selected_mode == "play_button":
            bot_state["awaiting_mode"] = True
            await message.reply_text(
                text=get_text(user_data, "game_mode_prompt"),
                reply_markup=create_game_mode_keyboard(user_data)
            )
            return

        if bot_state.get("awaiting_mode"):
            if selected_mode == "player_vs_ai":
                bot_state["awaiting_mode"] = False
                bot_state["awaiting_symbol"] = True
                await message.reply_text(
                    text=get_text(user_data, "choose_symbol"),
                    reply_markup=create_symbol_keyboard(user_data)
                )
            elif selected_mode == "ai_vs_player":
                bot_state["awaiting_mode"] = False
                bot_state["awaiting_symbol"] = True
                await message.reply_text(
                    text=get_text(user_data, "choose_symbol"),
                    reply_markup=create_symbol_keyboard(user_data)
                )
            elif selected_mode == "ai_vs_ai":
                bot_state["awaiting_mode"] = False
                await start_ai_vs_ai(update, context)
            elif selected_mode == "web3":
                bot_state["awaiting_mode"] = False
                keyboard = [[InlineKeyboardButton("Play Web3", url=f"{WEB3_URL}?user_id={user_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.reply_text(
                    text="Play in Web3:",
                    reply_markup=reply_markup
                )
            return
        elif selected_mode in ["profile_button", "info_button"]:
            await message.reply_text(
                text=get_text(user_data, "feature_coming_soon"),
                reply_markup=create_main_menu_keyboard(user_data)
            )
            return

    if bot_state.get("awaiting_symbol"):
        logger.debug(f"Processing symbol selection: {text}")
        if text in ["x", "o"]:
            bot_state["human_player"] = text.upper()
            bot_state["ai_player"] = "O" if text.upper() == "X" else "X"
            bot_state["awaiting_symbol"] = False
            await start_player_vs_ai(update, context, player_first=True)
        else:
            await message.reply_text(
                text=get_text(user_data, "invalid_symbol"),
                reply_markup=create_symbol_keyboard(user_data)
            )
        return

    if bot_state.get("game_active"):
        board = bot_state.get("board")
        try:
            move = int(text) - 1
            bot_state["invalid_input_count"] = bot_state.get("invalid_input_count", 0)
            if 0 <= move < 9 and board[move] == " ":
                human_player = bot_state["human_player"]
                board[move] = human_player
                log_move(board, move, human_player)
                update_memory(board[:], move, human_player, "win" if check_winner(board, human_player) else "pending")
                bot_state["move_count"] = bot_state.get("move_count", 0) + 1
                logger.debug(f"Move {bot_state['move_count']}: Human move: {move}, Board: {board}")
                save_board_state(user_id, board, bot_state["move_count"])

                if check_winner(board, human_player):
                    await message.reply_text(
                        text=get_text(user_data, "player_wins", player=human_player) + f"\n\n{format_board(board)}",
                        reply_markup=create_main_menu_keyboard(user_data)
                    )
                    update_stats("Human")
                    bot_state["game_active"] = False
                    clear_board_state(user_id)
                    return

                if bot_state["move_count"] >= 9:
                    await message.reply_text(
                        text=get_text(user_data, "draw") + f"\n\n{format_board(board)}",
                        reply_markup=create_main_menu_keyboard(user_data)
                    )
                    update_stats(None)
                    bot_state["game_active"] = False
                    clear_board_state(user_id)
                    return

                game_message = await message.reply_text(
                    text=get_text(user_data, "ai_thinking"),
                    reply_markup=create_keyboard(board, interactive=True)
                )

                await asyncio.sleep(settings["ai_delay"])
                ai_player = bot_state["ai_player"]
                ai_move_idx = ai_move(board, ai_player, settings["difficulty"])
                if ai_move_idx is None or ai_move_idx < 0 or ai_move_idx >= 9 or board[ai_move_idx] != " ":
                    logger.error(f"AI invalid move: {ai_move_idx}, board: {board}")
                    await send_error_message(message, user_data)
                    bot_state["game_active"] = False
                    clear_board_state(user_id)
                    return

                board[ai_move_idx] = ai_player
                log_move(board, ai_move_idx, ai_player)
                update_memory(board[:], ai_move_idx, ai_player, "win" if check_winner(board, ai_player) else "pending")
                bot_state["move_count"] += 1
                logger.debug(f"Move {bot_state['move_count']}: AI move: {ai_move_idx}, Board: {board}")
                save_board_state(user_id, board, bot_state["move_count"])

                if check_winner(board, ai_player):
                    await try_update_message(
                        game_message,
                        get_text(user_data, "player_wins", player=ai_player) + f"\n\n{format_board(board)}",
                        create_main_menu_keyboard(user_data),
                        user_data
                    )
                    update_stats("AI")
                    bot_state["game_active"] = False
                    clear_board_state(user_id)
                    return

                if bot_state["move_count"] >= 9:
                    await try_update_message(
                        game_message,
                        get_text(user_data, "draw") + f"\n\n{format_board(board)}",
                        create_main_menu_keyboard(user_data),
                        user_data
                    )
                    update_stats(None)
                    bot_state["game_active"] = False
                    clear_board_state(user_id)
                    return

                await try_update_message(
                    game_message,
                    get_text(user_data, "your_turn") + f"\n\n{format_board(board)}",
                    create_keyboard(board, interactive=True),
                    user_data
                )
            else:
                bot_state["invalid_input_count"] += 1
                if bot_state["invalid_input_count"] >= 5:
                    await send_error_message(message, user_data)
                    bot_state["game_active"] = False
                    clear_board_state(user_id)
                    return
                await message.reply_text(
                    text=get_text(user_data, "invalid_move"),
                    reply_markup=create_keyboard(board, interactive=True)
                )
        except ValueError as e:
            logger.warning(f"Invalid input: {text}, error: {e}")
            bot_state["invalid_input_count"] = bot_state.get("invalid_input_count", 0) + 1
            if bot_state["invalid_input_count"] >= 5:
                await send_error_message(message, user_data)
                bot_state["game_active"] = False
                clear_board_state(user_id)
                return
            await message.reply_text(
                text=get_text(user_data, "invalid_move"),
                reply_markup=create_keyboard(board, interactive=True)
            )
        return

    logger.debug(f"Unknown message: {text}, sending main menu")
    await message.reply_text(
        text=get_text(user_data, "main_menu"),
        reply_markup=create_main_menu_keyboard(user_data)
    )

async def start_player_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, player_first=True):
    message = update.message
    user_id = message.chat.id
    saved_state = load_board_state(user_id)
    if saved_state:
        board, move_count = saved_state
        bot_state["board"] = board
        bot_state["move_count"] = move_count
        logger.debug(f"Restored board state for user {user_id} in start_player_vs_ai: {bot_state}")
    else:
        bot_state["board"] = create_board()
        bot_state["move_count"] = 0
    bot_state.update({
        "game_active": True,
        "invalid_input_count": 0,
    })
    board = bot_state["board"]
    human_player = bot_state.get("human_player", "X")
    ai_player = bot_state.get("ai_player", "O")

    first_player = human_player if player_first else ai_player
    await message.reply_text(
        text=get_text({"bot_data": bot_state}, "game_start", player=human_player, opponent=ai_player) +
        f"\n\nFirst move: {first_player}\n\n{format_board(board)}",
        reply_markup=create_keyboard(board, interactive=True)
    )
    save_board_state(user_id, board, bot_state["move_count"])

    if not player_first:
        game_message = await message.reply_text(
            text=get_text({"bot_data": bot_state}, "ai_thinking"),
            reply_markup=create_keyboard(board, interactive=True)
        )
        await asyncio.sleep(settings["ai_delay"])
        ai_move_idx = ai_move(board, ai_player, settings["difficulty"])
        if ai_move_idx is None or ai_move_idx < 0 or ai_move_idx >= 9 or board[ai_move_idx] != " ":
            logger.error(f"AI invalid move: {ai_move_idx}, board: {board}")
            await send_error_message(message, {"bot_data": bot_state})
            bot_state["game_active"] = False
            clear_board_state(user_id)
            return

        board[ai_move_idx] = ai_player
        log_move(board, ai_move_idx, ai_player)
        update_memory(board[:], ai_move_idx, ai_player, "win" if check_winner(board, ai_player) else "pending")
        bot_state["move_count"] += 1
        logger.debug(f"Move {bot_state['move_count']}: AI move: {ai_move_idx}, Board: {board}")
        save_board_state(user_id, board, bot_state["move_count"])

        if check_winner(board, ai_player):
            await try_update_message(
                game_message,
                get_text({"bot_data": bot_state}, "player_wins", player=ai_player) + f"\n\n{format_board(board)}",
                create_main_menu_keyboard({"bot_data": bot_state}),
                {"bot_data": bot_state}
            )
            update_stats("AI")
            bot_state["game_active"] = False
            clear_board_state(user_id)
            return

        if is_board_full(board):
            await try_update_message(
                game_message,
                get_text({"bot_data": bot_state}, "draw") + f"\n\n{format_board(board)}",
                create_main_menu_keyboard({"bot_data": bot_state}),
                {"bot_data": bot_state}
            )
            update_stats(None)
            bot_state["game_active"] = False
            clear_board_state(user_id)
            return

        await try_update_message(
            game_message,
            get_text({"bot_data": bot_state}, "your_turn") + f"\n\n{format_board(board)}",
            create_keyboard(board, interactive=True),
            {"bot_data": bot_state}
        )


async def start_ai_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.chat.id
    saved_state = load_board_state(user_id)
    if saved_state:
        board, move_count = saved_state
        bot_state["board"] = board
        bot_state["move_count"] = move_count
        logger.debug(f"Loaded board state for user {user_id} in start_ai_vs_ai: {bot_state}")
    else:
        bot_state["board"] = create_board()
        bot_state["move_count"] = 0
    bot_state.update({
        "game_active": True,
    })
    board = bot_state["board"]
    game_message = await message.reply_text(
        text=get_text({"bot_data": bot_state}, "game_start", player="AI1 (X)", opponent="AI2 (O)") +
        f"\nFirst move: X\n{format_board(board)}",
        reply_markup=create_keyboard(board, interactive=False)
    )
    save_board_state(user_id, board, bot_state["move_count"])

    move_count = 0
    max_moves = 9
    start_time = time.time()
    max_duration = 60
    while bot_state.get("game_active") and move_count < max_moves and time.time() - start_time <= max_duration:
        for player in ["X", "O"]:
            if not bot_state.get("game_active"):
                break
            move_count += 1
            bot_state["move_count"] = move_count
            board_copy = deepcopy(board)
            await asyncio.sleep(settings["ai_delay"])
            move = ai_move(board_copy, player, settings["difficulty"])
            if move is None or move < 0 or move >= 9 or board_copy[move] != " ":
                logger.error(f"Invalid move {move} by {player}, board: {board_copy}")
                await send_error_message(message, {"bot_data": bot_state})
                bot_state["game_active"] = False
                clear_board_state(user_id)
                await message.reply_text(
                    text=get_text({"bot_data": bot_state}, "main_menu"),
                    reply_markup=create_main_menu_keyboard({"bot_data": bot_state})
                )
                return

            board[move] = player
            log_move(board, move, player)
            update_memory(board[:], move, player, "win" if check_winner(board, player) else "pending")
            save_board_state(user_id, board, bot_state["move_count"])

            result_text = get_text({"bot_data": bot_state}, "ai_move", player=player, move=move + 1) + f"\n\n{format_board(board)}"
            game_message = await try_update_message(
                game_message,
                result_text,
                create_keyboard(board, interactive=False),
                {"bot_data": bot_state}
            )
            if not game_message:
                game_message = await message.reply_text(
                    text=result_text,
                    reply_markup=create_keyboard(board, interactive=False)
                )

            if check_winner(board, player) or is_board_full(board):
                result_text = get_text({"bot_data": bot_state}, "player_wins", player=player) if check_winner(board, player) else get_text({"bot_data": bot_state}, "draw")
                game_message = await try_update_message(
                    game_message,
                    f"{result_text}\n\n{format_board(board)}\n\n" + get_text({"bot_data": bot_state}, "main_menu"),
                    create_main_menu_keyboard({"bot_data": bot_state}),
                    {"bot_data": bot_state}
                )
                if not game_message:
                    game_message = await message.reply_text(
                        text=f"{result_text}\n\n{format_board(board)}\n\n" + get_text({"bot_data": bot_state}, "main_menu"),
                        reply_markup=create_main_menu_keyboard({"bot_data": bot_state})
                    )
                update_stats("AI" if check_winner(board, player) else None)
                bot_state["game_active"] = False
                clear_board_state(user_id)
                return

            if move_count >= max_moves or time.time() - start_time > max_duration:
                result_text = get_text({"bot_data": bot_state}, "draw")
                game_message = await try_update_message(
                    game_message,
                    f"{result_text}\n\n{format_board(board)}\n\n" + get_text({"bot_data": bot_state}, "main_menu"),
                    create_main_menu_keyboard({"bot_data": bot_state}),
                    {"bot_data": bot_state}
                )
                if not game_message:
                    await message.reply_text(
                        text=f"{result_text}\n\n{format_board(board)}\n\n" + get_text({"bot_data": bot_state}, "main_menu"),
                        reply_markup=create_main_menu_keyboard({"bot_data": bot_state})
                    )
                update_stats(None)
                bot_state["game_active"] = False
                clear_board_state(user_id)
                return
            await asyncio.sleep(0.05)

    # Ensure main menu is shown if the loop exits unexpectedly
    if bot_state.get("game_active"):
        await message.reply_text(
            text=get_text({"bot_data": bot_state}, "main_menu"),
            reply_markup=create_main_menu_keyboard({"bot_data": bot_state})
        )
        bot_state["game_active"] = False
        clear_board_state(user_id)

def acquire_lock():
    lock = FileLock("bot.lock")
    try:
        lock.acquire(timeout=1.0)
        return lock
    except:
        print("Error: Another bot instance is running. Exiting...")
        sys.exit(1)

def main():
    lock = acquire_lock()
    try:
        # Инициализация приложения
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("Starting application...")

        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("difficulty", set_difficulty))
        application.add_handler(CommandHandler("language", set_language))
        application.add_handler(CommandHandler("settings", settings_command))
        application.add_handler(CommandHandler("web3", web3_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Запуск бота
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
    finally:
        lock.release()
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")
            logger.debug("Removed bot.lock file")

if __name__ == "__main__":
    main()