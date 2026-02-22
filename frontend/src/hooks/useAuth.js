/**
 * Global auth store using Zustand.
 * Supports two-step login: credentials → OTP verification → tokens.
 */
import { create } from "zustand";
import api from "../services/api";

const useAuthStore = create((set, get) => ({
    user: JSON.parse(localStorage.getItem("user") || "null"),
    isAuthenticated: !!localStorage.getItem("access_token"),
    loading: false,

    // Step 1: Verify credentials → receive user_id + OTP sent
    // Does NOT store tokens yet
    login: async (email, password) => {
        set({ loading: true });
        try {
            const { data } = await api.post("/auth/login", { email, password });
            set({ loading: false });
            return data; // { message, user_id, phone, requires_otp }
        } catch (err) {
            set({ loading: false });
            throw err;
        }
    },

    register: async (payload) => {
        set({ loading: true });
        try {
            const { data } = await api.post("/auth/register", payload);
            set({ loading: false });
            return data; // { message, user_id, phone, requires_otp }
        } catch (err) {
            set({ loading: false });
            throw err;
        }
    },

    // Step 2: Verify OTP → receive tokens → complete login
    verifyOtp: async (userId, otp) => {
        set({ loading: true });
        try {
            const { data } = await api.post(`/auth/verify-login-otp?user_id=${userId}&otp=${otp}`);
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

    // Resend OTP
    resendOtp: async (userId) => {
        const { data } = await api.post(`/auth/resend-otp?user_id=${userId}`);
        return data;
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
