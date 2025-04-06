import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { logout } from '../services/authService';
import './Home.css';

const Home = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="home-container">
            <div className="sidebar">
                <div className="sidebar-header">
                    <h2>Clothing Comparator</h2>
                </div>
                <div className="search-container">
                    <form onSubmit={handleSearch}>
                        <input
                            type="text"
                            placeholder="Search for clothing..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        <button type="submit">Search</button>
                    </form>
                </div>
                <div className="sidebar-menu">
                    <button onClick={() => navigate('/settings')}>Settings</button>
                    <button onClick={handleLogout}>Logout</button>
                </div>
            </div>
            <div className="main-content">
                <div className="welcome-animation">
                    <h1>Welcome to Clothing Comparator</h1>
                    <p>Start searching for your favorite clothing items!</p>
                </div>
            </div>
        </div>
    );
};

export default Home; 