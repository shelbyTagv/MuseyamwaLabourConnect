import { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../hooks/useAuth";
import toast from "react-hot-toast";
import { UserPlus, Eye, EyeOff, Briefcase, Wrench, KeyRound, Loader2, ShieldCheck, Phone } from "lucide-react";

export default function Register() {
    const navigate = useNavigate();
    const { register, verifyFirebase, verifyOtp, resendOtp, loading } = useAuthStore();
    const [form, setForm] = useState({
        full_name: "",
        email: "",
        phone: "",
        password: "",
        role: "employee",
    });
    const [showPw, setShowPw] = useState(false);

    // OTP step
    const [otpStep, setOtpStep] = useState(false);
    const [authMode, setAuthMode] = useState("otp");
    const [userId, setUserId] = useState(null);
    const [phone, setPhone] = useState("");
    const [otp, setOtp] = useState("");
    const [sending, setSending] = useState(false);
    const confirmationRef = useRef(null);

    const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = await register(form);
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
                toast.success(`Welcome, ${data.user.full_name}!`);
                navigate("/tokens");
            }
        } catch (err) {
            toast.error(err.response?.data?.detail || "Registration failed");
        }
    };

    const handleFirebaseSend = async (phoneNumber) => {
        setSending(true);
        try {
            const { setupRecaptcha, sendFirebaseOTP } = await import("../services/firebase");
            setupRecaptcha();
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
                if (!confirmationRef.current) {
                    toast.error("Please wait for the code to be sent");
                    return;
                }
                const { confirmOTPAndGetToken } = await import("../services/firebase");
                const firebaseIdToken = await confirmOTPAndGetToken(confirmationRef.current, otp);
                data = await verifyFirebase(userId, firebaseIdToken);
            } else {
                data = await verifyOtp(userId, otp);
            }

            toast.success(`Welcome, ${data.user.full_name}! Your phone is now verified.`);
            navigate("/tokens");
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
        <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4 py-12">
            <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-brand-600/15 rounded-full blur-[100px]" />

            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold gradient-text mb-2">
                        {otpStep ? "Verify Your Phone" : "Join MuseyamwaLabourConnect"}
                    </h1>
                    <p className="text-white/50">
                        {otpStep ? `Enter the code sent to ${phone}` : "Create your account"}
                    </p>
                </div>

                {!otpStep ? (
                    <form onSubmit={handleSubmit} className="glass-card p-8 space-y-5">
                        <div>
                            <label className="input-label">I want to</label>
                            <div className="grid grid-cols-2 gap-3">
                                <button type="button" onClick={() => setForm({ ...form, role: "employer" })}
                                    className={`flex items-center justify-center gap-2 py-3 rounded-xl border text-sm font-medium transition-all
                  ${form.role === "employer"
                                            ? "bg-brand-600/20 border-brand-500/50 text-brand-300"
                                            : "bg-white/5 border-white/10 text-white/60 hover:bg-white/10"}`}>
                                    <Briefcase size={18} /> Hire Workers
                                </button>
                                <button type="button" onClick={() => setForm({ ...form, role: "employee" })}
                                    className={`flex items-center justify-center gap-2 py-3 rounded-xl border text-sm font-medium transition-all
                  ${form.role === "employee"
                                            ? "bg-brand-600/20 border-brand-500/50 text-brand-300"
                                            : "bg-white/5 border-white/10 text-white/60 hover:bg-white/10"}`}>
                                    <Wrench size={18} /> Find Work
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="input-label">Full Name</label>
                            <input type="text" required value={form.full_name} onChange={update("full_name")}
                                className="input-field" placeholder="John Doe" />
                        </div>
                        <div>
                            <label className="input-label">Email</label>
                            <input type="email" required value={form.email} onChange={update("email")}
                                className="input-field" placeholder="you@example.com" />
                        </div>
                        <div>
                            <label className="input-label">Phone (Zimbabwe)</label>
                            <input type="tel" required value={form.phone} onChange={update("phone")}
                                className="input-field" placeholder="+263771234567" />
                            <p className="text-xs text-white/40 mt-1">We'll send a verification code to this number</p>
                        </div>
                        <div>
                            <label className="input-label">Password</label>
                            <div className="relative">
                                <input type={showPw ? "text" : "password"} required minLength={8}
                                    value={form.password} onChange={update("password")}
                                    className="input-field pr-12" placeholder="Min 8 characters" />
                                <button type="button" onClick={() => setShowPw(!showPw)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70">
                                    {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>

                        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                            {loading ? <Loader2 size={18} className="animate-spin" /> : <><UserPlus size={18} /> Create Account</>}
                        </button>

                        <p className="text-center text-sm text-white/50">
                            Already have an account?{" "}
                            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">Sign In</Link>
                        </p>
                    </form>
                ) : (
                    <form onSubmit={handleOtpVerify} className="glass-card p-8 space-y-5">
                        <div className="flex items-center justify-center mb-2">
                            <div className="w-16 h-16 rounded-full bg-brand-600/20 flex items-center justify-center">
                                <ShieldCheck size={32} className="text-brand-400" />
                            </div>
                        </div>

                        <p className="text-sm text-white/50 text-center">
                            A 6-digit verification code has been sent to confirm your phone number.
                        </p>

                        {sending ? (
                            <div className="text-center py-4">
                                <Loader2 size={24} className="animate-spin mx-auto mb-2 text-brand-400" />
                                <p className="text-sm text-white/50">Sending verification code...</p>
                            </div>
                        ) : (
                            <>
                                <div>
                                    <label className="input-label">Verification Code</label>
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
                                    {loading ? <Loader2 size={18} className="animate-spin" /> : <><KeyRound size={18} /> Verify & Continue</>}
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
                                Back
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
