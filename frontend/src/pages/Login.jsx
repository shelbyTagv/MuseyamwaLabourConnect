import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../hooks/useAuth";
import toast from "react-hot-toast";
import { LogIn, Eye, EyeOff, KeyRound, Loader2, ShieldCheck, Phone } from "lucide-react";

export default function Login() {
    const navigate = useNavigate();
    const { login, verifyFirebase, verifyOtp, resendOtp, loading } = useAuthStore();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPw, setShowPw] = useState(false);

    // OTP step
    const [otpStep, setOtpStep] = useState(false);
    const [authMode, setAuthMode] = useState("otp"); // "firebase" or "otp"
    const [userId, setUserId] = useState(null);
    const [phone, setPhone] = useState("");
    const [otp, setOtp] = useState("");
    const [sending, setSending] = useState(false);
    const confirmationRef = useRef(null);

    const handleCredentials = async (e) => {
        e.preventDefault();
        try {
            const data = await login(email, password);
            if (data.requires_otp) {
                setUserId(data.user_id);
                setPhone(data.phone);
                setAuthMode(data.auth_mode || "otp");
                setOtpStep(true);

                if (data.auth_mode === "firebase") {
                    await handleFirebaseSend(data.phone);
                } else {
                    toast.success(`📲 Verification code sent to ${data.phone}`);
                }
            } else {
                // No OTP required — tokens came directly
                localStorage.setItem("access_token", data.access_token);
                localStorage.setItem("refresh_token", data.refresh_token);
                localStorage.setItem("user", JSON.stringify(data.user));
                useAuthStore.setState({ user: data.user, isAuthenticated: true });
                toast.success(`Welcome back, ${data.user.full_name}!`);
                const dest = data.user.role === "admin" ? "/admin" : data.user.role === "employer" ? "/employer" : "/employee";
                navigate(dest);
            }
        } catch (err) {
            toast.error(err.response?.data?.detail || "Login failed");
        }
    };

    const handleFirebaseSend = async (phoneNumber) => {
        setSending(true);
        try {
            const { setupRecaptcha, sendFirebaseOTP } = await import("../services/firebase");
            setupRecaptcha("verify-btn");
            const confirmation = await sendFirebaseOTP(phoneNumber);
            confirmationRef.current = confirmation;
            toast.success(`📲 Verification code sent to ${phoneNumber}`);
        } catch (err) {
            console.error("Firebase OTP error:", err);
            if (err.code === "auth/too-many-requests") {
                toast.error("Too many attempts. Please try again later.");
            } else if (err.code === "auth/invalid-phone-number") {
                toast.error("Invalid phone number format. Use +263...");
            } else {
                toast.error("Failed to send code. Try again.");
            }
        } finally {
            setSending(false);
        }
    };

    const handleOtpVerify = async (e) => {
        e.preventDefault();
        if (otp.length !== 6) { toast.error("Enter the 6-digit code"); return; }

        try {
            let data;
            if (authMode === "firebase") {
                // Firebase: verify OTP client-side → get Firebase token → send to backend
                if (!confirmationRef.current) {
                    toast.error("Please wait for the code to be sent");
                    return;
                }
                const { confirmOTPAndGetToken } = await import("../services/firebase");
                const firebaseIdToken = await confirmOTPAndGetToken(confirmationRef.current, otp);
                data = await verifyFirebase(userId, firebaseIdToken);
            } else {
                // Fallback: verify OTP directly with backend
                data = await verifyOtp(userId, otp);
            }

            toast.success(`Welcome back, ${data.user.full_name}!`);
            const dest = data.user.role === "admin" ? "/admin" : data.user.role === "employer" ? "/employer" : "/employee";
            navigate(dest);
        } catch (err) {
            console.error("Verify error:", err);
            if (err.code === "auth/invalid-verification-code") {
                toast.error("Wrong code. Please check and try again.");
            } else {
                toast.error(err.response?.data?.detail || "Verification failed");
            }
        }
    };

    const handleResend = async () => {
        if (authMode === "firebase") {
            confirmationRef.current = null;
            await handleFirebaseSend(phone);
        } else {
            try {
                const data = await resendOtp(userId);
                toast.success(data.message);
            } catch { toast.error("Failed to resend code"); }
        }
    };

    return (
        <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4">
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-brand-600/15 rounded-full blur-[100px]" />

            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold gradient-text mb-2">
                        {otpStep ? "Verify Your Phone" : "Welcome Back"}
                    </h1>
                    <p className="text-white/50">
                        {otpStep ? `Enter the code sent to ${phone}` : "Sign in to MuseyamwaLabourConnect"}
                    </p>
                </div>

                {!otpStep ? (
                    <form onSubmit={handleCredentials} className="glass-card p-8 space-y-5">
                        <div>
                            <label className="input-label">Email</label>
                            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                                className="input-field" placeholder="you@example.com" />
                        </div>
                        <div>
                            <label className="input-label">Password</label>
                            <div className="relative">
                                <input type={showPw ? "text" : "password"} required value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="input-field pr-12" placeholder="••••••••" />
                                <button type="button" onClick={() => setShowPw(!showPw)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70">
                                    {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>
                        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                            {loading ? <Loader2 size={18} className="animate-spin" /> : <><LogIn size={18} /> Sign In</>}
                        </button>
                        <p className="text-center text-sm text-white/50">
                            Don't have an account?{" "}
                            <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">Register</Link>
                        </p>
                    </form>
                ) : (
                    <form onSubmit={handleOtpVerify} className="glass-card p-8 space-y-5">
                        <div className="flex items-center justify-center mb-2">
                            <div className="w-16 h-16 rounded-full bg-brand-600/20 flex items-center justify-center">
                                <ShieldCheck size={32} className="text-brand-400" />
                            </div>
                        </div>

                        {sending ? (
                            <div className="text-center py-4">
                                <Loader2 size={24} className="animate-spin mx-auto mb-2 text-brand-400" />
                                <p className="text-sm text-white/50">Sending verification code...</p>
                            </div>
                        ) : (
                            <>
                                <div>
                                    <label className="input-label">6-Digit Verification Code</label>
                                    <input className="input-field text-center text-2xl tracking-[0.5em] font-mono"
                                        placeholder="000000" maxLength={6} value={otp}
                                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} autoFocus />
                                    <p className="text-xs text-white/40 mt-2 text-center flex items-center justify-center gap-1">
                                        <Phone size={12} />
                                        {authMode === "firebase"
                                            ? `SMS sent via Firebase to ${phone}`
                                            : `Check Render logs for the code sent to ${phone}`
                                        }
                                    </p>
                                </div>
                                <button id="verify-btn" type="submit" disabled={loading || otp.length !== 6}
                                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
                                    {loading ? <Loader2 size={18} className="animate-spin" /> : <><KeyRound size={18} /> Verify & Sign In</>}
                                </button>
                            </>
                        )}

                        <div className="flex items-center justify-between text-sm">
                            <button type="button" onClick={handleResend} disabled={sending}
                                className="text-brand-400 hover:text-brand-300 transition-colors disabled:opacity-50">
                                Resend code
                            </button>
                            <button type="button" onClick={() => { setOtpStep(false); setOtp(""); confirmationRef.current = null; }}
                                className="text-white/40 hover:text-white/60 transition-colors">
                                Back to login
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
