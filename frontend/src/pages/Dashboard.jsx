import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Copy, Loader, ArrowRight, X } from 'lucide-react';

const Dashboard = () => {
    const { logout, user } = useAuth();
    const navigate = useNavigate();
    
    // UI States
    const [view, setView] = useState('menu'); // menu, create, join
    const [inviteCode, setInviteCode] = useState('');
    const [joinCode, setJoinCode] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    
    // Polling for creator — check if opponent accepted the invite
    useEffect(() => {
        let interval;
        if (view === 'create' && inviteCode) {
            interval = setInterval(async () => {
                try {
                    const res = await api.get(`/invites/${inviteCode}`);
                    if (res.data.game_id) {
                        clearInterval(interval);
                        navigate(`/game/${res.data.game_id}`);
                    }
                } catch (err) {
                    // Backend may return error when status is no longer "pending"
                    // but we still need the game_id to navigate
                }
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [view, inviteCode, navigate]);

    const handleCreateInvite = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await api.post('/invites/create');
            setInviteCode(res.data.invite_id);
            setView('create');
        } catch (err) {
            setError('Failed to create invite');
        } finally {
            setLoading(false);
        }
    };

    const handleJoinGame = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await api.post(`/invites/${joinCode}/accept`);
            const gameId = res.data.game_id;
            navigate(`/game/${gameId}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to join game');
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(inviteCode);
    };

    return (
        <div className="dashboard">
            <div className="dashboard-container">
                {/* Header */}
                <div className="dashboard-header">
                     <h1 className="dashboard-title gradient-text-blue">
                        Tic Tac Toe
                    </h1>
                    <div className="dashboard-user-area">
                        <span className="dashboard-username">Hello, {user?.username}</span>
                        <button 
                            onClick={() => { logout(); navigate('/login'); }}
                            className="btn-logout"
                        >
                            Logout
                        </button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="dashboard-content">
                    {error && (
                        <div className="error-floating">
                            <div className="error-banner">{error}</div>
                        </div>
                    )}

                    {view === 'menu' && (
                        <div className="menu-grid">
                            {/* Create Game Card */}
                            <button 
                                onClick={handleCreateInvite}
                                disabled={loading}
                                className="menu-card menu-card--blue"
                            >
                                <div className="card-overlay" />
                                <div className="card-icon card-icon--blue">
                                    <span>+</span>
                                </div>
                                <h2 className="card-title">Create Match</h2>
                                <p className="card-desc card-desc--blue">Generate an invite code and challenge a friend.</p>
                            </button>

                            {/* Join Game Card */}
                            <button 
                                onClick={() => setView('join')}
                                className="menu-card menu-card--purple"
                            >
                                <div className="card-overlay" />
                                <div className="card-icon card-icon--purple">
                                    <ArrowRight style={{ color: '#fff', width: '2rem', height: '2rem' }} />
                                </div>
                                <h2 className="card-title">Join Match</h2>
                                <p className="card-desc card-desc--purple">Enter an existing invite code to start playing.</p>
                            </button>
                        </div>
                    )}

                    {view === 'create' && (
                        <div className="invite-panel">
                             <div className="invite-spinner-icon">
                                <Loader className="animate-spin" style={{ width: '2rem', height: '2rem' }} />
                             </div>
                             <h2 className="invite-title">Waiting for opponent...</h2>
                             <p className="invite-subtitle">Share this code with your friend</p>
                             
                             <div className="invite-code-box">
                                <span className="invite-code">{inviteCode}</span>
                                <button onClick={copyToClipboard} className="btn-copy">
                                    <Copy style={{ width: '1.25rem', height: '1.25rem' }} />
                                </button>
                             </div>

                             <button 
                                onClick={() => setView('menu')}
                                className="btn-cancel-link"
                             >
                                Cancel
                             </button>
                        </div>
                    )}

                    {view === 'join' && (
                        <div className="invite-panel invite-panel--relative">
                             <button 
                                onClick={() => setView('menu')}
                                className="invite-close-btn"
                             >
                                <X style={{ width: '1.5rem', height: '1.5rem' }} />
                             </button>

                             <h2 className="invite-title">Join Match</h2>
                             
                             <form onSubmit={handleJoinGame} className="join-form">
                                <div>
                                    <label className="join-label">Invite Code</label>
                                    <input
                                        type="text"
                                        value={joinCode}
                                        onChange={(e) => setJoinCode(e.target.value)}
                                        className="join-input"
                                        placeholder="ENTER-CODE"
                                        required
                                    />
                                </div>
                                
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="btn-join"
                                >
                                    {loading ? 'Joining...' : 'Join Game'}
                                </button>
                             </form>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
