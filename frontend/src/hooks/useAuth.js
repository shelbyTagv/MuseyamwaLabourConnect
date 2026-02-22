/**
 * Global auth store using Zustand.
 * Supports dual-mode verification:
 *   - "firebase": Firebase Phone Auth (SMS via Firebase)
 *   - "otp": Fallback console-logged OTP (when Firebase not configured)
 */
import { create } from "zustand";
import api from "../services/api";

const useAuthStore = create((set, get) => ({
    user: JSON.parse(localStorage.getItem("user") || "null"),
    isAuthenticated: !!localStorage.getItem("access_token"),
    loading: false,

    // Step 1: Verify credentials → receive user_id + phone + auth_mode
    login: async (email, password) => {
        set({ loading: true });
        try {
            const { data } = await api.post("/auth/login", { email, password });
            set({ loading: false });
            return data; // { message, user_id, phone, requires_otp, auth_mode }
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
            return data; // { message, user_id, phone, requires_otp, auth_mode }
        } catch (err) {
            set({ loading: false });
            throw err;
        }
    },

    // Step 2a: Verify with Firebase ID token (firebase mode)
    verifyFirebase: async (userId, firebaseIdToken) => {
        set({ loading: true });
        try {
            const { data } = await api.post("/auth/verify-firebase", {
                user_id: userId,
                firebase_id_token: firebaseIdToken,
            });
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

    // Step 2b: Verify with console OTP (fallback mode)
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

    // Resend OTP (fallback mode only)
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
