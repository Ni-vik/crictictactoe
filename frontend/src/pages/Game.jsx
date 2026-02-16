import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useWebSocket from 'react-use-websocket';
import { useAuth } from '../context/AuthContext';
import { searchPlayers } from '../services/api';
import { Loader, Trophy, X, Send } from 'lucide-react';

const Game = () => {
    const { gameId } = useParams();
    const { token, user } = useAuth();
    const navigate = useNavigate();
    
    const [gameState, setGameState] = useState(null);
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [headers, setHeaders] = useState(null);
    const [winner, setWinner] = useState(null);
    
    // Modal State
    const [showGuessModal, setShowGuessModal] = useState(false);
    const [selectedCell, setSelectedCell] = useState(null);
    const [playerGuess, setPlayerGuess] = useState('');
    const [modalError, setModalError] = useState('');
    
    // Autocomplete State
    const [suggestions, setSuggestions] = useState([]);

    useEffect(() => {
        const delayDebounceFn = setTimeout(async () => {
            if (playerGuess.length >= 2) {
                const results = await searchPlayers(playerGuess);
                setSuggestions(results);
            } else {
                setSuggestions([]);
            }
        }, 300);

        return () => clearTimeout(delayDebounceFn);
    }, [playerGuess]);

    const socketUrl = `wss://crictictactoe.onrender.com/ws/game/${gameId}?token=${token}`;
    
    const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl, {
        onOpen: () => console.log('Connected to Game WS'),
        shouldReconnect: (closeEvent) => true,
    });

    useEffect(() => {
        if (lastMessage !== null) {
            const data = JSON.parse(lastMessage.data);
            handleWebSocketMessage(data);
        }
    }, [lastMessage]);

    const handleWebSocketMessage = (data) => {
        switch (data.type) {
            case 'player_joined':
                setGameState(data.game_state);
                if (data.game_state.grid_headers) {
                    setHeaders(data.game_state.grid_headers);
                }
                addSystemMessage(`${data.username} joined the game`);
                break;
            case 'game_start':
                setHeaders(data.grid_headers);
                setGameState(prevState => ({
                    ...prevState,
                    status: 'in_progress'
                }));
                addSystemMessage(data.message);
                break;
            case 'move_made':
                setGameState(prevState => ({
                    ...prevState,
                    board: data.board,
                    current_turn: data.next_turn,
                    status: data.game_status
                }));
                if (data.winner) {
                    setWinner(data.winner);
                }
                break;
            case 'error':
                if (showGuessModal) {
                    setModalError(data.message);
                } else {
                    alert(data.message); 
                }
                break;
            case 'chat_message':
                setMessages(prev => [...prev, {
                    sender: data.username,
                    text: data.message,
                    timestamp: data.timestamp
                }]);
                break;
            case 'player_disconnected':
                addSystemMessage(`${data.username} disconnected`);
                break;
            default:
                break;
        }
    };

    const addSystemMessage = (text) => {
        setMessages(prev => [...prev, { sender: 'System', text, timestamp: new Date().toISOString() }]);
    };

    const handleCellClick = (index) => {
        if (!gameState) return;
        if (gameState.board[index] !== '') return;
        if (gameState.status !== 'in_progress') return; 
        
        setSelectedCell(index);
        setPlayerGuess('');
        setModalError('');
        setShowGuessModal(true);
    };

    const submitMove = (e) => {
        e.preventDefault();
        sendMessage(JSON.stringify({
            type: 'make_move',
            position: selectedCell,
            player_guess: playerGuess
        }));
    };

    // Close modal if board updates at selected cell
    useEffect(() => {
        if (selectedCell !== null && gameState?.board[selectedCell] !== '') {
            setShowGuessModal(false);
            setSelectedCell(null);
        }
    }, [gameState?.board, selectedCell]);

    const sendChat = (e) => {
        e.preventDefault();
        if (!messageInput.trim()) return;
        sendMessage(JSON.stringify({
            type: 'chat',
            message: messageInput
        }));
        setMessageInput('');
    };

    if (!headers && !gameState) {
        return (
             <div className="game-loading">
                <div className="game-loading-inner">
                    <Loader className="animate-spin" style={{ width: '2.5rem', height: '2.5rem', margin: '0 auto 1rem', color: 'var(--blue-500)' }} />
                    <p>Connecting to Game...</p>
                </div>
            </div>
        );
    }

    const getRowHeader = (idx) => headers?.rows[idx] || `Row ${idx}`;
    const getColHeader = (idx) => headers?.cols[idx] || `Col ${idx}`;

    return (
        <div className="game-page">
            {/* Left Panel: Game Board */}
            <div className="game-board-panel">
                <div className="game-board-container">
                    <div className="game-top-bar">
                        <button onClick={() => navigate('/dashboard')} className="btn-exit">
                            &larr; Forfeit Match
                        </button>
                        <div className="game-status">
                            {winner ? (
                                <span className="status-winner">
                                    <Trophy style={{ width: '1.5rem', height: '1.5rem' }} /> 
                                    {winner === 'draw' ? 'Match Drawn' : 'Match Won!'}
                                </span>
                            ) : (
                                <span className={gameState?.current_turn === user?.user_id ? 'status-your-turn' : 'status-waiting'}>
                                    {gameState?.status === 'waiting' ? 'Waiting for Opponent...' : (gameState?.current_turn === user?.user_id ? 'Your Innings' : 'Opponent Batting')}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Grid */}
                    <div>
                        {/* Column Headers */}
                         <div className="grid-row">
                            <div className="grid-corner"></div>
                            {[0, 1, 2].map(col => (
                                <div key={`col-${col}`} className="grid-col-header">
                                    {getColHeader(col)}
                                </div>
                            ))}
                        </div>

                        {/* Rows */}
                        {[0, 1, 2].map(row => (
                            <div key={`row-${row}`} className="grid-row">
                                {/* Row Header */}
                                <div className="grid-row-header">
                                    {getRowHeader(row)}
                                </div>
                                
                                {[0, 1, 2].map(col => {
                                    const index = row * 3 + col;
                                    const cellValue = gameState?.board[index];
                                    let cellClass = 'cell';
                                    if (cellValue === 'X') cellClass += ' cell--x';
                                    else if (cellValue === 'O') cellClass += ' cell--o';
                                    else if (!winner) cellClass += ' cell--empty';

                                    return (
                                        <button
                                            key={`cell-${index}`}
                                            onClick={() => handleCellClick(index)}
                                            disabled={!!cellValue || !!winner}
                                            className={cellClass}
                                        >
                                            {cellValue}
                                        </button>
                                    );
                                })}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right Panel: Chat */}
            <div className="chat-panel">
                <div className="chat-header">
                    Match Chat
                </div>
                <div className="chat-messages">
                    {messages.map((msg, i) => (
                        <div key={i} className={`chat-msg ${msg.sender === 'System' ? 'chat-msg--system' : 'chat-msg--user'}`}>
                            {msg.sender === 'System' ? (
                                <span className="chat-system-text">{msg.text}</span>
                            ) : (
                                <div className="chat-bubble">
                                    <div className="chat-sender">{msg.sender}</div>
                                    <div className="chat-text">{msg.text}</div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
                <form onSubmit={sendChat} className="chat-form">
                    <input 
                        className="chat-input"
                        placeholder="Type a message..."
                        value={messageInput}
                        onChange={e => setMessageInput(e.target.value)}
                    />
                    <button type="button" onClick={sendChat} className="btn-send">
                        <Send style={{ width: '1rem', height: '1rem' }} />
                    </button>
                </form>
            </div>

            {/* Guess Modal */}
            {showGuessModal && (
                <div className="modal-overlay">
                    <div className="modal-card">
                        <button 
                            onClick={() => {
                                setShowGuessModal(false);
                                setSuggestions([]);
                            }}
                            className="modal-close"
                        >
                            <X style={{ width: '1.5rem', height: '1.5rem' }} />
                        </button>
                        
                        <h3 className="modal-title gradient-text-blue-green">
                            Who is this player?
                        </h3>
                        
                        <div className="modal-criteria">
                            <div className="modal-criteria-row">
                                <span className="criteria-label">Row criteria:</span>
                                <span className="criteria-value--row">{getRowHeader(Math.floor(selectedCell / 3))}</span>
                            </div>
                            <div className="modal-criteria-row">
                                <span className="criteria-label">Col criteria:</span>
                                <span className="criteria-value--col">{getColHeader(selectedCell % 3)}</span>
                            </div>
                        </div>

                        {modalError && (
                             <div className="error-banner">
                                {modalError}
                            </div>
                        )}

                        <form onSubmit={submitMove} className="guess-form">
                            <div className="autocomplete-container">
                                <input
                                    type="text"
                                    value={playerGuess}
                                    onChange={(e) => {
                                        setPlayerGuess(e.target.value);
                                        // Simple debounce handled by useEffect in component body
                                    }}
                                    className="modal-input"
                                    placeholder="Start typing player name..."
                                    autoFocus
                                />
                                {suggestions.length > 0 && (
                                    <ul className="suggestions-list">
                                        {suggestions.map((player, idx) => (
                                            <li 
                                                key={idx} 
                                                onClick={() => {
                                                    setPlayerGuess(player.player_name);
                                                    setSuggestions([]);
                                                }}
                                                className="suggestion-item"
                                            >
                                                <span className="suggestion-name">{player.player_name}</span>
                                                <span className="suggestion-meta">
                                                    {player.country && <span className="tag-country">{player.country}</span>}
                                                    {player.ipl_teams && player.ipl_teams.length > 0 && (
                                                        <span className="tag-team">{player.ipl_teams[0]}</span>
                                                    )}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                            <button
                                type="submit"
                                className="btn-submit-guess"
                            >
                                Submit Guess
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Game;
