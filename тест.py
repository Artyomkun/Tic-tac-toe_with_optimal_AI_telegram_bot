import os
import json
import random
import time
import asyncio
import logging
import sys
from copy import deepcopy
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv
from filelock import FileLock

def acquire_lock():
    lock = FileLock("bot.lock")
    try:
        lock.acquire(timeout=1.0)
        return lock
    except:
        print("Error: Another bot instance is running. Exiting...")
        sys.exit(1)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN or not isinstance(BOT_TOKEN, str) or len(BOT_TOKEN.split(':')) != 2:
    print("❌ Ошибка: Неверный или отсутствует BOT_TOKEN.")
    sys.exit(1)
else:
    print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = {
    "logs_enabled": True,
    "language": "ru",
    "ai_delay": 5,
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
        "tic_tac_toe_web3": "Tic Tac Toe Web3",
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
        "game_over_returning": "Игра окончена. Возвращаемся в меню."
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
        "tic_tac_toe_web3": "Tic Tac Toe Web3",
        "choose_symbol": "Choose symbol (X or O):",
        "error_message": "Error! Board not showing? Restart the game (/start).",
        "invalid_symbol": "Invalid symbol! Use: X или O",
        "your_turn": "Your turn!",
        "return_to_menu": "Return to menu",
        "main_menu": "Main Menu",
        "play_again_or_menu": "Do you want to play again or return to menu?",
        "play_button": "Play",
        "profile_button": "Profile",
        "info_button": "Info",
        "feature_coming_soon": "Feature coming soon",
        "game_over_returning": "Game over. Returning to menu."
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
        "tic_tac_toe_web3": "Tic Tac Toe Web3 ゲーム",
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
        "game_over_returning": "ゲーム終了。メニューに戻ります。"
    },
    "it": {
        "welcome_message": "Benvenuto a Tris! 🎮\nScegli una lingua:",
        "game_start": "La partita inizia! Sei {player}, l'IA è {opponent}. Tocca a te!",
        "invalid_move": "Mossa non valida! In modalità IA contro IA, solo l'IA può muovere.",
        "player_wins": "{player} vince! 🏆",
        "draw": "Pareggio! 🤝",
        "play_again": "Giocare di nuovo?",
        "yes_button": "Sì",
        "no_button": "No",
        "game_exit": "Partita terminata! A presto! 👋",
        "difficulty_prompt": "Scegli la difficoltà",
        "invalid_difficulty": "Difficoltà non valida. Usa: easy, medium, hard",
        "difficulty_set": "Difficoltà impostata: {difficulty}",
        "language_prompt": "Scegli una lingua",
        "language_set": "Lingua impostata: {language}",
        "ai_move": "L'IA ({player}) muove alla posizione {move}.",
        "settings_menu": "Seleziona un'impostazione",
        "ai_thinking": "L'IA sta pensando...",
        "game_mode_prompt": "Scegli una modalità di gioco:",
        "classic_mode": "Gioco Classico",
        "player_vs_ai": "Giocatore contro IA",
        "ai_vs_player": "IA contro Giocatore",
        "ai_vs_ai": "IA contro IA",
        "tic_tac_toe_web3": "Tic Tac Toe Web3",
        "choose_symbol": "Scegli un simbolo (X o O):",
        "error_message": "Errore! La scacchiera non si aggiorna? Riavvia il gioco (/start).",
        "invalid_symbol": "Simbolo non valido. Usa: X o O",
        "your_turn": "Tocca a te!",
        "return_to_menu": "Torna al menu",
        "main_menu": "Menu Principale",
        "play_again_or_menu": "Vuoi giocare di nuovo o tornare al menu?",
        "play_button": "Gioca",
        "profile_button": "Profilo",
        "info_button": "Info",
        "feature_coming_soon": "Funzionalità in arrivo",
        "game_over_returning": "Partita finita. Torniamo al menu."
    },
    "hi": {
        "welcome_message": "टिक-टैक-टो में आपका स्वागत है! 🎮\nएक भाषा चुनें:",
        "game_start": "खेल शुरू होता है! आप {player} हैं, AI {opponent} है। आपकी बारी!",
        "invalid_move": "अमान्य चाल! AI बनाम AI मोड में, केवल AI चालें अनुमत हैं।",
        "player_wins": "{player} जीता! 🏆",
        "draw": "ड्रॉ! 🤝",
        "play_again": "फिर से खेलें?",
        "yes_button": "हाँ",
        "no_button": "नहीं",
        "game_exit": "खेल समाप्त! फिर मिलेंगे! 👋",
        "difficulty_prompt": "कठिनाई चुनें",
        "invalid_difficulty": "अमान्य कठिनाई! उपयोग करें: easy, medium, hard",
        "difficulty_set": "कठिनाई सेट: {difficulty}",
        "language_prompt": "एक भाषा चुनें:",
        "language_set": "भाषा सेट: {language}",
        "ai_move": "AI ({player}) स्थिति {move} पर चाल चलता है।",
        "settings_menu": "एक सेटिंग चुनें:",
        "ai_thinking": "AI सोच रहा है...",
        "game_mode_prompt": "एक खेल मोड चुनें:",
        "classic_mode": "क्लासिक खेल",
        "player_vs_ai": "खिलाड़ी बनाम AI",
        "ai_vs_player": "AI बनाम खिलाड़ी",
        "ai_vs_ai": "AI बनाम AI",
        "tic_tac_toe_web3": "Tic Tac Toe Web3",
        "choose_symbol": "प्रतीक चुनें (X या O):",
        "error_message": "त्रुटि! बोर्ड नहीं दिख रहा है? खेल को पुनः आरंभ करें (/start)।",
        "invalid_symbol": "अमान्य प्रतीक! उपयोग करें: X या O",
        "your_turn": "आपकी बारी!",
        "return_to_menu": "मेनू पर लौटें",
        "main_menu": "मुख्य मेनू",
        "play_again_or_menu": "क्या आप फिर से खेलना चाहते हैं या मेनू पर लौटना चाहते हैं?",
        "play_button": "खेलें",
        "profile_button": "प्रोफ़ाइल",
        "info_button": "जानकारी",
        "feature_coming_soon": "फ़ीचर जल्द ही आ रहा है",
        "game_over_returning": "खेल समाप्त। मेनू पर लौट रहे हैं।"
    }
}

