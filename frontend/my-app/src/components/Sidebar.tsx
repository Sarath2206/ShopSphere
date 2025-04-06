import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const Sidebar: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <h2>ShopSphere</h2>
                {user && <p className="user-email">{user.email}</p>}
            </div>
            <nav className="sidebar-nav">
                <Link to="/" className="nav-item">
                    <i className="fas fa-home"></i>
                    <span>Home</span>
                </Link>
                <Link to="/search" className="nav-item">
                    <i className="fas fa-search"></i>
                    <span>Search</span>
                </Link>
                <Link to="/history" className="nav-item">
                    <i className="fas fa-history"></i>
                    <span>Search History</span>
                </Link>
                <Link to="/settings" className="nav-item">
                    <i className="fas fa-cog"></i>
                    <span>Settings</span>
                </Link>
                <button onClick={handleLogout} className="nav-item logout-button">
                    <i className="fas fa-sign-out-alt"></i>
                    <span>Logout</span>
                </button>
            </nav>
        </div>
    );
};

export default Sidebar; 