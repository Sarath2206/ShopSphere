// Authentication page component
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const authError = document.getElementById('authError');

// Handle login form submission
loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const phone = document.getElementById('loginPhone').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ phone, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store the authentication token
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('userId', data.user_id);
            // Redirect to home page
            window.location.href = '/index.html';
        } else {
            showError(data.error || 'Login failed');
        }
    } catch (error) {
        showError('An error occurred during login');
    }
});

// Handle register form submission
registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const phone = document.getElementById('registerPhone').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, phone, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store the authentication token
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('userId', data.user_id);
            // Redirect to home page
            window.location.href = '/index.html';
        } else {
            showError(data.error || 'Registration failed');
        }
    } catch (error) {
        showError('An error occurred during registration');
    }
});

// Show error message
function showError(message) {
    authError.textContent = message;
    authError.style.display = 'block';
    setTimeout(() => {
        authError.style.display = 'none';
    }, 3000);
}

// Check if user is already logged in
function checkAuth() {
    const token = localStorage.getItem('authToken');
    if (token) {
        window.location.href = '/index.html';
    }
}

// Initialize the auth page
document.addEventListener('DOMContentLoaded', checkAuth); 