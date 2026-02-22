import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../hooks/useAuth";
import toast from "react-hot-toast";
import { LogIn, Eye, EyeOff } from "lucide-react";

export default function Login() {
    const navigate = useNavigate();
    const { login, loading } = useAuthStore();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPw, setShowPw] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = await login(email, password);
            toast.success(`Welcome back, ${data.user.full_name}!`);
            const dest = data.user.role === "admin" ? "/admin" : data.user.role === "employer" ? "/employer" : "/employee";
            navigate(dest);
        } catch (err) {
            toast.error(err.response?.data?.detail || "Login failed");
        }
    };

    return (
        <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4">
            {/* Background glow */}
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-brand-600/15 rounded-full blur-[100px]" />

            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold gradient-text mb-2">Welcome Back</h1>
                    <p className="text-white/50">Sign in to MuseyamwaLabourConnect</p>
                </div>

                <form onSubmit={handleSubmit} className="glass-card p-8 space-y-5">
                    <div>
                        <label className="input-label">Email</label>
                        <input
                            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                            className="input-field" placeholder="you@example.com"
                        />
                    </div>

                    <div>
                        <label className="input-label">Password</label>
                        <div className="relative">
                            <input
                                type={showPw ? "text" : "password"} required value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="input-field pr-12" placeholder="••••••••"
                            />
                            <button type="button" onClick={() => setShowPw(!showPw)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70">
                                {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <><LogIn size={18} /> Sign In</>
                        )}
                    </button>

                    <p className="text-center text-sm text-white/50">
                        Don't have an account?{" "}
                        <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">Register</Link>
                    </p>
                </form>
            </div>
        </div>
    );
}
