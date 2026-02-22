/**
 * Firebase configuration for Phone Auth.
 *
 * SETUP:
 * 1. Go to https://console.firebase.google.com
 * 2. Create a project (or reuse one)
 * 3. Enable Authentication → Phone sign-in method
 * 4. Copy your config values into the .env file:
 *    VITE_FIREBASE_API_KEY=...
 *    VITE_FIREBASE_AUTH_DOMAIN=...
 *    VITE_FIREBASE_PROJECT_ID=...
 *    VITE_FIREBASE_APP_ID=...
 */

import { initializeApp } from "firebase/app";
import {
    getAuth,
    RecaptchaVerifier,
    signInWithPhoneNumber,
} from "firebase/auth";

const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

/**
 * Set up an invisible reCAPTCHA on a button.
 * Call this once when the OTP step mounts.
 *
 * @param {string} buttonId - The id of the "send code" / "verify" button
 * @returns {RecaptchaVerifier}
 */
export function setupRecaptcha(buttonId) {
    if (window.recaptchaVerifier) {
        window.recaptchaVerifier.clear();
    }
    window.recaptchaVerifier = new RecaptchaVerifier(auth, buttonId, {
        size: "invisible",
        callback: () => {
            // reCAPTCHA solved — allow signInWithPhoneNumber
        },
    });
    return window.recaptchaVerifier;
}

/**
 * Send OTP to a phone number via Firebase.
 *
 * @param {string} phoneNumber - E.164 format, e.g. "+263771234567"
 * @returns {ConfirmationResult} — call .confirm(code) to verify
 */
export async function sendFirebaseOTP(phoneNumber) {
    const appVerifier = window.recaptchaVerifier;
    if (!appVerifier) throw new Error("reCAPTCHA not initialized");
    const confirmationResult = await signInWithPhoneNumber(auth, phoneNumber, appVerifier);
    return confirmationResult;
}

/**
 * After user enters the 6-digit code, confirm it and get the Firebase ID token.
 *
 * @param {ConfirmationResult} confirmationResult
 * @param {string} code - The 6-digit OTP entered by the user
 * @returns {string} Firebase ID token to send to your backend
 */
export async function confirmOTPAndGetToken(confirmationResult, code) {
    const result = await confirmationResult.confirm(code);
    const idToken = await result.user.getIdToken();
    return idToken;
}

export { auth };
