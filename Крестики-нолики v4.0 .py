import os
import json
import random
import sqlite3
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
    except Exception:
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
    "ai_delay": 7,
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
        "invalid_move": "Неверный ход!.",
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
        "error_message": "Ошибка! Доска не обновлена. Перезапустите игру (/restart).",
        "invalid_symbol": "Неверный символ. Используйте: X или O",
        "return_to_menu": "Вернуться в меню",
        "main_menu": "Главное меню",
        "play_again_or_menu": "Хотите сыграть еще раз или вернуться в меню?",
        "play_button": "Играть",
        "profile_button": "Профиль",
        "info_button": "Инфо",
        "feature_coming_soon": "Функция скоро появится",
        "game_over_returning": "Игра окончена. Возвращаемся в меню.",
        "symbol_assigned": "Вам назначен символ: {symbol}",
        "game_restarted": "Игра перезапущена! Выберите язык:",
        "human_move": "Ваш ход",
        "your_turn": "Ваш ход",
    },
    "en": {
        "welcome_message": "Welcome to Tic-Tac-Toe! 🎮\nChoose a language:",
        "game_start": "Game starts! You are {player}, AI is {opponent}. Your turn!",
        "invalid_move": "Invalid move!.",
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
        "error_message": "Error! Board not showing? Restart the game (/restart).",
        "invalid_symbol": "Invalid symbol! Use: X или O",
        "return_to_menu": "Return to menu",
        "main_menu": "Main Menu",
        "play_again_or_menu": "Do you want to play again or return to menu?",
        "play_button": "Play",
        "profile_button": "Profile",
        "info_button": "Info",
        "feature_coming_soon": "Feature coming soon",
        "game_over_returning": "Game over. Returning to menu.",
        "symbol_assigned": "You have been assigned symbol: {symbol}",
        "game_restarted": "Game restarted! Choose a language:",
        "human_move": "Your move",
        "your_turn": "Your turn",
    },
    "ja": {
        "welcome_message": "チックタックトーへようこそ！🎮\n言語を選択してください：",
        "game_start": "ゲームが始まります！あなたは{player}、AIは{opponent}です。あなたのターン！",
        "invalid_move": "無効な手です！。",
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
        "error_message": "エラー！ボードが更新されていません。ゲームを再起動してください（/restart）。",
        "invalid_symbol": "無効なシンボルです。XまたはOを使用してください",
        "return_to_menu": "メニューに戻る",
        "main_menu": "メインメニュー",
        "play_again_or_menu": "もう一度プレイしますか、それともメニューに戻りますか？",
        "play_button": "プレイ",
        "profile_button": "プロフィール",
        "info_button": "情報",
        "feature_coming_soon": "機能は近日公開予定です",
        "game_over_returning": "ゲーム終了。メニューに戻ります。",
        "symbol_assigned": "あなたに割り当てられたシンボル：{symbol}",
        "game_restarted": "ゲームが再起動されました！言語を選択してください：",
        "human_move": "あなたの動き",
        "your_turn": "あなたのターン",
    },
    "it": {
        "welcome_message": "Benvenuto a Tris! 🎮\nScegli una lingua:",
        "game_start": "La partita inizia! Sei {player}, l'IA è {opponent}. Tocca a te!",
        "invalid_move": "Mossa non valida!.",
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
        "error_message": "Errore! La scacchiera non si aggiorna? Riavvia il gioco (/restart).",
        "invalid_symbol": "Simbolo non valido. Usa: X o O",
        "return_to_menu": "Torna al menu",
        "main_menu": "Menu Principale",
        "play_again_or_menu": "Vuoi giocare di nuovo o tornare al menu?",
        "play_button": "Gioca",
        "profile_button": "Profilo",
        "info_button": "Info",
        "feature_coming_soon": "Funzionalità in arrivo",
        "game_over_returning": "Partita finita. Torniamo al menu.",
        "symbol_assigned": "Ti è stato assegnato il simbolo: {symbol}",
        "game_restarted": "Partita riavviata! Scegli una lingua:",
        "human_move": "La tua mossa",
        "your_turn": "Tocca a te",
    },
    "hi": {
        "welcome_message": "टिक-टैक-टो में आपका स्वागत है! 🎮\nएक भाषा चुनें:",
        "game_start": "खेल शुरू होता है! आप {player} हैं, AI {opponent} है। आपकी बारी!",
        "invalid_move": "अमान्य चाल!",
        "player_wins": "{player} जीता! 🏆",
        "draw": "ड्रॉ! 🤝",
        "play_again": "फिर से खेलें?",
        "yes_button": "हाँ",
        "no_button": "नहीं",
        "game_exit": "खेल समाप्त! फिर मिलेंगे! 👋",
        "difficulty_prompt": "कठिनाई चुनें",
        "invalid_difficulty": "अमान्य कठिनाई! उपयोग करें: easy, medium, hard",
        "difficulty_set": "कठिनाई सेट: {difficulty}",
        "language_prompt": "एक भाषа चुनें:",
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
        "error_message": "त्रुटि! बोर्ड नहीं दिख रहा है? खेल को पुनः आरंभ करें (/restart)।",
        "invalid_symbol": "अमान्य प्रतीк! उपयोग करें: X या O",
        "return_to_menu": "मेनू पर लौटें",
        "main_menu": "मुख्य मेनू",
        "play_again_or_menu": "क्या आप फिर से खेलना चाहते हैं या मेनू पर लौटना चाहते हैं?",
        "play_button": "खेलें",
        "profile_button": "प्रोफ़ाइल",
        "info_button": "जानकारी",
        "feature_coming_soon": "फ़ीचर जल्द ही आ रहा है",
        "game_over_returning": "खेल समाप्त। मेनू पर लौट रहे हैं।",
        "symbol_assigned": "आपको प्रतीक सौंपा गया है: {symbol}",
        "game_restarted": "खेल पुनः शुरू हुआ! एक भाषा चुनें:",
        "human_move": "अपनी चाल",
        "your_turn": "आपकी बारी",
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

def save_user_settings(user_id: int, difficulty: str):
    logger.debug(f"Saving settings for user {user_id}: difficulty={difficulty}")
    try:
        with open(f"settings_{user_id}.json", "w") as f:
            json.dump({"difficulty": difficulty}, f)
    except Exception as e:
        logger.error(f"Failed to save settings for user {user_id}: {e}")

def save_board_state(user_id, board, move_count, context):
    logger.debug(f"Saving board state for user {user_id}: board={board}, move_count={move_count}")
    try:
        conn = sqlite3.connect("game.db", timeout=5.0)  # Добавлен тайм-аут
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO game_state 
            (user_id, board, move_count, game_mode, difficulty, human_player, ai_player, ai1_symbol, ai2_symbol, player1_symbol, player2_symbol)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            json.dumps(board),
            move_count,
            context.user_data.get("game_mode"),
            context.user_data.get("difficulty"),
            context.user_data.get("human_player"),
            context.user_data.get("ai_player"),
            context.user_data.get("ai1_symbol"),
            context.user_data.get("ai2_symbol"),
            context.user_data.get("player1_symbol"),
            context.user_data.get("player2_symbol")
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save board state for user {user_id}: {e}")
        raise  # Поднимаем исключение для отслеживания
    finally:
        conn.close()

def load_board_state(user_id: int) -> tuple | None:
    try:
        conn = sqlite3.connect("game.db")
        cursor = conn.cursor()
        cursor.execute("SELECT board, move_count FROM game_state WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            board = json.loads(result[0])
            move_count = result[1]
            if (isinstance(board, list) and len(board) == 9 and
                all(c in [" ", "X", "O"] for c in board)):
                logger.debug(f"Loaded board state for user {user_id}: {board}, move_count: {move_count}")
                return board, move_count
        return None
    except Exception as e:
        logger.error(f"Failed to load board state for user {user_id}: {e}")
        return None

def clear_board_state(user_id):
    logger.debug(f"Clearing board state for user {user_id}")
    try:
        conn = sqlite3.connect("game.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM game_state WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
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
    # Заменяем пустые клетки номерами, если interactive=True
    buttons = [
        board[i] if board[i] in ["X", "O"] else str(i+1) if interactive else " "
        for i in range(9)
    ]
    
    # Разбиваем на строки по 3 кнопки
    keyboard = [
        [buttons[0], buttons[1], buttons[2]],
        [buttons[3], buttons[4], buttons[5]],
        [buttons[6], buttons[7], buttons[8]]
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

def create_difficulty_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    # Используем переведённые строки из словаря translations
    lang = context.user_data.get("language", settings["language"])
    difficulty_translations = {
        "ru": {"easy": "Легко", "medium": "Средне", "hard": "Сложно"},
        "en": {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
        "ja": {"easy": "簡単", "medium": "中級", "hard": "難しい"},
        "it": {"easy": "Facile", "medium": "Medio", "hard": "Difficile"},
        "hi": {"easy": "आसान", "medium": "मध्यम", "hard": "कठिन"}
    }
    keyboard = [
        [difficulty_translations[lang].get("easy", "Easy")],
        [difficulty_translations[lang].get("medium", "Medium")],
        [difficulty_translations[lang].get("hard", "Hard")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

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

def log_move(board, move_idx, player):
    logger.debug(f"Move logged: player={player}, move_idx={move_idx}, board={board}")

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

def ai_move(board, player, difficulty):
    logger.debug(f"AI move called with board: {board}, player: {player}, difficulty: {difficulty}")
    available_moves = [i for i in range(9) if board[i] == " "]
    if not available_moves:
        logger.error(f"No available moves on board: {board}")
        return None
    if difficulty == "hard":
        if 4 in available_moves:
            return 4
        opponent = "O" if player == "X" else "X"
        best_score = -float("inf")
        best_move = None
        for move in available_moves:
            board[move] = player
            score = minimax(board, 0, False, player, opponent)
            board[move] = " "
            if score > best_score:
                best_score = score
                best_move = move
        return best_move or random.choice(available_moves)
    elif difficulty == "medium":
        corners = [0, 2, 6, 8]
        available_corners = [i for i in corners if i in available_moves]
        if available_corners:
            return random.choice(available_corners)
    return random.choice(available_moves)

def update_memory(board: list, move: int, player: str, outcome: str):
    board_key = str(tuple(board))
    memory = ai_memory if player == "O" else human_memory
    if len(memory) > 1000:
        oldest_key = next(iter(memory))
        memory.pop(oldest_key)
        logger.debug(f"Memory limit reached, removed oldest key: {oldest_key}")
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
async def try_update_message(message, text: str, reply_markup, context):
    board_state = str(reply_markup.keyboard) if hasattr(reply_markup, 'keyboard') else str(reply_markup)
    if context.user_data.get("last_message_text") == text and context.user_data.get("last_board_state") == board_state:
        logger.debug("Skipped duplicate message update")
        return message

    logger.debug(f"Sending new message with text: {text}, board_state: {board_state}")
    try:
        new_message = await message.chat.send_message(text=text, reply_markup=reply_markup)
        context.user_data["last_message_text"] = text
        context.user_data["last_board_state"] = board_state
        logger.debug(f"New message sent successfully for user {message.chat_id}")
        return new_message
    except Exception as e:
        logger.error(f"Failed to send new message for user {message.chat_id}: {e}")
        await message.chat.send_message(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )
        context.user_data["game_active"] = False
        clear_board_state(message.chat_id)
        return None

async def start_game_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    user_data = context.user_data
    user_id = update.message.chat.id
    logger.debug(f"Starting game mode {mode} for player {user_id}, user_data: {user_data}")
    
    try:
        user_data["game_mode"] = mode
        user_data["awaiting"] = "difficulty"
        try:
            await update.message.reply_text(
                text=get_text(context, "difficulty_prompt"),
                reply_markup=create_difficulty_keyboard(context)
            )
        except Exception as e:
            logger.error(f"Failed to send difficulty prompt for user {user_id}: {e}")
            user_data.clear()
            await update.message.reply_text(
                text=get_text(context, "error_message"),
                reply_markup=create_main_menu_keyboard(context)
            )
    except Exception as e:
        logger.error(f"Error in start_game_mode for user {user_id}: {e}")
        user_data.clear()
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )

async def start_ai_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, difficulty: str):
    user_data = context.user_data
    user_id = update.message.chat.id
    logger.debug(f"Starting ai_vs_ai for user {user_id}, difficulty: {difficulty}, user_data: {user_data}")
    
    if not user_data.get("game_active") or not user_data.get("board") or not user_data.get("ai1_symbol") or not user_data.get("ai2_symbol"):
        logger.error(f"Invalid state: game_active={user_data.get('game_active')}, board={user_data.get('board')}, ai1={user_data.get('ai1_symbol')}, ai2={user_data.get('ai2_symbol')}")
        user_data["game_active"] = False
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )
        clear_board_state(user_id)
        return

    try:
        board = user_data["board"]
        ai1_symbol = user_data["ai1_symbol"]
        ai2_symbol = user_data["ai2_symbol"]
        move_count = user_data["move_count"]
        game_message = await update.message.reply_text(
            text=f"AI ({ai1_symbol}) thinking...\n\n{format_board(board)}",
            reply_markup=create_keyboard(board, False)
        )

        while not check_winner(board, ai1_symbol) and not check_winner(board, ai2_symbol) and not is_board_full(board):
            await asyncio.sleep(2)  # Уменьшено с 7 до 2 секунд
            ai_move_idx = ai_move(board, ai1_symbol, difficulty)
            if ai_move_idx is None or ai_move_idx < 0 or ai_move_idx >= 9 or board[ai_move_idx] != " ":
                logger.error(f"Invalid AI1 move: {ai_move_idx}, board: {board}")
                user_data["game_active"] = False
                await game_message.reply_text(
                    text=get_text(context, "error_message"),
                    reply_markup=create_main_menu_keyboard(context)
                )
                clear_board_state(user_id)
                return
            
            board[ai_move_idx] = ai1_symbol
            log_move(board, ai_move_idx, ai1_symbol)
            move_count += 1
            user_data["move_count"] = move_count
            save_board_state(user_id, board, move_count, context)
            
            if check_winner(board, ai1_symbol) or is_board_full(board):
                break
            
            game_message = await game_message.reply_text(  # Новое сообщение
                text=f"AI ({ai2_symbol}) thinking...\n\n{format_board(board)}",
                reply_markup=create_keyboard(board, False)
            )
            
            await asyncio.sleep(2)  # Уменьшено с 7 до 2 секунд
            ai_move_idx = ai_move(board, ai2_symbol, difficulty)
            if ai_move_idx is None or ai_move_idx < 0 or ai_move_idx >= 9 or board[ai_move_idx] != " ":
                logger.error(f"Invalid AI2 move: {ai_move_idx}, board: {board}")
                user_data["game_active"] = False
                await game_message.reply_text(
                    text=get_text(context, "error_message"),
                    reply_markup=create_main_menu_keyboard(context)
                )
                clear_board_state(user_id)
                return
            
            board[ai_move_idx] = ai2_symbol
            log_move(board, ai_move_idx, ai2_symbol)
            move_count += 1
            user_data["move_count"] = move_count
            save_board_state(user_id, board, move_count, context)
            
        result_text = (
            get_text(context, "player_wins", player=ai1_symbol) if check_winner(board, ai1_symbol)
            else get_text(context, "player_wins", player=ai2_symbol) if check_winner(board, ai2_symbol)
            else get_text(context, "draw")
        )
        game_message = await game_message.reply_text(  # Новое сообщение
            text=f"{result_text}\n\n{format_board(board)}\n\n{get_text(context, 'play_again')}",
            reply_markup=ReplyKeyboardMarkup([[get_text(context, "yes_button"), get_text(context, "no_button")]], resize_keyboard=True)
        )
        user_data["awaiting_play_again"] = True
        user_data["last_mode"] = "ai_vs_ai"
        user_data["game_active"] = False
        clear_board_state(user_id)
    except Exception as e:
        logger.error(f"Error in start_ai_vs_ai for user {user_id}: {e}")
        user_data["game_active"] = False
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )
        clear_board_state(user_id)

async def start_player_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, player_first: bool):
    user_data = context.user_data
    user_id = update.message.chat.id
    logger.debug(f"Starting player_vs_ai for user {user_id}, player_first: {player_first}")

    # Проверка всех ключей
    if not all(key in user_data for key in ["game_active", "board", "human_player", "ai_player", "move_count"]):
        logger.error(f"Invalid state for user {user_id}: {user_data}")
        user_data["game_active"] = False
        clear_board_state(user_id)
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )
        return

    try:
        board = user_data["board"]
        human_player = user_data["human_player"]
        ai_player = user_data["ai_player"]

        initial_text = f"{get_text(context, 'your_turn')} ({human_player})\n\n{format_board(board)}" if player_first else get_text(context, "ai_thinking")
        board_message = await update.message.reply_text(
            text=initial_text,
            reply_markup=create_keyboard(board, interactive=player_first)
        )
        user_data["board_message_id"] = board_message.message_id

        if not player_first:
            await asyncio.sleep(1)
            ai_move_idx = ai_move(board, ai_player, user_data.get("difficulty", settings["difficulty"]))
            if ai_move_idx is None or ai_move_idx < 0 or ai_move_idx >= 9 or board[ai_move_idx] != " ":
                logger.error(f"Invalid AI move: {ai_move_idx}, board: {board}")
                user_data["game_active"] = False
                await update.message.reply_text(
                    text=get_text(context, "error_message"),
                    reply_markup=create_main_menu_keyboard(context)
                )
                clear_board_state(user_id)
                return
            board[ai_move_idx] = ai_player
            log_move(board, ai_move_idx, ai_player)
            user_data["move_count"] += 1
            save_board_state(user_id, board, user_data["move_count"], context)
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=user_data["board_message_id"],
                text=f"{get_text(context, 'your_turn')} ({human_player})\n\n{format_board(board)}",
                reply_markup=create_keyboard(board, interactive=True)
            )
    except Exception as e:
        logger.error(f"Error in start_player_vs_ai for user {user_id}: {e}")
        user_data["game_active"] = False
        clear_board_state(user_id)
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )

