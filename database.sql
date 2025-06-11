CREATE TABLE IF NOT EXISTS game_state (
    user_id BIGINT PRIMARY KEY,
    board TEXT NOT NULL,
    move_count INTEGER NOT NULL,
    game_mode TEXT,
    difficulty TEXT,
    human_player TEXT,
    ai_player TEXT,
    ai1_symbol TEXT,
    ai2_symbol TEXT,
    player1_symbol TEXT,
    player2_symbol TEXT
);

CREATE TABLE IF NOT EXISTS game_stats (
    user_id BIGINT PRIMARY KEY,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0
);