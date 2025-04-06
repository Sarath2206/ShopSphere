import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { getCurrentUser } from './services/authService';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Home from './components/Home';
import Settings from './components/Settings';
import Search from './components/Search';

const PrivateRoute = ({ children }) => {
    const user = getCurrentUser();
    return user ? children : <Navigate to="/login" />;
};

const App = () => {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route
                    path="/home"
                    element={
                        <PrivateRoute>
                            <Home />
                        </PrivateRoute>
                    }
                />
                <Route
                    path="/settings"
                    element={
                        <PrivateRoute>
                            <Settings />
                        </PrivateRoute>
                    }
                />
                <Route
                    path="/search"
                    element={
                        <PrivateRoute>
                            <Search />
                        </PrivateRoute>
                    }
                />
                <Route path="/" element={<Navigate to="/home" />} />
            </Routes>
        </Router>
    );
};

export default App; 