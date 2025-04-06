// Home page component
const API_BASE_URL = 'http://localhost:8000/api';

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('authToken');
    if (!token) {
        window.location.href = '/auth.html';
        return false;
    }
    return true;
}

// Get user information
async function getUserInfo() {
    const token = localStorage.getItem('authToken');
    const userId = localStorage.getItem('userId');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/user/${userId}/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Error fetching user info:', error);
        return null;
    }
}

// Initialize the home page
async function initHomePage() {
    if (!checkAuth()) return;
    
    const userInfo = await getUserInfo();
    const app = document.getElementById('app');
    
    app.innerHTML = `
        <div class="home-container">
            <div class="user-info">
                <div class="welcome-message">
                    Welcome, ${userInfo ? userInfo.name : 'User'}!
                </div>
                <button onclick="logout()" class="btn btn-outline-danger btn-sm">Logout</button>
            </div>
            <div class="logo-container">
                <img src="/assets/logo.png" alt="ShopSphere Logo" class="logo">
            </div>
            <h1 class="animated-heading">ShopSphere</h1>
            <p class="subtitle">Your Ultimate Clothing Comparison Platform</p>
            <a href="/search.html" class="btn btn-primary btn-lg start-button">Start Shopping</a>
        </div>
    `;
}

// Add animation to the heading
function animateHeading() {
    const heading = document.querySelector('.animated-heading');
    heading.style.animation = 'fadeInUp 1s ease-out';
}

// Initialize the home page
document.addEventListener('DOMContentLoaded', () => {
    initHomePage();
    animateHeading();
}); 