/**
 * Global auth store using Zustand.
 */
import { create } from "zustand";
import api from "../services/api";

const useAuthStore = create((set, get) => ({
    user: JSON.parse(localStorage.getItem("user") || "null"),
    isAuthenticated: !!localStorage.getItem("access_token"),
    loading: false,

    login: async (email, password) => {
        set({ loading: true });
        try {
            const { data } = await api.post("/auth/login", { email, password });
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            set({ user: data.user, isAuthenticated: true, loading: false });
            return data;
        } catch (err) {
            set({ loading: false });
            throw err;
        }
    },

    register: async (payload) => {
        set({ loading: true });
        try {
            const { data } = await api.post("/auth/register", payload);
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            set({ user: data.user, isAuthenticated: true, loading: false });
            return data;
        } catch (err) {
            set({ loading: false });
            throw err;
        }
    },

    logout: () => {
        localStorage.clear();
        set({ user: null, isAuthenticated: false });
        window.location.href = "/login";
    },

    refreshUser: async () => {
        try {
            const { data } = await api.get("/auth/me");
            localStorage.setItem("user", JSON.stringify(data));
            set({ user: data });
        } catch {
            // ignore
        }
    },
}));

export default useAuthStore;
