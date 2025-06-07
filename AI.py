import json
import os
import logging
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

# Configure logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# File for storing game results
GAME_STORAGE_FILE = "tictactoe_games.json"

# Generate or load RSA key pair
def initialize_keys():
    if not os.path.exists("private_key.pem"):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        with open("private_key.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open("public_key.pem", "wb") as f:
            f.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
    with open("private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    with open("public_key.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
    return private_key, public_key

PRIVATE_KEY, PUBLIC_KEY = initialize_keys()

def sign_game_data(data):
    data_str = json.dumps(data, sort_keys=True)
    signature = PRIVATE_KEY.sign(
        data_str.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return signature.hex()

def verify_game_data(data, signature_hex):
    try:
        data_str = json.dumps(data, sort_keys=True)
        PUBLIC_KEY.verify(
            bytes.fromhex(signature_hex),
            data_str.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def save_game_result(human_player, ai_player, outcome):
    game_data = {
        "timestamp": str(datetime.now()),
        "player_symbol": human_player,
        "ai_symbol": ai_player,
        "outcome": outcome
    }
    signature = sign_game_data(game_data)
    game_entry = {"data": game_data, "signature": signature}
    
    games = []
    if os.path.exists(GAME_STORAGE_FILE):
        with open(GAME_STORAGE_FILE, "r") as f:
            games = json.load(f)
    
    games.append(game_entry)
    with open(GAME_STORAGE_FILE, "w") as f:
        json.dump(games, f, indent=2)
    logger.info(f"Game result saved: {game_data}")