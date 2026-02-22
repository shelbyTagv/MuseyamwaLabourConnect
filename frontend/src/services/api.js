/**
 * Axios API client with JWT interceptors.
 */
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "";

const api = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: { "Content-Type": "application/json" },
});

// Attach access token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// Handle 401 – try refresh
api.interceptors.response.use(
    (res) => res,
    async (error) => {
        const orig = error.config;
        if (error.response?.status === 401 && !orig._retry) {
            orig._retry = true;
            const refresh = localStorage.getItem("refresh_token");
            if (refresh) {
                try {
                    const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
                        refresh_token: refresh,
                    });
                    localStorage.setItem("access_token", data.access_token);
                    localStorage.setItem("refresh_token", data.refresh_token);
                    orig.headers.Authorization = `Bearer ${data.access_token}`;
                    return api(orig);
                } catch {
                    localStorage.clear();
                    window.location.href = "/login";
                }
            }
        }
        return Promise.reject(error);
    }
);

export default api;