async def start_classic_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.message.chat.id
    logger.debug(f"Starting classic_game for user {user_id}")

    # Проверка всех ключей
    if not all(key in user_data for key in ["game_active", "board", "player1_symbol", "player2_symbol", "move_count"]):
        logger.error(f"Invalid state for user {user_id}: {user_data}")
        user_data["game_active"] = False
        clear_board_state(user_id)
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )
        return

    try:
        user_data["hints_enabled"] = user_data.get("difficulty") == "medium"
        current_player = user_data["player1_symbol"] if user_data["move_count"] % 2 == 0 else user_data["player2_symbol"]
        hint_text = ""
        if user_data["hints_enabled"]:
            hint_move = ai_move(user_data["board"], current_player, "medium")
            if hint_move is not None:
                hint_text = f"\n{get_text(context, 'hint_text', hint=hint_move + 1)}"
        board_message = await update.message.reply_text(
            text=f"{get_text(context, 'your_turn')} ({current_player})\n\n{format_board(user_data['board'])}{hint_text}",
            reply_markup=create_keyboard(user_data["board"], True)
        )
        user_data["board_message_id"] = board_message.message_id
    except Exception as e:
        logger.error(f"Error in start_classic_game for user {user_id}: {e}")
        user_data["game_active"] = False
        clear_board_state(user_id)
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )

async def send_error_message(message, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Sending error message to user {message.chat.id}")
    try:
        await message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )
    except Exception as e:
        logger.error(f"Failed to send error message to user {message.chat.id}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    user_data = context.user_data
    message = update.message
    user_id = message.chat.id
    logger.debug(f"Got message: '{text}' from user {user_id}, data: {user_data}")
    board = user_data.get("board")
    if board is None:
        board = create_board()
        user_data["board"] = board
    
    game_mode = user_data.get("game_mode")

    if text.startswith('/'):
        logger.debug(f"Skipping command: {text}")
        return

    # Обработка выбора языка
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
            logger.debug(f"Language set to {lang_map[text]} for user {user_id}")
            await message.reply_text(
                text=get_text(context, "language_set", language=user_data["language"]),
                reply_markup=create_main_menu_keyboard(context)
            )
            return
        else:
            logger.debug(f"Invalid language input: {text}")
            await message.reply_text(
                text=get_text(context, "language_prompt"),
                reply_markup=create_language_keyboard()
            )
            return

    # Словарь для обработки кнопок (используем переведённые тексты)
    mode_map = {
        get_text(context, "play_button").lower(): "play_button",
        get_text(context, "classic_mode").lower(): "classic_mode",
        get_text(context, "player_vs_ai").lower(): "player_vs_ai",
        get_text(context, "ai_vs_player").lower(): "ai_vs_player",
        get_text(context, "ai_vs_ai").lower(): "ai_vs_ai",
        get_text(context, "tic_tac_toe_web3").lower(): "web3",
        get_text(context, "profile_button").lower(): "profile",
        get_text(context, "info_button").lower(): "info",
        get_text(context, "yes_button").lower(): "yes",
        get_text(context, "no_button").lower(): "no"
    }

    # Словарь для перевода кнопок сложности обратно в "easy", "medium", "hard"
    difficulty_map = {
        "ru": {"легко": "easy", "средне": "medium", "сложно": "hard"},
        "en": {"easy": "easy", "medium": "medium", "hard": "hard"},
        "ja": {"簡単": "easy", "中級": "medium", "難しい": "hard"},
        "it": {"facile": "easy", "medio": "medium", "difficile": "hard"},
        "hi": {"आसान": "easy", "मध्यम": "medium", "कठिन": "hard"}
    }

    # Обработка выбора режима или кнопок
    if text in mode_map:
        selected_mode = mode_map[text]
        logger.debug(f"Processing button: {selected_mode}")

        if selected_mode == "play_button":
            user_data["awaiting"] = "mode"
            await message.reply_text(
                text=get_text(context, "game_mode_prompt"),
                reply_markup=create_game_mode_keyboard(context)
            )
            return

        elif selected_mode in ["classic_mode", "player_vs_ai", "ai_vs_player", "ai_vs_ai"]:
            user_data["awaiting"] = "difficulty"
            user_data["game_mode"] = selected_mode
            await update.message.reply_text(
                text=get_text(context, "difficulty_prompt"),
                reply_markup=create_difficulty_keyboard(context)
            )
            return

        elif selected_mode == "web3":
            user_data.clear()
            user_data["language"] = context.user_data.get("language", settings["language"])
            keyboard = [InlineKeyboardButton("Play Web3", url=f"https://tic-tac-toewithoptimalaitelegrambot-production.up.railway.app/")]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text(
                text="Click below to play Tic Tac Toe Web3",
                reply_markup=reply_markup
            )
            clear_board_state(user_id)
            return

        elif selected_mode in ["profile", "info"]:
            await message.reply_text(
                text=get_text(context, "feature_coming_soon"),
                reply_markup=create_main_menu_keyboard(context)
            )
            return

        elif selected_mode == "yes" and user_data.get("awaiting_play_again"):
            user_data["awaiting_play_again"] = False
            user_data["awaiting"] = "difficulty"
            user_data["game_mode"] = user_data.get("last_mode")
            await update.message.reply_text(
                text=get_text(context, "difficulty_prompt"),
                reply_markup=create_difficulty_keyboard(context)
            )
            return

        elif selected_mode == "no" and user_data.get("awaiting_play_again"):
            user_data["awaiting_play_again"] = False
            user_data["awaiting"] = None
            await message.reply_text(
                text=get_text(context, "game_exit"),
                reply_markup=create_main_menu_keyboard(context)
            )
            return

    # Обработка выбора сложности
    if user_data.get("awaiting") == "difficulty":
        lang = user_data.get("language", settings["language"])
        difficulty = difficulty_map[lang].get(text, None)
        if difficulty in ["easy", "medium", "hard"]:
            try:
                user_data["difficulty"] = difficulty
                save_user_settings(user_id, difficulty)
                user_data["awaiting"] = "symbol"  # Переходим к выбору символа
                logger.debug(f"Difficulty set to {difficulty} for user {user_id}, awaiting symbol")

                # Инициализируем доску и счётчик ходов
                user_data["board"] = create_board()
                user_data["move_count"] = 0
                user_data["game_active"] = True

                await message.reply_text(
                    text=get_text(context, "choose_symbol"),
                    reply_markup=create_symbol_keyboard(context)
                )
            except Exception as e:
                logger.error(f"Error setting difficulty for user {user_id}: {e}")
                user_data["game_active"] = False
                await message.reply_text(
                    text=get_text(context, "error_message"),
                    reply_markup=create_main_menu_keyboard(context)
                )
        else:
            logger.debug(f"Invalid difficulty input: {text} for user {user_id}")
            await message.reply_text(
                text=get_text(context, "invalid_difficulty"),
                reply_markup=create_difficulty_keyboard(context)
            )
        return

    # Обработка выбора символа
    if user_data.get("awaiting") == "symbol":
        if text.upper() in ["X", "O"]:
            try:
                selected_symbol = text.upper()
                game_mode = user_data.get("game_mode")
                logger.debug(f"Symbol {selected_symbol} selected for user {user_id}, game_mode: {game_mode}")

                if game_mode not in ["player_vs_ai", "ai_vs_player", "ai_vs_ai", "classic_mode"]:
                    logger.error(f"Invalid game mode: {game_mode} for user {user_id}")
                    user_data.clear()
                    await message.reply_text(
                        text=get_text(context, "error_message"),
                        reply_markup=create_main_menu_keyboard(context)
                    )
                    return

                # Назначаем символы игрокам
                if game_mode in ["player_vs_ai", "ai_vs_player"]:
                    user_data["human_player"] = selected_symbol
                    user_data["ai_player"] = "O" if selected_symbol == "X" else "X"
                elif game_mode == "ai_vs_ai":
                    user_data["ai1_symbol"] = selected_symbol
                    user_data["ai2_symbol"] = "O" if selected_symbol == "X" else "X"
                elif game_mode == "classic_mode":
                    user_data["player1_symbol"] = selected_symbol
                    user_data["player2_symbol"] = "O" if selected_symbol == "X" else "X"

                save_board_state(user_id, user_data["board"], user_data["move_count"], context)

                await message.reply_text(
                    text=get_text(context, "symbol_assigned", symbol=selected_symbol),
                    reply_markup=None
                )
                await asyncio.sleep(1)

                # Запускаем игру в зависимости от режима
                logger.debug(f"Starting game mode {game_mode} for user {user_id}")
                user_data["awaiting"] = None
                if game_mode == "player_vs_ai":
                    await start_player_vs_ai(update, context, player_first=True)
                elif game_mode == "ai_vs_player":
                    await start_player_vs_ai(update, context, player_first=False)
                elif game_mode == "ai_vs_ai":
                    await start_ai_vs_ai(update, context, user_data["difficulty"])
                elif game_mode == "classic_mode":
                    await start_classic_game(update, context)
            except Exception as e:
                logger.error(f"Failed to start game for user {user_id}, mode: {game_mode}: {e}")
                user_data["game_active"] = False
                user_data.clear()
                await message.reply_text(
                    text=get_text(context, "error_message"),
                    reply_markup=create_main_menu_keyboard(context)
                )
                clear_board_state(user_id)
        else:
            logger.debug(f"Invalid symbol input: {text} for user {user_id}")
            await message.reply_text(
                text=get_text(context, "invalid_symbol"),
                reply_markup=create_symbol_keyboard(context)
            )
        return    
    if user_data.get("game_active") and game_mode in ["player_vs_ai", "ai_vs_player", "classic_mode"]:
        try:
            # Пытаемся преобразовать ввод в число (ход)
            move = int(text.strip()) - 1  # Переводим в 0-8 индекс
            if 0 <= move < 9 and board[move] == " ":
                # Определяем символ текущего игрока
                if game_mode == "classic_mode":
                    if "player1_symbol" not in user_data or "player2_symbol" not in user_data:
                        logger.error(f"Missing player symbols for user {user_id}: {user_data}")
                        raise ValueError("Missing player symbols")
                    current_player = user_data["player1_symbol"] if user_data["move_count"] % 2 == 0 else user_data["player2_symbol"]
                else:
                    current_player = user_data["human_player"]
                
                # Делаем ход
                board[move] = current_player
                user_data["move_count"] += 1
                
                # Проверяем и сохраняем состояние
                required_keys = ["game_mode", "difficulty", "player1_symbol", "player2_symbol"] if game_mode == "classic_mode" else ["game_mode", "difficulty", "human_player", "ai_player"]
                if not all(key in user_data for key in required_keys):
                    logger.error(f"Missing required keys for user {user_id}: {user_data}")
                    raise ValueError("Missing required game data")
                
                save_board_state(user_id, board, user_data["move_count"], context)
                
                # Проверяем результат после хода
                if check_winner(board, current_player):
                    await message.reply_text(
                        text=f"{get_text(context, 'player_wins', player=current_player)}\n\n{format_board(board)}",
                        reply_markup=ReplyKeyboardMarkup(
                            [[get_text(context, "yes_button"), get_text(context, "no_button")]],
                            resize_keyboard=True
                        )
                    )    
                    user_data["game_active"] = False
                    return
                elif is_board_full(board):
                    await message.reply_text(
                        text=f"{get_text(context, 'draw')}\n\n{format_board(board)}",
                        reply_markup=ReplyKeyboardMarkup(
                            [[get_text(context, "yes_button"), get_text(context, "no_button")]],
                            resize_keyboard=True
                        )
                    )
                    user_data["game_active"] = False
                    return
                
                # Если игра продолжается, обновляем доску
                reply_markup = create_keyboard(board, True)
                if "board_message_id" in user_data:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=user_id,
                            message_id=user_data["board_message_id"],
                            text=f"{format_board(board)}\n\n{get_text(context, 'your_turn')}",
                            reply_markup=reply_markup
                        )
                    except Exception as e:
                        logger.warning(f"Failed to edit message for user {user_id}: {e}, sending new one")
                        board_message = await try_update_message(message, f"{format_board(board)}\n\n{get_text(context, 'your_turn')}", reply_markup, context)
                        if board_message:
                            user_data["board_message_id"] = board_message.message_id
                else:
                    board_message = await try_update_message(message, f"{format_board(board)}\n\n{get_text(context, 'your_turn')}", reply_markup, context)
                    if board_message:
                        user_data["board_message_id"] = board_message.message_id
                
                # Если это режим против ИИ, делаем ход ИИ
                if game_mode in ["player_vs_ai", "ai_vs_player"]:
                    await asyncio.sleep(1)  # Небольшая задержка для "раздумий" ИИ
                    ai_player = user_data["ai_player"]
                    ai_move_idx = ai_move(board, ai_player, user_data.get("difficulty", "medium"))
                    
                    if ai_move_idx is not None and 0 <= ai_move_idx < 9 and board[ai_move_idx] == " ":
                        board[ai_move_idx] = ai_player
                        user_data["move_count"] += 1
                        save_board_state(user_id, board, user_data["move_count"], context)
                        
                        # Проверяем результат после хода ИИ
                        if check_winner(board, ai_player):
                            await message.reply_text(
                                text=f"{get_text(context, 'player_wins', player=ai_player)}\n\n{format_board(board)}",
                                reply_markup=ReplyKeyboardMarkup(
                                    [[get_text(context, "yes_button"), get_text(context, "no_button")]],
                                    resize_keyboard=True
                                )
                            )
                            user_data["game_active"] = False
                            return
                        elif is_board_full(board):
                            await message.reply_text(
                                text=f"{get_text(context, 'draw')}\n\n{format_board(board)}",
                                reply_markup=ReplyKeyboardMarkup(
                                    [[get_text(context, "yes_button"), get_text(context, "no_button")]],
                                    resize_keyboard=True
                                )
                            )
                            user_data["game_active"] = False
                            return
                        
                        # Обновляем доску после хода ИИ
                        reply_markup = create_keyboard(board, True)
                        await message.reply_text(
                            text=f"{format_board(board)}\n\n{get_text(context, 'your_turn')}",
                            reply_markup=reply_markup
                        )
                else:
                    await message.reply_text(
                        text=get_text(context, "human_move"),
                        reply_markup=create_keyboard(board, True)
                    )
        except ValueError:
            await message.reply_text(
                text=get_text(context, "invalid_move"),
                reply_markup=create_keyboard(board, True)
            )
        return

    # Если команда не распознана, показываем главное меню
    await message.reply_text(
        text=get_text(context, "main_menu"),
        reply_markup=create_main_menu_keyboard(context)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.message.chat.id
    logger.debug(f"Start command received from user {user_id}")
    user_data.clear()
    user_data["awaiting_language"] = True
    await update.message.reply_text(
        text=get_text(context, "welcome_message"),
        reply_markup=create_language_keyboard()
    )

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.message.chat_id
    logger.debug(f"Restart command received from user {user_id}")
    user_data.clear()  # Полный сброс состояния
    user_data["awaiting_language"] = True  # Установка флага для выбора языка
    clear_board_state(user_id)  # Очистка сохранённого состояния доски
    await update.message.reply_text(
        text=get_text(context, "game_restarted"),
        reply_markup=create_language_keyboard()
    )

async def set_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.message.chat.id
    logger.debug(f"Difficulty command received from user {user_id}")
    user_data["awaiting"] = "difficulty"
    await update.message.reply_text(
        text=get_text(context, "difficulty_prompt"),
        reply_markup=create_difficulty_keyboard(context)
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.message.chat.id
    logger.debug(f"Language command received from user {user_id}")
    user_data["awaiting_language"] = True
    await update.message.reply_text(
        text=get_text(context, "language_prompt"),
        reply_markup=create_language_keyboard()
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    logger.debug(f"Settings command received from user {user_id}")
    await update.message.reply_text(
        text=get_text(context, "settings_menu"),
        reply_markup=create_main_menu_keyboard(context)
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.message:
        user_data = context.user_data
        user_data["game_active"] = False
        user_data.clear()
        await update.message.reply_text(
            text=get_text(context, "error_message"),
            reply_markup=create_main_menu_keyboard(context)
        )
        clear_board_state(update.message.chat.id)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    context.user_data.clear()
    clear_board_state(user_id)
    logger.debug(f"State reset for user {user_id}")
    await update.message.reply_text(
        text="Состояние сброшено. Начните новую игру с /start.",
        reply_markup=create_main_menu_keyboard(context)
    )
def save_data(data, filename='board_state.json'):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
        print("Данные успешно сохранены!")
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")

# Функция для загрузки данных из JSON-файла
def load_data(filename='board_state.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        print("Данные успешно загружены!")
        return data
    except FileNotFoundError:
        print("Сохранённый файл не найден. Начинаем с нуля.")
        return None
    except Exception as e:
        print(f"Ошибка при загрузке: {e}")
        return None

def main():
    lock = acquire_lock()
    try:
        # Инициализация базы данных
        conn = sqlite3.connect("game.db")
        with open("database.sql", "r") as f:
            conn.executescript(f.read())
        conn.close()
        
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("restart", restart))
        app.add_handler(CommandHandler("difficulty", set_difficulty))
        app.add_handler(CommandHandler("language", set_language))
        app.add_handler(CommandHandler("settings", settings_command))
        app.add_handler(CommandHandler("reset", reset))
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
        logger.info("Bot shutdown, lock released")

if __name__ == "__main__":
    main()
