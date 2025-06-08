const { useState, useEffect } = React;
const ReactDOM = window.ReactDOM;

const translations = {
    ru: {
        welcome_message: "Добро пожаловать в Крестики-Нолики! 🎮\nВыберите режим игры:",
        game_start: "Игра начинается! Вы - {player}, ИИ - {opponent}. Ваш ход!",
        invalid_move: "Неверный ход! Выберите другую клетку.",
        player_wins: "{player} побеждает! 🏆",
        draw: "Ничья! 🤝",
        play_again: "Сыграть еще?",
        yes_button: "Да",
        no_button: "Нет",
        ai_thinking: "ИИ думает...",
        connect_wallet: "Подключить кошелек",
        web3_mode: "Веб3 игра",
        choose_symbol: "Выберите символ: X или O",
        board_message: "Текущая доска:",
        ai_move: "ИИ ({player}) ходит на позицию {move}."
    },
    en: {
        welcome_message: "Welcome to Tic-Tac-Toe! 🎮\nChoose a game mode:",
        game_start: "Game starts! You are {player}, AI is {opponent}. Your turn!",
        invalid_move: "Invalid move! Try another cell.",
        player_wins: "{player} wins! 🏆",
        draw: "It's a draw! 🤝",
        play_again: "Play again?",
        yes_button: "Yes",
        no_button: "No",
        ai_thinking: "AI is thinking...",
        connect_wallet: "Connect Wallet",
        web3_mode: "Web3 Game",
        choose_symbol: "Choose symbol: X or O",
        board_message: "Current board:",
        ai_move: "AI ({player}) moves to position {move}."
    },
    ja: {
        welcome_message: "tic-tac-toeへようこそ！ 🎮\nゲームモードを選択してください：",
        game_start: "ゲーム開始！あなたは{player}、AIは{opponent}です。あなたのターン！",
        invalid_move: "無効な動きです！別のセルを試してください。",
        player_wins: "{player}が勝ちました！ 🏆",
        draw: "引き分けです！ 🤝",
        play_again: "もう一度プレイしますか？",
        yes_button: "はい",
        no_button: "いいえ",
        ai_thinking: "AIが考えています...",
        connect_wallet: "ウォレットを接続",
        web3_mode: "Web3ゲーム",
        choose_symbol: "シンボルを選択してください：XまたはO",
        board_message: "現在のボード:",
        ai_move: "AI ({player}) がポジション {move} に移動しました。"
    },
    it: {
        welcome_message: "Benvenuto a Tris! 🎮\nScegli una modalità di gioco:",
        game_start: "Il gioco inizia! Tu sei {player}, l'IA è {opponent}. Tocca a te!",
        invalid_move: "Mossa non valida! Prova un'altra cella.",
        player_wins: "{player} vince! 🏆",
        draw: "È un pareggio! 🤝",
        play_again: "Giocare di nuovo?",
        yes_button: "Sì",
        no_button: "No",
        ai_thinking: "L'IA sta pensando...",
        connect_wallet: "Collega il portafoglio",
        web3_mode: "Gioco Web3",
        choose_symbol: "Scegli il simbolo: X o O",
        board_message: "Tavolo attuale:",
        ai_move: "L'IA ({player}) si muove alla posizione {move}."
    },
    hi: {
        welcome_message: "टिक-टैक-टो में आपका स्वागत है! 🎮\nखेल मोड चुनें:",
        game_start: "खेल शुरू! आप {player} हैं, AI {opponent} है। आपकी बारी!",
        invalid_move: "अमान्य चाल! दूसरी सेल आज़माएं।",
        player_wins: "{player} जीत गया! 🏆",
        draw: "यह ड्रॉ है! 🤝",
        play_again: "फिर से खेलें?",
        yes_button: "हां",
        no_button: "नहीं",
        ai_thinking: "AI सो सप है...",
        connect_wallet: "वॉलेट कनेक्ट करें",
        web3_mode: "वेब3 गेम",
        choose_symbol: "प्रतीक चुनें: X या O",
        board_message: "वर्तमान बोर्ड:",
        ai_move: "AI ({player}) ने स्थिति {move} पर चाल चली।"
    }
};

const getText = (key, lang = 'en', params = {}) => {
    let text = translations[lang][key] || key;
    Object.keys(params).forEach(k => text = text.replace(`{${k}}`, params[k]));
    return text;
};