def get_text(context: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    lang = context.user_data.get("language", settings["language"])
    if lang not in translations:
        logger.warning(f"Language {lang} not supported, falling back to 'ru'")
        lang = "ru"
        context.user_data["language"] = lang
    text = translations[lang].get(key, translations["ru"].get(key, key))
    return text.format(**kwargs if kwargs else {})

def save_board_state(user_id: int, board: list, move_count: int):
    try:
        state_file = "board_state.json"
        data = {}
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
        data[str(user_id)] = {
            "board": board,
            "move_count": move_count,
            "timestamp": time.time()
        }
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
                if (isinstance(board, list) and len(board) == 9 and
                    all(c in [" ", "X", "O"] for c in board)):
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

def create_main_menu_keyboard(context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [get_text(context, "play_button")],
        [get_text(context, "profile_button"), get_text(context, "info_button")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def create_language_keyboard():
    keyboard = [
        ["Русский (ru)"],
        ["English (en)"],
        ["日本語 (ja)"],
        ["Italiano (it)"],
        ["हिन्दी (hi)"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def create_game_mode_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    logger.debug("Creating game mode keyboard")
    keyboard = [
        [get_text(context, "classic_mode")],
        [get_text(context, "player_vs_ai")],
        [get_text(context, "ai_vs_player")],
        [get_text(context, "ai_vs_ai")],
        [get_text(context, "tic_tac_toe_web3")]
    ]
    logger.debug(f"Game mode keyboard created: {keyboard}")
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=get_text(context, "game_mode_prompt")
    )

def create_symbol_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    keyboard = [["X", "O"]]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
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

def ai_move(board: list, player: str, difficulty: str = None) -> int | None:
    start_time = time.time()
    board_copy = deepcopy(board)
    opponent = "O" if player == "X" else "X"
    available_moves = get_available_moves(board_copy)
    if not available_moves:
        logger.warning(f"No available moves for player {player}, board: {board_copy}")
        return None

    difficulty = difficulty or settings["difficulty"]

    if difficulty == "easy":
        move = random.choice(available_moves)
    elif difficulty == "medium":
        key = str(tuple(board_copy))
        memory = ai_memory if player == "O" else human_memory
        if key in memory and random.random() < settings["adaptivity_level"]:
            move = random.choices(memory[key]["moves"], weights=memory[key]["weights"], k=1)[0]
        else:
            move = random.choice(available_moves)
    else:  # hard
        key = str(tuple(board_copy))
        memory = ai_memory if player == "O" else human_memory
        if key in memory:
            move = random.choices(memory[key]["moves"], weights=memory[key]["weights"], k=1)[0]
        else:
            best_score = -float("inf") if player == "O" else float("inf")
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
            move = random.choice(best_moves)
            board_copy[move] = player
            outcome = "win" if check_winner(board_copy, player) else "draw" if is_board_full(board_copy) else "pending"
            update_memory(board_copy, move, player, outcome)
            board_copy[move] = " "

    if move is None or move < 0 or move >= 9 or board_copy[move] != " ":
        logger.error(f"Invalid AI move {move} for {player}, board: {board_copy}")
        return None
    logger.debug(f"AI move {move} for {player} took {time.time() - start_time:.2f}s")
    return move

def update_memory(board: list, move: int, player: str, outcome: str):
    board_key = str(tuple(board))
    memory = ai_memory if player == "O" else human_memory
    if len(memory) > 1000:
        oldest_key = next(iter(memory))
        memory.pop(oldest_key)
        logger.debug(f"Memory limit reached, removed oldest board state: {oldest_key}")
    if board_key not in memory:
        memory[board_key] = {"moves": [], "weights": []}
    if move not in memory[board_key]["moves"]:
        memory[board_key]["moves"].append(move)
        weight = 1.0 if outcome == "win" else 0.5 if outcome == "draw" else 0.1
        memory[board_key]["weights"].append(weight)
        logger.debug(f"Added new move {move} for board {board_key} with weight {weight}")
    else:
        idx = memory[board_key]["moves"].index(move)
        weight = memory[board_key]["weights"][idx]
        if outcome == "win":
            memory[board_key]["weights"][idx] = min(weight + 0.5, 2.0)
        elif outcome == "draw":
            memory[board_key]["weights"][idx] = min(weight + 0.2, 1.5)
        logger.debug(f"Updated weight for move {move} on board {board_key} to {memory[board_key]['weights'][idx]}")

async def try_update_message(message, text, reply_markup, context, max_retries=3, initial_delay=1):
    if context.user_data.get("last_message_text") == text and context.user_data.get("last_board_state") == reply_markup:
        logger.debug("Skipped duplicate message update")
        return message

    await asyncio.sleep(1.5)

    for attempt in range(max_retries):
        try:
            await message.edit_text(text=text, reply_markup=reply_markup)
            context.user_data["last_message_text"] = text
            context.user_data["last_board_state"] = reply_markup
            return message
        except Exception as e:
            logger.warning(f"Edit attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(initial_delay * (2 ** attempt))
    try:
        new_message = await message.chat.send_message(text=text, reply_markup=reply_markup)
        context.user_data["last_message_text"] = text
        context.user_data["last_board_state"] = reply_markup
        logger.info("Sent new message as fallback after edit failed")
        return new_message
    except Exception as e:
        logger.error(f"Failed to send fallback message: {e}")
        return None

async def send_error_message(message, context):
    await message.reply_text(
        text=get_text(context, "error_message"),
        reply_markup=create_main_menu_keyboard(context)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    clear_board_state(user_id)
    context.user_data.clear()
    context.user_data["language"] = settings["language"]
    saved_difficulty = load_user_settings(user_id)
    if saved_difficulty:
        context.user_data["difficulty"] = saved_difficulty
    logger.debug(f"Started bot for user {user_id}, initial user_data: {context.user_data}")
    await update.message.reply_text(
        text=get_text(context, "welcome_message"),
        reply_markup=create_language_keyboard()
    )
    await asyncio.sleep(1.5)
    context.user_data["awaiting_language"] = True

async def set_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].lower() in ["easy", "medium", "hard"]:
        context.user_data["difficulty"] = args[0].lower()
        save_user_settings(update.message.chat.id, args[0].lower())
        await update.message.reply_text(
            text=get_text(context, "difficulty_set", difficulty=args[0].lower()),
            reply_markup=create_main_menu_keyboard(context)
        )
        await asyncio.sleep(1.5)
    else:
        await update.message.reply_text(
            text=get_text(context, "difficulty_prompt") + "\n" + get_text(context, "invalid_difficulty"),
            reply_markup=create_difficulty_keyboard(context)
        )
        await asyncio.sleep(1.5)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=get_text(context, "language_prompt"),
        reply_markup=create_language_keyboard()
    )
    await asyncio.sleep(1.5)
    context.user_data["awaiting_language"] = True

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=get_text(context, "settings_menu"),
        reply_markup=create_main_menu_keyboard(context)
    )

def create_difficulty_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    logger.debug("Creating difficulty keyboard")
    keyboard = [
        ["easy"],
        ["medium"],
        ["hard"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=get_text(context, "difficulty_prompt")
    )

def save_user_settings(user_id: int, difficulty: str):
    try:
        settings_file = "user_settings.json"
        data = {}
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
        data[str(user_id)] = {"difficulty": difficulty}
        with open(settings_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved user settings for user {user_id}: difficulty={difficulty}")
    except Exception as e:
        logger.error(f"Failed to save user settings for user {user_id}: {e}")

def load_user_settings(user_id: int) -> str | None:
    try:
        settings_file = "user_settings.json"
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
            if str(user_id) in data:
                difficulty = data[str(user_id)].get("difficulty")
                if difficulty in ["easy", "medium", "hard"]:
                    logger.debug(f"Loaded user settings for user {user_id}: difficulty={difficulty}")
                    return difficulty
        return None
    except Exception as e:
        logger.error(f"Failed to load user settings for user {user_id}: {e}")
        return None
async def start_classic_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.message.chat.id

    # Загружаем сохранённое состояние игры, если оно есть
    saved_state = load_board_state(user_id)
    if saved_state:
        board, move_count = saved_state
        user_data["board"] = board
        user_data["move_count"] = move_count
        logger.debug(f"Loaded board state for user {user_id} in start_classic_game: {user_data}")
    else:
        user_data["board"] = create_board()
        user_data["move_count"] = 0

    # Устанавливаем начальные параметры игры
    user_data.update({
        "game_active": True,
        "last_board_state": None,
        "last_message_text": None,
        "game_mode": "classic_mode",
        "player1_symbol": user_data.get("player1_symbol", "X"),
        "player2_symbol": user_data.get("player2_symbol", "O"),
        "invalid_input_count": 0
    })

    board = user_data["board"]
    message = update.message
    current_player = user_data["player1_symbol"] if user_data["move_count"] % 2 == 0 else user_data["player2_symbol"]

    # Отправляем начальное сообщение с игровым полем
    game_message = await message.reply_text(
        text=get_text(context, "game_start", player=f"Player 1 ({user_data['player1_symbol']})", opponent=f"Player 2 ({user_data['player2_symbol']})") +
             f"\nCurrent turn: {current_player}\n\n{format_board(board)}",
        reply_markup=create_keyboard(board, interactive=True)
    )

    # Сохраняем начальное состояние доски
    save_board_state(user_id, board, user_data["move_count"])
    await asyncio.sleep(1.5)

async def start_player_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, player_first=True):
    user_data = context.user_data
    user_id = update.message.chat.id
    saved_state = load_board_state(user_id)
    if saved_state:
        board, move_count = saved_state
        user_data["board"] = board
        user_data["move_count"] = move_count
        logger.debug(f"Restored board state for user {user_id} in start_player_vs_AI: {user_data}")
    else:
        user_data["board"] = create_board()
        user_data["move_count"] = 0
    user_data.update({
        "game_active": True,
        "invalid_input_count": 0,
        "last_board_state": None,
        "last_message_text": None
    })
    board = user_data["board"]
    human_player = user_data.get("human_player", "X")
    ai_player = user_data.get("ai_player", "O")

    message = update.message
    first_player = human_player if player_first else ai_player
    game_message = await message.reply_text(
        text=get_text(context, "game_start", player=human_player, opponent=ai_player) +
        f"\n\nFirst move: {first_player}\n\n{format_board(board)}",
        reply_markup=create_keyboard(board, interactive=True)
    )
    save_board_state(user_id, board, user_data["move_count"])
    await asyncio.sleep(1.5)

    if not player_first:
        if not all(c in [" ", "X", "O"] for c in board):
            logger.error(f"Invalid board: {board}")
            user_data["board"] = create_board()
            save_board_state(user_id, user_data["board"], user_data["move_count"])
            await send_error_message(message, context)
            user_data["game_active"] = False
            return

        game_message = await try_update_message(
            game_message,
            get_text(context, "ai_thinking"),
            create_keyboard(board, interactive=True),
            context
        )
        await asyncio.sleep(settings["ai_delay"])
        ai_move_idx = ai_move(board, ai_player, user_data.get("difficulty", settings["difficulty"]))
        if ai_move_idx is None or ai_move_idx < 0 or ai_move_idx >= 9 or board[ai_move_idx] != " ":
            logger.error(f"AI invalid move: {ai_move_idx}, board: {board}")
            save_board_state(user_id, board, user_data["move_count"])
            await send_error_message(message, context)
            user_data["game_active"] = False
            return

        board[ai_move_idx] = ai_player
        log_move(board, ai_move_idx, ai_player)
        update_memory(board[:], ai_move_idx, ai_player, "win" if check_winner(board, ai_player) else "pending")
        user_data["move_count"] += 1
        logger.debug(f"Move {user_data['move_count']}: AI move: {ai_move_idx}, Board: {board}")
        save_board_state(user_id, board, user_data["move_count"])

        game_message = await try_update_message(
            game_message,
            get_text(context, "ai_move", player=ai_player, move=ai_move_idx + 1) + f"\n\n{format_board(board)}",
            create_keyboard(board, interactive=True),
            context
        )
        if not game_message:
            game_message = await message.reply_text(
                text=get_text(context, "ai_move", player=ai_player, move=ai_move_idx + 1) + f"\n\n{format_board(board)}",
                reply_markup=create_keyboard(board, interactive=True)
            )
        await asyncio.sleep(1.5)

        if check_winner(board, ai_player) or is_board_full(board):
            result_text = get_text(context, "player_wins", player=ai_player) if check_winner(board, ai_player) else get_text(context, "draw")
            game_message = await try_update_message(
                game_message,
                f"{result_text}\n\n{format_board(board)}\n\n{get_text(context, 'game_over_returning')}",
                create_keyboard(board, interactive=False),
                context
            )
            await asyncio.sleep(2.0)
            await message.reply_text(
                text=get_text(context, "main_menu"),
                reply_markup=create_main_menu_keyboard(context)
            )
            update_stats("AI" if check_winner(board, ai_player) else None)
            user_data["game_active"] = False
            clear_board_state(user_id)
            return

        game_message = await try_update_message(
            game_message,
            get_text(context, "your_turn") + f"\n\n{format_board(board)}",
            create_keyboard(board, interactive=True),
            context
        )
        if not game_message:
            game_message = await message.reply_text(
                text=get_text(context, "your_turn") + f"\n\n{format_board(board)}",
                reply_markup=create_keyboard(board, interactive=True)
            )
        await asyncio.sleep(1.5)

async def start_ai_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, difficulty: str = "medium"):
    user_data = context.user_data
    user_id = update.message.chat.id
    saved_state = load_board_state(user_id)
    if saved_state:
        board, move_count = saved_state
        user_data["board"] = board
        user_data["move_count"] = move_count
        logger.debug(f"Loaded board state for user {user_id} in start_ai_vs_ai: {user_data}")
    else:
        user_data["board"] = create_board()
        user_data["move_count"] = 0
    user_data.update({
        "game_active": True,
        "last_board_state": None,
        "last_message_text": None,
        "difficulty": difficulty
    })
    save_user_settings(user_id, difficulty)
    board = user_data["board"]
    message = update.message
    game_message = await message.reply_text(
        text=get_text(context, "game_start", player="AI1 (X)", opponent="AI2 (O)") + f"\nFirst move: X\n{format_board(board)}",
        reply_markup=create_keyboard(board, interactive=False)
    )
    save_board_state(user_id, board, user_data["move_count"])
    await asyncio.sleep(1.5)

    move_count = 0
    max_moves = 9
    start_time = time.time()
    max_duration = 60
    while user_data.get("game_active") and move_count < max_moves and time.time() - start_time <= max_duration:
        for player in ["X", "O"]:
            if not user_data.get("game_active"):
                break
            move_count += 1
            user_data["move_count"] = move_count
            board_copy = deepcopy(board)
            await asyncio.sleep(settings["ai_delay"])
            try:
                move = ai_move(board_copy, player, user_data["difficulty"])
            except Exception as e:
                logger.error(f"Error in ai_move for player {player}, board: {board_copy}: {e}")
                move = None
            if move is None or move < 0 or move >= 9 or board_copy[move] != " ":
                logger.error(f"Invalid move {move} by {player}, board: {board_copy}")
                save_board_state(user_id, board, move_count)
                await send_error_message(message, context)
                user_data["game_active"] = False
                clear_board_state(user_id)
                return

            board[move] = player
            log_move(board, move, player)
            update_memory(board[:], move, player, "win" if check_winner(board, player) else "pending")
            save_board_state(user_id, board, user_data["move_count"])
            game_message = await try_update_message(
                game_message,
                f"AI {player} moves to {move + 1}\n\n{format_board(board)}",
                create_keyboard(board, interactive=False),
                context
            )
            if not game_message:
                game_message = await message.reply_text(
                    text=f"AI {player} moves to {move + 1}\n\n{format_board(board)}",
                    reply_markup=create_keyboard(board, interactive=False)
                )
            await asyncio.sleep(1.5)

            if check_winner(board, player) or is_board_full(board):
                result_text = get_text(context, "player_wins", player=f"AI {player}") if check_winner(board, player) else get_text(context, "draw")
                game_message = await try_update_message(
                    game_message,
                    f"{result_text}\n\n{format_board(board)}\n\n{get_text(context, 'game_over_returning')}",
                    create_keyboard(board, interactive=False),
                    context
                )
                await asyncio.sleep(2.0)
                await message.reply_text(
                    text=get_text(context, "main_menu"),
                    reply_markup=create_main_menu_keyboard(context)
                )
                update_stats("AI" if check_winner(board, player) else None)
                user_data["game_active"] = False
                clear_board_state(user_id)
                return

            if move_count >= max_moves or time.time() - start_time > max_duration:
                result_text = get_text(context, "draw")
                game_message = await try_update_message(
                    game_message,
                    f"{result_text}\n\n{format_board(board)}\n\n{get_text(context, 'game_over_returning')}",
                    create_keyboard(board, interactive=False),
                    context
                )
                await asyncio.sleep(2.0)
                await message.reply_text(
                    text=get_text(context, "main_menu"),
                    reply_markup=create_main_menu_keyboard(context)
                )
                update_stats(None)
                user_data["game_active"] = False
                clear_board_state(user_id)
                return

def set_player_symbol(symbol: str) -> tuple[str, str] | None:
    symbol = symbol.upper()
    if symbol not in ["X", "O"]:
        print(f"Ошибка: Недопустимый символ: {symbol}. Используйте X или O.")
        return None
    human_symbol = symbol
    ai_symbol = "O" if symbol == "X" else "X"
    print(f"Символ игрока установлен: {human_symbol}, символ ИИ: {ai_symbol}")
    return human_symbol, ai_symbol

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    user_data = context.user_data
    message = update.message
    user_id = message.chat.id
    logger.debug(f"Received message: '{text}' from user {user_id}, user_data: {user_data}")

    if text.startswith('/'):
        logger.debug(f"Skipping command: {text}")
        return

    if user_data.get("awaiting_language"):
        lang_map = {
            "русский (ru)": "ru",
            "english (en)": "en",
            "日本語 (ja)": "ja",
            "italiano (it)": "it",
            "हिन्दी (hi)": "hi"
        }
        if text in lang_map:
            user_data["language"] = lang_map[text]
            user_data["awaiting_language"] = False
            logger.debug(f"Language set to {user_data['language']} for user {user_id}")
            await message.reply_text(
                text=get_text(context, "language_set", language=user_data["language"]),
                reply_markup=create_main_menu_keyboard(context)
            )
            await asyncio.sleep(1.5)
        else:
            logger.debug(f"Invalid language input: {text}")
            await message.reply_text(
                text=get_text(context, "language_prompt"),
                reply_markup=create_language_keyboard()
            )
            await asyncio.sleep(1.5)
        return

    symbol_map = {
        "x": "X",
        "o": "O",
        "х": "X",
        "о": "O",
        "0": "O",
        "エックス": "X",
        "オー": "O",
        "एक्स": "X",
        "ओ": "O"
    }

    mode_map = {
        get_text(context, "play_button").lower(): "play_button",
        get_text(context, "classic_mode").lower(): "classic_mode",
        get_text(context, "player_vs_ai").lower(): "player_vs_ai",
        get_text(context, "ai_vs_player").lower(): "ai_vs_player",
        get_text(context, "ai_vs_ai").lower(): "ai_vs_ai",
        get_text(context, "tic_tac_toe_web3").lower(): "web3_mode",
        get_text(context, "profile_button").lower(): "profile_button",
        get_text(context, "info_button").lower(): "info_button",
        get_text(context, "yes_button").lower(): "yes_button",
        get_text(context, "no_button").lower(): "no_button"
    }

    if text in mode_map:
        selected_mode = mode_map[text]
        logger.debug(f"Processing button: {selected_mode}")

        if selected_mode == "play_button":
            user_data["awaiting_mode"] = True
            await message.reply_text(
                text=get_text(context, "game_mode_prompt"),
                reply_markup=create_game_mode_keyboard(context)
            )
            await asyncio.sleep(1.5)
            return

        if user_data.get("awaiting_mode"):
            if selected_mode == "classic_mode":
                user_data["awaiting_mode"] = False
                user_data["game_mode"] = "classic_mode"
                user_data["awaiting_difficulty"] = True
                await message.reply_text(
                    text=get_text(context, "difficulty_prompt"),
                    reply_markup=create_difficulty_keyboard(context)
                )
                await asyncio.sleep(1.5)
            elif selected_mode == "player_vs_ai":
                user_data["awaiting_mode"] = False
                user_data["awaiting_difficulty"] = True
                user_data["game_mode"] = "player_vs_ai"
                await message.reply_text(
                    text=get_text(context, "difficulty_prompt"),
                    reply_markup=create_difficulty_keyboard(context)
                )
                await asyncio.sleep(1.5)
            elif selected_mode == "ai_vs_player":
                user_data["awaiting_mode"] = False
                user_data["awaiting_difficulty"] = True
                user_data["game_mode"] = "ai_vs_player"
                await message.reply_text(
                    text=get_text(context, "difficulty_prompt"),
                    reply_markup=create_difficulty_keyboard(context)
                )
                await asyncio.sleep(1.5)
            elif selected_mode == "ai_vs_ai":
                user_data["awaiting_mode"] = False
                user_data["awaiting_difficulty"] = True
                user_data["game_mode"] = "ai_vs_ai"
                await message.reply_text(
                    text=get_text(context, "difficulty_prompt"),
                    reply_markup=create_difficulty_keyboard(context)
                )
                await asyncio.sleep(1.5)
            return

        elif selected_mode == "web3_mode":
            user_data["awaiting_mode"] = False
            try:
                keyboard = [InlineKeyboardButton("Play Tic Tac Toe Web3", url=f"https://yourgame.com?user_id={user_id}")]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.reply_text(
                    text="Click below to play the Tic Tac Toe Web3 game:",
                    reply_markup=reply_markup
                )
                await asyncio.sleep(1.5)
            except Exception as e:
                logger.error(f"Failed to send Web3 inline button: {e}")
                await message.reply_text(
                    text="Error loading Web3 game.",
                    reply_markup=create_main_menu_keyboard(context)
                )
                await asyncio.sleep(1.5)
            return

        elif user_data.get("awaiting_difficulty"):
            if text in ["easy", "medium", "hard"]:
                user_data["difficulty"] = text
                save_user_settings(user_id, text)
                user_data["awaiting_difficulty"] = False
                user_data["awaiting_symbol"] = True  # Теперь ожидаем выбор символа
                logger.debug(f"Difficulty set to {text} for user {user_id}, awaiting symbol")

                # Создаем новую доску перед началом игры
                user_data["board"] = create_board()
                user_data["move_count"] = 0

                await message.reply_text(
                    text=get_text(context, "choose_symbol"),
                    reply_markup=create_symbol_keyboard(context)
                )
                await asyncio.sleep(1.5)
            else:
                logger.debug(f"Invalid difficulty input: {text} for user {user_id}")
                await message.reply_text(
                    text=get_text(context, "invalid_difficulty"),
                    reply_markup=create_difficulty_keyboard(context)
                )
                await asyncio.sleep(1.5)
            return


        elif user_data.get("awaiting_symbol"):
            if text in symbol_map:
                selected_symbol = symbol_map[text]
                game_mode = user_data.get("game_mode")
                logger.debug(f"Symbol {selected_symbol} selected for user {user_id}, game_mode: {game_mode}")
                user_data["awaiting_symbol"] = False
                if game_mode == "player_vs_ai":
                    user_data["human_player"] = selected_symbol
                    user_data["ai_player"] = "O" if selected_symbol == "X" else "X"
                    await start_player_vs_ai(update, context, player_first=True)
                elif game_mode == "ai_vs_player":
                    user_data["human_player"] = selected_symbol
                    user_data["ai_player"] = "O" if selected_symbol == "X" else "X"
                    await start_player_vs_ai(update, context, player_first=False)
                elif game_mode == "ai_vs_ai":
                    user_data["ai1_symbol"] = selected_symbol
                    user_data["ai2_symbol"] = "O" if selected_symbol == "X" else "X"
                    await start_ai_vs_ai(update, context, difficulty=user_data["difficulty"])
                elif game_mode == "classic_mode":
                    user_data["player1_symbol"] = selected_symbol
                    user_data["player2_symbol"] = "O" if selected_symbol == "X" else "X"
                    await start_classic_game(update, context)
            else:
                logger.debug(f"Invalid symbol input: {text} for user {user_id}")
                await message.reply_text(
                    text=get_text(context, "invalid_symbol"),
                    reply_markup=create_symbol_keyboard(context)
                )
                await asyncio.sleep(1.5)
            return

        elif selected_mode in ["profile_button", "info_button"]:
            await message.reply_text(
                text=get_text(context, "feature_coming_soon"),
                reply_markup=create_main_menu_keyboard(context)
            )
            await asyncio.sleep(1.5)
            return

        elif selected_mode == "yes_button" and user_data.get("awaiting_play_again"):
            user_data["awaiting_play_again"] = False
            if user_data.get("last_mode") == "ai_vs_ai":
                await start_ai_vs_ai(update, context, difficulty=user_data.get("difficulty", settings["difficulty"]))
            elif user_data.get("last_mode") in ["player_vs_ai", "ai_vs_player"]:
                await start_player_vs_ai(update, context, player_first=user_data.get("last_mode") == "player_vs_ai")
            elif user_data.get("last_mode") == "classic_mode":
                await start_classic_game(update, context)
            await asyncio.sleep(1.5)
            return

        elif selected_mode == "no_button" and user_data.get("awaiting_play_again"):
            user_data["awaiting_play_again"] = False
            await message.reply_text(
                text=get_text(context, "game_exit"),
                reply_markup=create_main_menu_keyboard(context)
            )
            await asyncio.sleep(1.5)
            return

    if user_data.get("game_active"):
        board = user_data.get("board")
        game_mode = user_data.get("game_mode")
        if game_mode == "classic_mode":
            try:
                move = int(text) - 1
                user_data["invalid_input_count"] = user_data.get("invalid_input_count", 0)
                current_player = user_data["player1_symbol"] if user_data["move_count"] % 2 == 0 else user_data["player2_symbol"]
                if 0 <= move < 9 and board[move] == " ":
                    board[move] = current_player
                    log_move(board, move, current_player)
                    user_data["move_count"] += 1
                    save_board_state(user_id, board, user_data["move_count"])

                    next_player = user_data["player2_symbol"] if current_player == user_data["player1_symbol"] else user_data["player1_symbol"]
                    game_message = await message.reply_text(
                        text=f"{get_text(context, 'your_turn')} ({next_player})\n\n{format_board(board)}",
                        reply_markup=create_keyboard(board, interactive=True)
                    )

                    if check_winner(board, current_player) or is_board_full(board):
                        result_text = get_text(context, "player_wins", player=f"Player {'1' if current_player == user_data['player1_symbol'] else '2'} ({current_player})") if check_winner(board, current_player) else get_text(context, "draw")
                        await try_update_message(
                            game_message,
                            f"{result_text}\n\n{format_board(board)}\n\n{get_text(context, 'play_again')}",
                            ReplyKeyboardMarkup([[get_text(context, "yes_button"), get_text(context, "no_button")]], resize_keyboard=True),
                            context
                        )
                        user_data["awaiting_play_again"] = True
                        user_data["last_mode"] = "classic_mode"
                        user_data["game_active"] = False
                        clear_board_state(user_id)
                        return
                else:
                    user_data["invalid_input_count"] += 1
                    if user_data["invalid_input_count"] >= 5:
                        await send_error_message(message, context)
                        user_data["game_active"] = False
                        clear_board_state(user_id)
                        return
                    else:
                        await message.reply_text(
                            text=get_text(context, "invalid_move"),
                            reply_markup=create_keyboard(board, interactive=True)
                        )
                        await asyncio.sleep(1.5)
            except ValueError:
                user_data["invalid_input_count"] = user_data.get("invalid_input_count", 0) + 1
                if user_data["invalid_input_count"] >= 5:
                    await send_error_message(message, context)
                    user_data["game_active"] = False
                    clear_board_state(user_id)
                    return
                else:
                    await message.reply_text(
                        text=get_text(context, "invalid_move"),
                        reply_markup=create_keyboard(board, interactive=True)
                    )
                    await asyncio.sleep(1.5)
        else:
            if game_mode == "ai_vs_ai":
                await message.reply_text(
                    text=get_text(context, "invalid_move"),
                    reply_markup=create_main_menu_keyboard(context)
                )
                await asyncio.sleep(1.5)
                return
            try:
                move = int(text) - 1
                user_data["invalid_input_count"] = 0
                if 0 <= move < 9 and board[move] == " ":
                    human_player = user_data["human_player"]
                    board[move] = human_player
                    log_move(board, move, human_player)
                    update_memory(board[:], move, human_player, "win" if check_winner(board, human_player) else "pending")
                    user_data["move_count"] += 1
                    logger.debug(f"Move {user_data['move_count']}: Human move: {move}, Board: {board}")
                    save_board_state(user_id, board, user_data["move_count"])

                    if check_winner(board, human_player) or is_board_full(board):
                        result_text = get_text(context, "player_wins", player=human_player) if check_winner(board, human_player) else get_text(context, "draw")
                        game_message = await message.reply_text(
                            text=f"{result_text}\n\n{format_board(board)}\n\n{get_text(context, 'play_again')}",
                            reply_markup=ReplyKeyboardMarkup([[get_text(context, "yes_button"), get_text(context, "no_button")]], resize_keyboard=True)
                        )
                        user_data["awaiting_play_again"] = True
                        user_data["last_mode"] = game_mode
                        update_stats("Human" if check_winner(board, human_player) else None)
                        user_data["game_active"] = False
                        clear_board_state(user_id)
                        return

                    game_message = await message.reply_text(
                        text=get_text(context, "ai_thinking"),
                        reply_markup=create_keyboard(board, interactive=True)
                    )
                    await asyncio.sleep(settings["ai_delay"])

                    ai_player = user_data["ai_player"]
                    ai_move_idx = ai_move(board, ai_player, user_data.get("difficulty", settings["difficulty"]))
                    if ai_move_idx is None or ai_move_idx < 0 or ai_move_idx >= 9 or board[ai_move_idx] != " ":
                        logger.error(f"AI invalid move: {ai_move_idx}, board: {board}")
                        await send_error_message(message, context)
                        user_data["game_active"] = False
                        clear_board_state(user_id)
                        return

                    board[ai_move_idx] = ai_player
                    log_move(board, ai_move_idx, ai_player)
                    update_memory(board[:], ai_move_idx, ai_player, "win" if check_winner(board, ai_player) else "pending")
                    user_data["move_count"] += 1
                    logger.debug(f"Move {user_data['move_count']}: AI move: {ai_move_idx}, Board: {board}")
                    save_board_state(user_id, board, user_data["move_count"])

                    if check_winner(board, ai_player) or is_board_full(board):
                        result_text = get_text(context, "player_wins", player=ai_player) if check_winner(board, ai_player) else get_text(context, "draw")
                        await try_update_message(
                            game_message,
                            f"{result_text}\n\n{format_board(board)}\n\n{get_text(context, 'play_again')}",
                            ReplyKeyboardMarkup([[get_text(context, "yes_button"), get_text(context, "no_button")]], resize_keyboard=True),
                            context
                        )
                        user_data["awaiting_play_again"] = True
                        user_data["last_mode"] = game_mode
                        update_stats("AI" if check_winner(board, ai_player) else None)
                        user_data["game_active"] = False
                        clear_board_state(user_id)
                        return

                    await try_update_message(
                        game_message,
                        get_text(context, "your_turn") + f"\n\n{format_board(board)}",
                        create_keyboard(board, interactive=True),
                        context
                    )
                    await asyncio.sleep(1.5)
                else:
                    user_data["invalid_input_count"] = user_data.get("invalid_input_count", 0) + 1
                    if user_data["invalid_input_count"] >= 5:
                        await send_error_message(message, context)
                        user_data["game_active"] = False
                        clear_board_state(user_id)
                        return
                    else:
                        await message.reply_text(
                            text=get_text(context, "invalid_move"),
                            reply_markup=create_keyboard(board, interactive=True)
                        )
                        await asyncio.sleep(1.5)
            except ValueError:
                user_data["invalid_input_count"] = user_data.get("invalid_input_count", 0) + 1
                if user_data["invalid_input_count"] >= 5:
                    await send_error_message(message, context)
                    user_data["game_active"] = False
                    clear_board_state(user_id)
                    return
                else:
                    await message.reply_text(
                        text=get_text(context, "invalid_move"),
                        reply_markup=create_keyboard(board, interactive=True)
                    )
                    await asyncio.sleep(1.5)
        return

    # Проверяем, чтобы не возвращаться в главное меню, если ожидается другой ввод
    if user_data.get("awaiting_symbol"):
        logger.debug(f"User {user_id} is still awaiting symbol, keeping symbol keyboard")
        await message.reply_text(
            text=get_text(context, "invalid_symbol"),
            reply_markup=create_symbol_keyboard(context)
        )
        await asyncio.sleep(1.5)
        return

    logger.debug(f"Unknown message: {text}, sending main menu")
    await message.reply_text(
        text=get_text(context, "main_menu"),
        reply_markup=create_main_menu_keyboard(context)
    )
    await asyncio.sleep(1.5)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}")
def create_symbol_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    keyboard = [["X", "O"]]
    logger.debug("Created symbol keyboard: [['X', 'O']]")
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main():
    lock = acquire_lock()
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("difficulty", set_difficulty))
        app.add_handler(CommandHandler("language", set_language))
        app.add_handler(CommandHandler("settings", settings_command))
        app.add_handler(MessageHandler(filters.ALL, handle_message))
        app.add_error_handler(error_handler)
        logger.info("Bot initialized, starting polling")
        app.run_polling()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        lock.release()
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")

if __name__ == "__main__":
    main()