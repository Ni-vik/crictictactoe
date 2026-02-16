import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000', // Adjust if backend runs on different port
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Search players
export const searchPlayers = async (query) => {
    try {
        const response = await api.get(`/players/search?q=${encodeURIComponent(query)}`);
        return response.data;
    } catch (error) {
        console.error("Search failed", error);
        return [];
    }
};

export default api;