const TicTacToe = () => {
    const [board, setBoard] = useState(Array(9).fill(" "));
    const [gameActive, setGameActive] = useState(false);
    const [humanPlayer, setHumanPlayer] = useState("X");
    const [aiPlayer, setAiPlayer] = useState("O");
    const [gameMode, setGameMode] = useState(null);
    const [walletConnected, setWalletConnected] = useState(false);
    const [account, setAccount] = useState(null);
    const [web3, setWeb3] = useState(null);
    const [contract, setContract] = useState(null);
    const [message, setMessage] = useState(getText("welcome_message"));
    const [language, setLanguage] = useState("en");
    const [difficulty] = useState("medium");

    const contractABI = [
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
    ];
    const contractAddress = "0xYourContractAddressHere"; // Replace with actual contract address

    useEffect(() => {
        if (window.ethereum) {
            const web3Instance = new Web3(window.ethereum);
            setWeb3(web3Instance);
            const contractInstance = new web3Instance.eth.Contract(contractABI, contractAddress);
            setContract(contractInstance);
        }
    }, []);

    const connectWallet = async () => {
        if (window.ethereum) {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                setAccount(accounts[0]);
                setWalletConnected(true);
                setMessage(getText("web3_mode", language));
            } catch (error) {
                console.error("Wallet connection failed:", error);
                setMessage("Failed to connect wallet.");
            }
        } else {
            setMessage("Please install MetaMask!");
        }
    };

    const checkWinner = (board, player) => {
        const wins = [[0,1,2], [3,4,5], [6,7,8], [0,3,6], [1,4,7], [2,5,8], [0,4,8], [2,4,6]];
        return wins.some(([a, b, c]) => board[a] === player && board[b] === player && board[c] === player);
    };

    const isBoardFull = (board) => !board.includes(" ");

    const getAvailableMoves = (board) => board.map((spot, i) => spot === " " ? i : null).filter(i => i !== null);

    const aiMove = (board, player) => {
        const opponent = player === "X" ? "O" : "X";
        if (difficulty === "easy") {
            return getAvailableMoves(board)[Math.floor(Math.random() * getAvailableMoves(board).length)];
        } else {
            let bestScore = player === "O" ? -Infinity : Infinity;
            let bestMoves = [];
            for (let move of getAvailableMoves(board)) {
                board[move] = player;
                let score = minimax(board, 0, player === "X", player, opponent);
                board[move] = " ";
                if (player === "O" && score > bestScore) {
                    bestScore = score;
                    bestMoves = [move];
                } else if (player === "X" && score < bestScore) {
                    bestScore = score;
                    bestMoves = [move];
                } else if (score === bestScore) {
                    bestMoves.push(move);
                }
            }
            return bestMoves[Math.floor(Math.random() * bestMoves.length)];
        }
    };

    const minimax = (board, depth, isMaximizing, player, opponent) => {
        if (checkWinner(board, "O")) return 1;
        if (checkWinner(board, "X")) return -1;
        if (isBoardFull(board)) return 0;

        if (isMaximizing) {
            let bestScore = -Infinity;
            for (let move of getAvailableMoves(board)) {
                board[move] = player;
                let score = minimax(board, depth + 1, false, player, opponent);
                board[move] = " ";
                bestScore = Math.max(bestScore, score);
            }
            return bestScore;
        } else {
            let bestScore = Infinity;
            for (let move of getAvailableMoves(board)) {
                board[move] = opponent;
                let score = minimax(board, depth + 1, true, player, opponent);
                board[move] = " ";
                bestScore = Math.min(bestScore, score);
            }
            return bestScore;
        }
    };

    const saveGameResult = async (playerSymbol, aiSymbol, outcome) => {
        if (contract && account) {
            try {
                await contract.methods.saveGameResult(playerSymbol, aiSymbol, outcome)
                    .send({ from: account });
                console.log("Game result saved to blockchain");
            } catch (error) {
                console.error("Error saving game result:", error);
            }
        }
    };

    const handleMove = async (index) => {
        if (!gameActive || board[index] !== " " || !walletConnected) return;

        const newBoard = [...board];
        newBoard[index] = humanPlayer;
        setBoard(newBoard);

        if (checkWinner(newBoard, humanPlayer)) {
            setMessage(getText("player_wins", language, { player: humanPlayer }));
            setGameActive(false);
            await saveGameResult(humanPlayer, aiPlayer, "Human Win");
            return;
        }
        if (isBoardFull(newBoard)) {
            setMessage(getText("draw", language));
            setGameActive(false);
            await saveGameResult(humanPlayer, aiPlayer, "Draw");
            return;
        }

        setMessage(getText("ai_thinking", language));
        setTimeout(() => {
            const aiMoveIndex = aiMove(newBoard, aiPlayer);
            newBoard[aiMoveIndex] = aiPlayer;
            setBoard(newBoard);
            setMessage(getText("ai_move", language, { player: aiPlayer, move: aiMoveIndex + 1 }));

            if (checkWinner(newBoard, aiPlayer)) {
                setMessage(getText("player_wins", language, { player: aiPlayer }));
                setGameActive(false);
                saveGameResult(humanPlayer, aiPlayer, "AI Win");
                return;
            }
            if (isBoardFull(newBoard)) {
                setMessage(getText("draw", language));
                setGameActive(false);
                saveGameResult(humanPlayer, aiPlayer, "Draw");
                return;
            }
        }, 1000);
    };

    const startGame = (symbol) => {
        setHumanPlayer(symbol);
        setAiPlayer(symbol === "X" ? "O" : "X");
        setBoard(Array(9).fill(" "));
        setGameActive(true);
        setGameMode("web3");
        setMessage(getText("game_start", language, { player: symbol, opponent: symbol === "X" ? "O" : "X" }));
    };

    const resetGame = () => {
        setBoard(Array(9).fill(" "));
        setGameActive(true);
        setMessage(getText("game_start", language, { player: humanPlayer, opponent: aiPlayer }));
    };

    const changeLanguage = (lang) => {
        setLanguage(lang);
        setMessage(getText("welcome_message", lang));
    };

    return React.createElement(
        'div',
        { className: 'flex flex-col items-center justify-center min-h-screen p-4' },
        React.createElement('h1', { className: 'text-4xl font-bold mb-6' }, 'Tic-Tac-Toe Web3'),
        React.createElement(
            'div',
            { className: 'mb-4' },
            React.createElement(
                'select',
                {
                    onChange: (e) => changeLanguage(e.target.value),
                    className: 'bg-gray-800 text-white p-2 rounded'
                },
                React.createElement('option', { value: 'en' }, 'English'),
                React.createElement('option', { value: 'ru' }, 'Русский'),
                React.createElement('option', { value: 'ja' }, '日本語'),
                React.createElement('option', { value: 'it' }, 'Italiano'),
                React.createElement('option', { value: 'hi' }, 'हिन्दी')
            )
        ),
        !walletConnected
            ? React.createElement(
                  'button',
                  {
                      onClick: connectWallet,
                      className: 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4'
                  },
                  getText("connect_wallet", language)
              )
            : !gameActive && !gameMode
            ? React.createElement(
                  'div',
                  { className: 'flex flex-col space-y-4' },
                  React.createElement('h2', { className: 'text-2xl' }, getText("choose_symbol", language)),
                  React.createElement(
                      'button',
                      {
                          onClick: () => startGame("X"),
                          className: 'bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded'
                      },
                      'X'
                  ),
                  React.createElement(
                      'button',
                      {
                          onClick: () => startGame("O"),
                          className: 'bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded'
                      },
                      'O'
                  )
              )
            : React.createElement(
                  'div',
                  { className: 'text-center' },
                  React.createElement(
                      'div',
                      { className: 'grid grid-cols-3 gap-2 w-64 mx-auto mb-4' },
                      board.map((cell, i) =>
                          React.createElement(
                              'button',
                              {
                                  key: i,
                                  onClick: () => handleMove(i),
                                  className: 'w-20 h-20 bg-gray-800 text-2xl font-bold flex items-center justify-center rounded',
                                  disabled: cell !== " " || !gameActive
                              },
                              cell
                          )
                      )
                  ),
                  React.createElement('p', { className: 'text-lg mb-4' }, message),
                  gameActive
                      ? null
                      : React.createElement(
                            'button',
                            {
                                onClick: resetGame,
                                className: 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
                            },
                            getText("play_again", language)
                        )
              )
    );
};

ReactDOM.render(React.createElement(TicTacToe), document.getElementById('root'));