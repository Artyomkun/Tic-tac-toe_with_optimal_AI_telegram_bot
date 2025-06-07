import os
import json
import random
import time
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from uuid import uuid4
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

if not all([BOT_TOKEN, INFURA_PROJECT_ID, PRIVATE_KEY, CONTRACT_ADDRESS]):
    print("Ошибка: Не все переменные окружения заданы")
    exit()
else:
    print(f"Токен загружен: {BOT_TOKEN[:10]}...")
    print(f"Infura Project ID: {INFURA_PROJECT_ID[:10]}...")

# Web3 setup
w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}'))
if not w3.is_connected():
    print("Ошибка: Не удалось подключиться к Infura")
    exit()

# Contract setup
contract_abi = [  # Replace with your contract's ABI
    {
        "inputs": [
            {"internalType": "string", "name": "_playerSymbol", "type": "string"},
            {"internalType": "string", "name": "_aiSymbol", "type": "string"},
            {"internalType": "string", "name": "_outcome", "type": "string"}
        ],
        "name": "saveGameResult",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_gameId", "type": "uint256"}
        ],
        "name": "verifyGameData",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "gameCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
account = w3.eth.account.from_key(PRIVATE_KEY)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Game settings
settings = {
    "logs_enabled": True,
    "language": "ru",
    "ai_delay": 2.0,
    "adaptivity_level": 0.7,
    "difficulty": "medium",
}

# Game memory and stats
ai_memory = {}
human_memory = {}
ai_logs = []
stats = {
    "AI": {"wins": 0, "losses": 0, "draws": 0},
    "Human": {"wins": 0, "losses": 0, "draws": 0},
}

# Translations
translations = {
    "ru": {
        "welcome_message": "Добро пожаловать в Крестики-Нолики! 🎮\nВыберите режим игры:",
        "game_start": "Игра начинается! Вы - {player}, ИИ - {opponent}. Ваш ход!",
        "invalid_move": "Неверный ход! Выберите другую клетку.",
        "player_wins": "{player} побеждает! 🏆",
        "draw": "Ничья! 🤝",
        "play_again": "Сыграть еще?",
        "yes_button": "Да",
        "no_button": "Нет",
        "game_exit": "Игра завершена. До встречи! 👋",
        "difficulty_prompt": "Выберите сложность: easy, medium, hard",
        "invalid_difficulty": "Неверная сложность. Используйте: easy, medium, hard",
        "difficulty_set": "Сложность установлена: {difficulty}",
        "language_prompt": "Выберите язык: ru, en, ja, it, hi",
        "invalid_language": "Неверный язык. Используйте: ru, en, ja, it, hi",
        "language_set": "Язык установлен: {language}",
        "board_message": "Текущая доска:",
        "ai_move": "ИИ ({player}) ходит на позицию {move}.",
        "settings_menu": "Настройки:\n/difficulty - Сложность\n/language - Язык",
        "ai_thinking": "ИИ думает...",
        "play_button": "Играть",
        "info_button": "Инфо 🚨",
        "language_button": "Смена языка",
        "profile_button": "Профиль",
        "select_language": "Какой язык выбрать?",
        "game_mode_prompt": "Выберите режим игры:",
        "classic_mode": "Классическая игра",
        "player_vs_ai": "Игрок против ИИ",
        "ai_vs_player": "ИИ против игрока",
        "ai_vs_ai": "ИИ против ИИ",
        "web3_mode": "Веб3 игра",
        "choose_symbol": "Выберите символ: X или O"
    },
    "en": {
        "welcome_message": "Welcome to Tic-Tac-Toe! 🎮\nChoose a game mode:",
        "game_start": "Game starts! You are {player}, AI is {opponent}. Your turn!",
        "invalid_move": "Invalid move! Try another cell.",
        "player_wins": "{player} wins! 🏆",
        "draw": "It's a draw! 🤝",
        "play_again": "Play again?",
        "yes_button": "Yes",
        "no_button": "No",
        "game_exit": "Game over. See you next time! 👋",
        "difficulty_prompt": "Choose difficulty: easy, medium, hard",
        "invalid_difficulty": "Invalid difficulty. Use: easy, medium, hard",
        "difficulty_set": "Difficulty set to: {difficulty}",
        "language_prompt": "Choose language: ru, en, ja, it, hi",
        "invalid_language": "Invalid language. Use: ru, en, ja, it, hi",
        "language_set": "Language set to: {language}",
        "board_message": "Current board:",
        "ai_move": "AI ({player}) moves to position {move}.",
        "settings_menu": "Settings:\n/difficulty - Difficulty\n/language - Language",
        "ai_thinking": "AI is thinking...",
        "play_button": "Play",
        "info_button": "Info 🚨",
        "language_button": "Change Language",
        "profile_button": "Profile",
        "select_language": "Which language to choose?",
        "game_mode_prompt": "Choose a game mode:",
        "classic_mode": "Classic Game",
        "player_vs_ai": "Player vs AI",
        "ai_vs_player": "AI vs Player",
        "ai_vs_ai": "AI vs AI",
        "web3_mode": "Web3 Game",
        "choose_symbol": "Choose symbol: X or O"
    },
    "ja": {
        "welcome_message": "tic-tac-toeへようこそ！ 🎮\nゲームモードを選択してください：",
        "game_start": "ゲーム開始！あなたは{player}、AIは{opponent}です。あなたのターン！",
        "invalid_move": "無効な動きです！別のセルを試してください。",
        "player_wins": "{player}が勝ちました！ 🏆",
        "draw": "引き分けです！ 🤝",
        "play_again": "もう一度プレイしますか？",
        "yes_button": "はい",
        "no_button": "いいえ",
        "game_exit": "ゲーム終了。またお会いしましょう！ 👋",
        "difficulty_prompt": "難易度を選んでください: easy, medium, hard",
        "invalid_difficulty": "無効な難易度です。使用: easy, medium, hard",
        "difficulty_set": "難易度が設定されました: {difficulty}",
        "language_prompt": "言語を選んでください: ru, en, ja, it, hi",
        "invalid_language": "無効な言語です。使用: ru, en, ja, it, hi",
        "language_set": "言語が設定されました: {language}",
        "board_message": "現在のボード:",
        "ai_move": "AI ({player}) がポジション {move} に移動しました。",
        "settings_menu": "設定:\n/difficulty - 難易度\n/language - 言語",
        "ai_thinking": "AIが考えています...",
        "play_button": "プレイ",
        "info_button": "情報 🚨",
        "language_button": "言語変更",
        "profile_button": "プロフィール",
        "select_language": "どの言語を選びますか？",
        "game_mode_prompt": "ゲームモードを選択してください：",
        "classic_mode": "クラシックゲーム",
        "player_vs_ai": "プレイヤー対AI",
        "ai_vs_player": "AI対プレイヤー",
        "ai_vs_ai": "AI対AI",
        "web3_mode": "Web3ゲーム",
        "choose_symbol": "シンボルを選択してください：XまたはO"
    },
    "it": {
        "welcome_message": "Benvenuto a Tris! 🎮\nScegli una modalità di gioco:",
        "game_start": "Il gioco inizia! Tu sei {player}, l'IA è {opponent}. Tocca a te!",
        "invalid_move": "Mossa non valida! Prova un'altra cella.",
        "player_wins": "{player} vince! 🏆",
        "draw": "È un pareggio! 🤝",
        "play_again": "Giocare di nuovo?",
        "yes_button": "Sì",
        "no_button": "No",
        "game_exit": "Partita finita. Ci vediamo! 👋",
        "difficulty_prompt": "Scegli la difficoltà: easy, medium, hard",
        "invalid_difficulty": "Difficoltà non valida. Usa: easy, medium, hard",
        "difficulty_set": "Difficoltà impostata: {difficulty}",
        "language_prompt": "Scegli la lingua: ru, en, ja, it, hi",
        "invalid_language": "Lingua non valida. Usa: ru, en, ja, it, hi",
        "language_set": "Lingua impostata: {language}",
        "board_message": "Tavolo attuale:",
        "ai_move": "L'IA ({player}) si muove alla posizione {move}.",
        "settings_menu": "Impostazioni:\n/difficulty - Difficoltà\n/language - Lingua",
        "ai_thinking": "L'IA sta pensando...",
        "play_button": "Gioca",
        "info_button": "Info 🚨",
        "language_button": "Cambia Lingua",
        "profile_button": "Profilo",
        "select_language": "Quale lingua scegliere?",
        "game_mode_prompt": "Scegli una modalità di gioco:",
        "classic_mode": "Gioco Classico",
        "player_vs_ai": "Giocatore vs IA",
        "ai_vs_player": "IA vs Giocatore",
        "ai_vs_ai": "IA vs IA",
        "web3_mode": "Gioco Web3",
        "choose_symbol": "Scegli il simbolo: X o O"
    },
    "hi": {
        "welcome_message": "टिक-टैक-टो में आपका स्वागत है! 🎮\nखेल मोड चुनें:",
        "game_start": "खेल शुरू! आप {player} हैं, AI {opponent} है। आपकी बारी!",
        "invalid_move": "अमान्य चाल! दूसरी सेल आज़माएं।",
        "player_wins": "{player} जीत गया! 🏆",
        "draw": "यह ड्रॉ है! 🤝",
        "play_again": "फिर से खेलें?",
        "yes_button": "हां",
        "no_button": "नहीं",
        "game_exit": "खेल खत्म। फिर मिलेंगे! 👋",
        "difficulty_prompt": "कठिनाई चुनें: easy, medium, hard",
        "invalid_difficulty": "अमान्य कठिनाई। उपयोग करें: easy, medium, hard",
        "difficulty_set": "कठिनाई सेट: {difficulty}",
        "language_prompt": "भाषा चुनें: ru, en, ja, it, hi",
        "invalid_language": "अमान्य भाषा। उपयोग करें: ru, en, ja, it, hi",
        "language_set": "भाषा सेट: {language}",
        "board_message": "वर्तमान बोर्ड:",
        "ai_move": "AI ({player}) ने स्थिति {move} पर चाल चली।",
        "settings_menu": "सेटिंग्स:\n/difficulty - कठिनाई\n/language - भाषा",
        "ai_thinking": "AI सोच रहा है...",
        "play_button": "खेलें",
        "info_button": "जानकारी 🚨",
        "language_button": "भाषा बदलें",
        "profile_button": "प्रोफाइल",
        "select_language": "कौन सी भाषा चुनें?",
        "game_mode_prompt": "खेल मोड चुनें:",
        "classic_mode": "क्लासिक गेम",
        "player_vs_ai": "खिलाड़ी बनाम AI",
        "ai_vs_player": "AI बनाम खिलाड़ी",
        "ai_vs_ai": "AI बनाम AI",
        "web3_mode": "वेब3 गेम",
        "choose_symbol": "प्रतीक चुनें: X या O"
    }
}

def get_text(context: ContextTypes.DEFAULT_TYPE, key, **kwargs):
    lang = context.user_data.get("language", settings["language"])
    text = translations.get(lang, translations["ru"]).get(key, key)
    return text.format(**kwargs if kwargs else {})

def create_board():
    return [" " for _ in range(9)]

def format_board(board):
    ascii_board = "╔═══╦═══╦═══╗\n"
    for i in range(3):
        ascii_board += "║ "
        for j in range(3):
            idx = i * 3 + j
            cell = board[idx] if board[idx] != " " else " "
            ascii_board += f"{cell} ║ "
        ascii_board += "\n"
        if i < 2:
            ascii_board += "╠═══╬═══╬═══╣\n"
        else:
            ascii_board += "╚═══╩═══╩═══╝"
    return ascii_board

def save_game_result(player_symbol, ai_symbol, outcome):
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.eth.gas_price
        txn = contract.functions.saveGameResult(player_symbol, ai_symbol, outcome).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': gas_price,
            'chainId': 1  # Ethereum mainnet chain ID
        })
        signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            logger.info(f"Game result saved, tx hash: {tx_hash.hex()}")
            return tx_hash.hex()
        else:
            logger.error("Transaction failed")
            return None
    except Exception as e:
        logger.error(f"Error saving game result: {e}")
        return None

