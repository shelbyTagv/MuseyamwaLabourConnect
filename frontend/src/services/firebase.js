/**
 * Firebase configuration for Phone Auth.
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

// ── DEBUG: Log Firebase config on load ──
console.log("🔍 FIREBASE CONFIG DEBUG:");
console.log("  apiKey:", firebaseConfig.apiKey ? "✅ SET (" + firebaseConfig.apiKey.substring(0, 10) + "...)" : "❌ MISSING");
console.log("  authDomain:", firebaseConfig.authDomain || "❌ MISSING");
console.log("  projectId:", firebaseConfig.projectId || "❌ MISSING");
console.log("  appId:", firebaseConfig.appId ? "✅ SET" : "❌ MISSING");

if (!firebaseConfig.apiKey || !firebaseConfig.projectId) {
    console.error("❌ FIREBASE: Missing required config! Add VITE_FIREBASE_* env vars to Vercel.");
}

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
console.log("🔍 FIREBASE: App initialized, auth ready");

/**
 * Set up an invisible reCAPTCHA on a button.
 */
export function setupRecaptcha(buttonId) {
    console.log(`🔍 FIREBASE: setupRecaptcha("${buttonId}")`);
    try {
        if (window.recaptchaVerifier) {
            console.log("🔍 FIREBASE: Clearing old reCAPTCHA verifier");
            window.recaptchaVerifier.clear();
        }
        const btn = document.getElementById(buttonId);
        console.log(`🔍 FIREBASE: Button #${buttonId} found:`, !!btn);

        window.recaptchaVerifier = new RecaptchaVerifier(auth, buttonId, {
            size: "invisible",
            callback: () => {
                console.log("✅ FIREBASE: reCAPTCHA solved!");
            },
            "expired-callback": () => {
                console.warn("⚠️ FIREBASE: reCAPTCHA expired");
            },
        });
        console.log("✅ FIREBASE: RecaptchaVerifier created successfully");
        return window.recaptchaVerifier;
    } catch (err) {
        console.error("❌ FIREBASE: setupRecaptcha FAILED:", err.code, err.message);
        throw err;
    }
}

/**
 * Send OTP to a phone number via Firebase.
 */
export async function sendFirebaseOTP(phoneNumber) {
    console.log(`🔍 FIREBASE: sendFirebaseOTP("${phoneNumber}")`);
    const appVerifier = window.recaptchaVerifier;
    if (!appVerifier) {
        console.error("❌ FIREBASE: reCAPTCHA not initialized! Call setupRecaptcha first.");
        throw new Error("reCAPTCHA not initialized");
    }
    try {
        console.log("🔍 FIREBASE: Calling signInWithPhoneNumber...");
        const confirmationResult = await signInWithPhoneNumber(auth, phoneNumber, appVerifier);
        console.log("✅ FIREBASE: SMS sent successfully! Confirmation result received.");
        return confirmationResult;
    } catch (err) {
        console.error("❌ FIREBASE: signInWithPhoneNumber FAILED:");
        console.error("  Code:", err.code);
        console.error("  Message:", err.message);
        console.error("  Full error:", err);
        throw err;
    }
}

/**
 * Confirm OTP code and get Firebase ID token.
 */
export async function confirmOTPAndGetToken(confirmationResult, code) {
    console.log(`🔍 FIREBASE: confirmOTPAndGetToken(code="${code}")`);
    try {
        const result = await confirmationResult.confirm(code);
        console.log("✅ FIREBASE: Code confirmed! Getting ID token...");
        const idToken = await result.user.getIdToken();
        console.log("✅ FIREBASE: Got ID token (length:", idToken.length, ")");
        return idToken;
    } catch (err) {
        console.error("❌ FIREBASE: confirmOTP FAILED:");
        console.error("  Code:", err.code);
        console.error("  Message:", err.message);
        throw err;
    }
}

export { auth };
