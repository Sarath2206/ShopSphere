import axios from 'axios';
import authService from './authService';

const API_URL = 'http://localhost:8000/api';

export interface SearchFilters {
    size?: string;
    color?: string;
    minPrice?: number;
    maxPrice?: number;
    gender?: string;
    material?: string;
}

export interface ClothingItem {
    id: number;
    source_website: string;
    title: string;
    price: number;
    image_url: string;
    product_url: string;
    size?: string;
    material?: string;
    color?: string;
    brand?: string;
    scraped_at: string;
}

class SearchService {
    private async getAuthHeader() {
        const user = authService.getCurrentUser();
        if (!user) throw new Error('Not authenticated');
        return { Authorization: `Bearer ${user.access}` };
    }

    async search(query: string, filters: SearchFilters = {}): Promise<ClothingItem[]> {
        try {
            const params = new URLSearchParams();
            params.append('query', query);
            if (filters.size) params.append('size', filters.size);
            if (filters.color) params.append('color', filters.color);
            if (filters.minPrice) params.append('min_price', filters.minPrice.toString());
            if (filters.maxPrice) params.append('max_price', filters.maxPrice.toString());
            if (filters.gender) params.append('gender', filters.gender);
            if (filters.material) params.append('material', filters.material);

            const response = await axios.get<{ results: ClothingItem[] }>(
                `${API_URL}/search/?${params.toString()}`
            );
            return response.data.results;
        } catch (error: any) {
            throw error;
        }
    }

    async getSearchHistory(): Promise<ClothingItem[]> {
        try {
            const response = await axios.get<ClothingItem[]>(
                `${API_URL}/items/`,
                { headers: await this.getAuthHeader() }
            );
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 401) {
                try {
                    await authService.refreshToken();
                    const response = await axios.get<ClothingItem[]>(
                        `${API_URL}/items/`,
                        { headers: await this.getAuthHeader() }
                    );
                    return response.data;
                } catch (refreshError) {
                    authService.logout();
                    throw new Error('Session expired. Please login again.');
                }
            }
            throw error;
        }
    }
}

export default new SearchService(); 