def verify_game_data(game_id):
    try:
        result = contract.functions.verifyGameData(game_id).call()
        return {
            'player': result[0],
            'player_symbol': result[1],
            'ai_symbol': result[2],
            'outcome': result[3],
            'timestamp': result[4]
        }
    except Exception as e:
        logger.error(f"Error verifying game data: {e}")
        return None

def create_keyboard(board):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            idx = i * 3 + j
            cell = board[idx] if board[idx] != " " else " "
            callback = f"move_{idx}" if board[idx] == " " else "invalid"
            row.append(InlineKeyboardButton(cell, callback_data=callback))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def create_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("日本語", callback_data="lang_ja")],
        [InlineKeyboardButton("Italiano", callback_data="lang_it")],
        [InlineKeyboardButton("हिन्दी", callback_data="lang_hi")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_game_mode_keyboard(context: ContextTypes.DEFAULT_TYPE, include_web3=False):
    lang = context.user_data.get("language", settings["language"])
    keyboard = [
        [InlineKeyboardButton(get_text(context, "classic_mode"), callback_data="mode_classic")],
        [InlineKeyboardButton(get_text(context, "player_vs_ai"), callback_data="mode_pva")],
        [InlineKeyboardButton(get_text(context, "ai_vs_player"), callback_data="mode_avp")],
        [InlineKeyboardButton(get_text(context, "ai_vs_ai"), callback_data="mode_ava")]
    ]
    if include_web3:
        keyboard.append([InlineKeyboardButton(get_text(context, "web3_mode"), callback_data="mode_web3")])
    return InlineKeyboardMarkup(keyboard)

def create_symbol_keyboard(context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("X", callback_data="symbol_X"), InlineKeyboardButton("O", callback_data="symbol_O")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_play_again_keyboard(context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", settings["language"])
    keyboard = [
        [
            InlineKeyboardButton(get_text(context, "yes_button"), callback_data="play_again_yes"),
            InlineKeyboardButton(get_text(context, "no_button"), callback_data="play_again_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_main_menu(context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", settings["language"])
    keyboard = [
        [KeyboardButton(get_text(context, "play_button"))],
        [
            KeyboardButton(get_text(context, "profile_button")),
            KeyboardButton(get_text(context, "info_button"))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def check_winner(board, player):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    return any(board[a] == board[b] == board[c] == player for a, b, c in wins)

def is_board_full(board):
    return " " not in board

def get_available_moves(board):
    return [i for i, spot in enumerate(board) if spot == " "]

def log_move(board, move, player):
    if settings["logs_enabled"]:
        ai_logs.append({"board": board[:], "move": move, "player": player})

def update_stats(winner):
    if winner == "AI":
        stats["AI"]["wins"] += 1
        stats["Human"]["losses"] += 1
    elif winner == "Human":
        stats["Human"]["wins"] += 1
        stats["AI"]["losses"] += 1
    else:
        stats["AI"]["draws"] += 1
        stats["Human"]["draws"] += 1

def evaluate_board(board):
    if check_winner(board, "O"):
        return 1
    if check_winner(board, "X"):
        return -1
    if is_board_full(board):
        return 0
    return None

def minimax(board, depth, is_maximizing, player, opponent, alpha=-float("inf"), beta=float("inf")):
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
    opponent = "O" if player == "X" else "X"
    if difficulty == "easy":
        time.sleep(settings["ai_delay"])
        return random.choice(get_available_moves(board))
    elif difficulty == "medium":
        if random.random() < settings["adaptivity_level"]:
            key = str(tuple(board))
            if player == "X" and key in ai_memory:
                time.sleep(settings["ai_delay"])
                return random.choices(ai_memory[key]["moves"], weights=ai_memory[key]["weights"])[0]
            elif player == "O" and key in human_memory:
                time.sleep(settings["ai_delay"])
                return random.choices(human_memory[key]["moves"], weights=human_memory[key]["weights"])[0]
        time.sleep(settings["ai_delay"])
        return random.choice(get_available_moves(board))
    else:  # hard
        best_score = -float("inf") if player == "O" else float("inf")
        best_moves = []
        for move in get_available_moves(board):
            board[move] = player
            score = minimax(board, 0, player == "X", player, opponent)
            board[move] = " "
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
        time.sleep(settings["ai_delay"])
        return random.choice(best_moves)

def update_memory(board, move, player, outcome):
    board_key = str(tuple(board))
    memory = ai_memory if player == "O" else human_memory
    if board_key not in memory:
        memory[board_key] = {"moves": [], "weights": []}
    if move not in memory[board_key]["moves"]:
        memory[board_key]["moves"].append(move)
        memory[board_key]["weights"].append(1 if outcome == "win" else 0.5)
    else:
        idx = memory[board_key]["moves"].index(move)
        memory[board_key]["weights"][idx] += 1 if outcome == "win" else 0.5

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        language_prompt = "\n".join(
            translations[lang]["select_language"] for lang in ["ru", "en", "ja", "it", "hi"]
        )
        await update.message.reply_text(
            language_prompt,
            reply_markup=create_language_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(get_text(context, "error_message"))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        if lang in ["ru", "en", "ja", "it", "hi"]:
            context.user_data["language"] = lang
            await query.message.reply_text(
                get_text(context, "game_mode_prompt"),
                reply_markup=create_game_mode_keyboard(context, include_web3=True)
            )
        else:
            await query.message.reply_text(
                get_text(context, "invalid_language"),
                reply_markup=create_language_keyboard()
            )
        return

    if data.startswith("mode_"):
        mode = data.split("_")[1]
        context.user_data["game_mode"] = mode
        if mode == "web3":
            context.user_data["game_active"] = True
            context.user_data["board"] = create_board()
            context.user_data["human_player"] = "X"
            context.user_data["ai_player"] = "O"
            await query.message.reply_text(
                get_text(context, "game_start", player="X", opponent="O"),
                reply_markup=create_keyboard(context.user_data["board"])
            )
            return
        elif mode == "ava":
            await start_ai_vs_ai(update, context)
            return
        else:
            await query.message.reply_text(
                get_text(context, "choose_symbol"),
                reply_markup=create_symbol_keyboard(context)
            )
        return

    if data.startswith("symbol_"):
        symbol = data.split("_")[1]
        context.user_data["human_player"] = symbol
        context.user_data["ai_player"] = "O" if symbol == "X" else "X"
        context.user_data["board"] = create_board()
        context.user_data["game_active"] = True
        mode = context.user_data.get("game_mode")
        if mode == "classic" or mode == "pva":
            await start_player_vs_ai(update, context, player_first=True)
        elif mode == "avp":
            await start_player_vs_ai(update, context, player_first=False)
        return

    if data == "play_again_yes":
        context.user_data["board"] = create_board()
        context.user_data["game_active"] = True
        mode = context.user_data.get("game_mode")
        if mode == "classic" or mode == "pva":
            await start_player_vs_ai(update, context, player_first=True)
        elif mode == "avp":
            await start_player_vs_ai(update, context, player_first=False)
        elif mode == "ava":
            await start_ai_vs_ai(update, context)
        elif mode == "web3":
            await query.message.reply_text(
                get_text(context, "game_start", player=context.user_data["human_player"], opponent=context.user_data["ai_player"]),
                reply_markup=create_keyboard(context.user_data["board"])
            )
        return
    elif data == "play_again_no":
        context.user_data["game_active"] = False
        await query.message.reply_text(
            get_text(context, "welcome_message"),
            reply_markup=create_main_menu(context)
        )
        return

    if not context.user_data.get("game_active", False):
        await query.message.reply_text(get_text(context, "game_exit"))
        return

    board = context.user_data["board"]
    if data.startswith("move_"):
        move = int(data.split("_")[1])
        if 0 <= move < 9 and board[move] == " ":
            board[move] = context.user_data["human_player"]
            log_move(board, move, context.user_data["human_player"])
            outcome = "win" if check_winner(board, context.user_data["human_player"]) else "pending"
            update_memory(board[:], move, context.user_data["human_player"], outcome)

            await query.message.edit_text(
                text=f"{get_text(context, 'board_message')}\n{format_board(board)}",
                reply_markup=create_keyboard(board)
            )

            if check_winner(board, context.user_data["human_player"]):
                await query.message.reply_text(get_text(context, "player_wins", player=context.user_data["human_player"]))
                update_stats("Human")
                if context.user_data.get("game_mode") == "web3":
                    tx_hash = save_game_result(
                        context.user_data["human_player"],
                        context.user_data["ai_player"],
                        "Human Win"
                    )
                    if tx_hash:
                        await query.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                    else:
                        await query.message.reply_text("Failed to save game result to blockchain.")
                context.user_data["game_active"] = False
                await query.message.reply_text(
                    get_text(context, "play_again"),
                    reply_markup=create_play_again_keyboard(context)
                )
                return
            if is_board_full(board):
                await query.message.reply_text(get_text(context, "draw"))
                update_stats(None)
                if context.user_data.get("game_mode") == "web3":
                    tx_hash = save_game_result(
                        context.user_data["human_player"],
                        context.user_data["ai_player"],
                        "Draw"
                    )
                    if tx_hash:
                        await query.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                    else:
                        await query.message.reply_text("Failed to save game result to blockchain.")
                context.user_data["game_active"] = False
                await query.message.reply_text(
                    get_text(context, "play_again"),
                    reply_markup=create_play_again_keyboard(context)
                )
                return

            await query.message.reply_text(get_text(context, "ai_thinking"))
            ai = ai_move(board, context.user_data["ai_player"], settings["difficulty"])
            if ai is not None:
                board[ai] = context.user_data["ai_player"]
                log_move(board, ai, context.user_data["ai_player"])
                outcome = "win" if check_winner(board, context.user_data["ai_player"]) else "pending"
                update_memory(board[:], ai, context.user_data["ai_player"], outcome)
                await query.message.reply_text(
                    text=f"{get_text(context, 'board_message')}\n{format_board(board)}\n\n"
                         f"{get_text(context, 'ai_move', player=context.user_data['ai_player'], move=ai + 1)}",
                    reply_markup=create_keyboard(board)
                )

                if check_winner(board, context.user_data["ai_player"]):
                    await query.message.reply_text(get_text(context, "player_wins", player=context.user_data["ai_player"]))
                    update_stats("AI")
                    if context.user_data.get("game_mode") == "web3":
                        tx_hash = save_game_result(
                            context.user_data["human_player"],
                            context.user_data["ai_player"],
                            "AI Win"
                        )
                        if tx_hash:
                            await query.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                        else:
                            await query.message.reply_text("Failed to save game result to blockchain.")
                    context.user_data["game_active"] = False
                    await query.message.reply_text(
                        get_text(context, "play_again"),
                        reply_markup=create_play_again_keyboard(context)
                    )
                    return
                if is_board_full(board):
                    await query.message.reply_text(get_text(context, "draw"))
                    update_stats(None)
                    if context.user_data.get("game_mode") == "web3":
                        tx_hash = save_game_result(
                            context.user_data["human_player"],
                            context.user_data["ai_player"],
                            "Draw"
                        )
                        if tx_hash:
                            await query.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                        else:
                            await query.message.reply_text("Failed to save game result to blockchain.")
                    context.user_data["game_active"] = False
                    await query.message.reply_text(
                        get_text(context, "play_again"),
                        reply_markup=create_play_again_keyboard(context)
                    )
                    return
        else:
            await query.message.reply_text(get_text(context, "invalid_move"))
    elif data == "invalid":
        await query.message.reply_text(get_text(context, "invalid_move"))

async def start_player_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, player_first=True):
    board = context.user_data["board"]
    human_player = context.user_data["human_player"]
    ai_player = context.user_data["ai_player"]
    await update.callback_query.message.reply_text(
        get_text(context, "game_start", player=human_player, opponent=ai_player),
        reply_markup=create_main_menu(context)
    )
    if not player_first:
        await update.callback_query.message.reply_text(get_text(context, "ai_thinking"))
        ai = ai_move(board, ai_player, settings["difficulty"])
        if ai is not None:
            board[ai] = ai_player
            log_move(board, ai, ai_player)
            outcome = "win" if check_winner(board, ai_player) else "pending"
            update_memory(board[:], ai, ai_player, outcome)
        await update.callback_query.message.reply_text(
            text=f"{get_text(context, 'board_message')}\n{format_board(board)}\n\n"
                 f"{get_text(context, 'ai_move', player=ai_player, move=ai + 1)}",
            reply_markup=create_keyboard(board)
        )
    else:
        await update.callback_query.message.reply_text(
            text=f"{get_text(context, 'board_message')}\n{format_board(board)}",
            reply_markup=create_keyboard(board)
        )

async def start_ai_vs_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["board"] = create_board()
    context.user_data["game_active"] = True
    board = context.user_data["board"]
    await update.callback_query.message.reply_text(
        get_text(context, "game_start", player="AI1 (X)", opponent="AI2 (O)"),
        reply_markup=create_main_menu(context)
    )
    while context.user_data["game_active"]:
        for player in ["X", "O"]:
            await update.callback_query.message.reply_text(get_text(context, "ai_thinking"))
            move = ai_move(board, player, settings["difficulty"])
            if move is not None:
                board[move] = player
                log_move(board, move, player)
                outcome = "win" if check_winner(board, player) else "pending"
                update_memory(board[:], move, player, outcome)
                await update.callback_query.message.reply_text(
                    text=f"{get_text(context, 'board_message')}\n{format_board(board)}\n\n"
                         f"{get_text(context, 'ai_move', player=player, move=move + 1)}",
                    reply_markup=create_keyboard(board)
                )
                if check_winner(board, player):
                    await update.callback_query.message.reply_text(get_text(context, "player_wins", player=player))
                    update_stats("AI")
                    context.user_data["game_active"] = False
                    await update.callback_query.message.reply_text(
                        get_text(context, "play_again"),
                        reply_markup=create_play_again_keyboard(context)
                    )
                    return
                if is_board_full(board):
                    await update.callback_query.message.reply_text(get_text(context, "draw"))
                    update_stats(None)
                    context.user_data["game_active"] = False
                    await update.callback_query.message.reply_text(
                        get_text(context, "play_again"),
                        reply_markup=create_play_again_keyboard(context)
                    )
                    return
            await asyncio.sleep(settings["ai_delay"])

async def set_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].lower() in ["easy", "medium", "hard"]:
        settings["difficulty"] = args[0].lower()
        await update.message.reply_text(get_text(context, "difficulty_set", difficulty=args[0].lower()))
    else:
        await update.message.reply_text(get_text(context, "difficulty_prompt") + "\n" + get_text(context, "invalid_difficulty"))

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].lower() in ["ru", "en", "ja", "it", "hi"]:
        context.user_data["language"] = args[0].lower()
        await update.message.reply_text(
            get_text(context, "language_set", language=args[0].lower()),
            reply_markup=create_main_menu(context)
        )
    else:
        await update.message.reply_text(
            get_text(context, "language_prompt") + "\n" + get_text(context, "invalid_language"),
            reply_markup=create_main_menu(context)
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(context, "settings_menu"))

async def view_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        game_count = contract.functions.gameCount().call()
        if game_count == 0:
            await update.message.reply_text("No games recorded on the blockchain yet.")
            return

        response = "Recorded Games:\n"
        for i in range(game_count):
            game_data = verify_game_data(i)
            if game_data:
                response += (
                    f"Game {i+1}: {game_data['timestamp']}\n"
                    f"Player: {game_data['player_symbol']}, AI: {game_data['ai_symbol']}, Outcome: {game_data['outcome']}\n"
                    f"Player Address: {game_data['player']}\n\n"
                )
            else:
                response += f"Game {i+1}: Error retrieving data\n\n"
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error viewing games: {e}")
        await update.message.reply_text("Error retrieving game data from blockchain.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = context.user_data.get("language", settings["language"])
    play_text = translations[lang]["play_button"]

    if text == play_text:
        await update.message.reply_text(
            get_text(context, "game_mode_prompt"),
            reply_markup=create_game_mode_keyboard(context, include_web3=True)
        )
        return

    if context.user_data.get("game_active", False) and context.user_data.get("game_mode") == "web3":
        try:
            move = int(text) - 1  # Convert to 0-based index
            if 0 <= move < 9 and context.user_data["board"][move] == " ":
                board = context.user_data["board"]
                human_player = context.user_data["human_player"]
                ai_player = context.user_data["ai_player"]

                # Human move
                board[move] = human_player
                log_move(board, move, human_player)
                outcome = "win" if check_winner(board, human_player) else "pending"
                update_memory(board[:], move, human_player, outcome)

                await update.message.reply_text(
                    text=f"{get_text(context, 'board_message')}\n{format_board(board)}",
                    reply_markup=create_keyboard(board)
                )

                if check_winner(board, human_player):
                    await update.message.reply_text(get_text(context, "player_wins", player=human_player))
                    update_stats("Human")
                    tx_hash = save_game_result(human_player, ai_player, "Human Win")
                    if tx_hash:
                        await update.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                    else:
                        await update.message.reply_text("Failed to save game result to blockchain.")
                    context.user_data["game_active"] = False
                    await update.message.reply_text(
                        get_text(context, "play_again"),
                        reply_markup=create_play_again_keyboard(context)
                    )
                    return
                if is_board_full(board):
                    await update.message.reply_text(get_text(context, "draw"))
                    update_stats(None)
                    tx_hash = save_game_result(human_player, ai_player, "Draw")
                    if tx_hash:
                        await update.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                    else:
                        await update.message.reply_text("Failed to save game result to blockchain.")
                    context.user_data["game_active"] = False
                    await update.message.reply_text(
                        get_text(context, "play_again"),
                        reply_markup=create_play_again_keyboard(context)
                    )
                    return

                # AI move
                await update.message.reply_text(get_text(context, "ai_thinking"))
                ai_move_idx = ai_move(board, ai_player, settings["difficulty"])
                if ai_move_idx is not None:
                    board[ai_move_idx] = ai_player
                    log_move(board, ai_move_idx, ai_player)
                    outcome = "win" if check_winner(board, ai_player) else "pending"
                    update_memory(board[:], ai_move_idx, ai_player, outcome)
                    await update.message.reply_text(
                        text=f"{get_text(context, 'board_message')}\n{format_board(board)}\n\n"
                             f"{get_text(context, 'ai_move', player=ai_player, move=ai_move_idx + 1)}",
                        reply_markup=create_keyboard(board)
                    )

                    if check_winner(board, ai_player):
                        await update.message.reply_text(get_text(context, "player_wins", player=ai_player))
                        update_stats("AI")
                        tx_hash = save_game_result(human_player, ai_player, "AI Win")
                        if tx_hash:
                            await update.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                        else:
                            await update.message.reply_text("Failed to save game result to blockchain.")
                        context.user_data["game_active"] = False
                        await update.message.reply_text(
                            get_text(context, "play_again"),
                            reply_markup=create_play_again_keyboard(context)
                        )
                        return
                    if is_board_full(board):
                        await update.message.reply_text(get_text(context, "draw"))
                        update_stats(None)
                        tx_hash = save_game_result(human_player, ai_player, "Draw")
                        if tx_hash:
                            await update.message.reply_text(f"Game result saved to blockchain, tx hash: {tx_hash}")
                        else:
                            await update.message.reply_text("Failed to save game result to blockchain.")
                        context.user_data["game_active"] = False
                        await update.message.reply_text(
                            get_text(context, "play_again"),
                            reply_markup=create_play_again_keyboard(context)
                        )
                        return
            else:
                await update.message.reply_text(get_text(context, "invalid_move"))
        except ValueError:
            await update.message.reply_text(get_text(context, "invalid_move"))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    logger.info("Starting bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("difficulty", set_difficulty))
    app.add_handler(CommandHandler("language", set_language))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("view_games", view_games))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    logger.info("Bot handlers registered.")
    app.run_polling()

if __name__ == "__main__":
    main()