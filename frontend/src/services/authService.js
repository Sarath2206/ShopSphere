import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const register = async (userData) => {
    const response = await axios.post(`${API_URL}/register/`, userData);
    return response.data;
};

export const login = async (credentials) => {
    const response = await axios.post(`${API_URL}/login/`, credentials);
    if (response.data.access) {
        localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
};

export const logout = () => {
    localStorage.removeItem('user');
};

export const getCurrentUser = () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
};

export const updateProfile = async (userData) => {
    const user = getCurrentUser();
    const response = await axios.put(
        `${API_URL}/profile/`,
        userData,
        {
            headers: {
                Authorization: `Bearer ${user.access}`
            }
        }
    );
    return response.data;
}; 