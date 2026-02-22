import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import useAuthStore from "../hooks/useAuth";
import toast from "react-hot-toast";
import { UserPlus, Eye, EyeOff, Briefcase, Wrench } from "lucide-react";

export default function Register() {
    const navigate = useNavigate();
    const { register, loading } = useAuthStore();
    const [searchParams] = useSearchParams();
    const [form, setForm] = useState({
        full_name: "",
        email: "",
        phone: "",
        password: "",
        role: searchParams.get("role") || "employee",
    });
    const [showPw, setShowPw] = useState(false);

    const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = await register(form);
            toast.success(`Welcome, ${data.user.full_name}! Purchase tokens to get started.`);
            navigate("/tokens");
        } catch (err) {
            toast.error(err.response?.data?.detail || "Registration failed");
        }
    };

    return (
        <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4 py-12">
            <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-brand-600/15 rounded-full blur-[100px]" />

            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold gradient-text mb-2">Join MuseyamwaLabourConnect</h1>
                    <p className="text-white/50">Create your account</p>
                </div>

                <form onSubmit={handleSubmit} className="glass-card p-8 space-y-5">
                    {/* Role selector */}
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
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <><UserPlus size={18} /> Create Account</>
                        )}
                    </button>

                    <p className="text-center text-sm text-white/50">
                        Already have an account?{" "}
                        <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">Sign In</Link>
                    </p>
                </form>
            </div>
        </div>
    );
}
