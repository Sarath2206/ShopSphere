import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterData extends LoginCredentials {
    username: string;
    phone_number?: string;
}

export interface AuthResponse {
    access: string;
    refresh: string;
}

class AuthService {
    async login(credentials: LoginCredentials): Promise<AuthResponse> {
        const response = await axios.post(`${API_URL}/auth/token/`, credentials);
        if (response.data.access) {
            localStorage.setItem('user', JSON.stringify(response.data));
        }
        return response.data;
    }

    async register(data: RegisterData): Promise<void> {
        await axios.post(`${API_URL}/auth/register/`, data);
    }

    logout(): void {
        localStorage.removeItem('user');
    }

    getCurrentUser(): AuthResponse | null {
        const userStr = localStorage.getItem('user');
        if (userStr) return JSON.parse(userStr);
        return null;
    }

    async refreshToken(): Promise<string> {
        const user = this.getCurrentUser();
        if (!user) throw new Error('No user logged in');
        
        const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: user.refresh
        });
        
        if (response.data.access) {
            const newUser = { ...user, access: response.data.access };
            localStorage.setItem('user', JSON.stringify(newUser));
            return response.data.access;
        }
        throw new Error('Failed to refresh token');
    }
}

export default new AuthService(); 