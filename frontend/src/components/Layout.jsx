import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import useAuthStore from "../hooks/useAuth";
import {
    Home, MapPin, MessageCircle, Wallet, User, LogOut,
    Menu, X, Shield, Briefcase, Bell
} from "lucide-react";

const NAV_ITEMS = {
    employer: [
        { to: "/employer", icon: Home, label: "Dashboard" },
        { to: "/employer/map", icon: MapPin, label: "Find Workers" },
        { to: "/tokens", icon: Wallet, label: "Tokens" },
        { to: "/chat", icon: MessageCircle, label: "Messages" },
        { to: "/profile", icon: User, label: "Profile" },
    ],
    employee: [
        { to: "/employee", icon: Home, label: "Dashboard" },
        { to: "/tokens", icon: Wallet, label: "Tokens" },
        { to: "/chat", icon: MessageCircle, label: "Messages" },
        { to: "/profile", icon: User, label: "Profile" },
    ],
    admin: [
        { to: "/admin", icon: Shield, label: "Dashboard" },
        { to: "/tokens", icon: Wallet, label: "Tokens" },
        { to: "/chat", icon: MessageCircle, label: "Messages" },
    ],
};

export default function Layout({ children }) {
    const { user, logout } = useAuthStore();
    const location = useLocation();
    const [mobileOpen, setMobileOpen] = useState(false);
    const items = NAV_ITEMS[user?.role] || [];

    return (
        <div className="min-h-screen bg-surface-950 flex">
            {/* ── Sidebar (desktop) ── */}
            <aside className="hidden lg:flex flex-col w-64 bg-surface-900/80 backdrop-blur-xl border-r border-white/5 p-6">
                <div className="mb-8">
                    <h1 className="text-lg font-bold gradient-text">Museyamwa</h1>
                    <p className="text-xs text-white/40 mt-1">LabourConnect</p>
                </div>

                <nav className="flex-1 space-y-1">
                    {items.map(({ to, icon: Icon, label }) => {
                        const active = location.pathname === to;
                        return (
                            <Link
                                key={to} to={to}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                  ${active
                                        ? "bg-brand-600/20 text-brand-300 border border-brand-500/30"
                                        : "text-white/60 hover:text-white hover:bg-white/5"
                                    }`}
                            >
                                <Icon size={18} />
                                {label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="mt-auto pt-6 border-t border-white/5">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-teal-400 flex items-center justify-center text-sm font-bold">
                            {user?.full_name?.charAt(0)}
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
                            <p className="text-xs text-white/40 capitalize">{user?.role}</p>
                        </div>
                    </div>
                    <button onClick={logout} className="flex items-center gap-2 text-sm text-white/50 hover:text-rose-400 transition-colors w-full">
                        <LogOut size={16} /> Sign Out
                    </button>
                </div>
            </aside>

            {/* ── Mobile header ── */}
            <div className="flex-1 flex flex-col">
                <header className="lg:hidden sticky top-0 z-40 bg-surface-900/90 backdrop-blur-xl border-b border-white/5 px-4 py-3 flex items-center justify-between">
                    <h1 className="text-lg font-bold gradient-text">Museyamwa</h1>
                    <button onClick={() => setMobileOpen(!mobileOpen)} className="text-white/70">
                        {mobileOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </header>

                {/* Mobile nav overlay */}
                {mobileOpen && (
                    <div className="lg:hidden fixed inset-0 z-50 bg-surface-950/95 backdrop-blur-xl p-6 animate-fade-in">
                        <div className="flex justify-end mb-8">
                            <button onClick={() => setMobileOpen(false)} className="text-white/70"><X size={24} /></button>
                        </div>
                        <nav className="space-y-2">
                            {items.map(({ to, icon: Icon, label }) => (
                                <Link
                                    key={to} to={to}
                                    onClick={() => setMobileOpen(false)}
                                    className="flex items-center gap-3 px-4 py-3 text-lg text-white/80 hover:text-white"
                                >
                                    <Icon size={20} /> {label}
                                </Link>
                            ))}
                            <button onClick={logout} className="flex items-center gap-3 px-4 py-3 text-lg text-rose-400 mt-4">
                                <LogOut size={20} /> Sign Out
                            </button>
                        </nav>
                    </div>
                )}

                {/* ── Main Content ── */}
                <main className="flex-1 p-4 lg:p-8 overflow-auto">
                    {children}
                </main>

                {/* ── Bottom nav (mobile) ── */}
                <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-surface-900/95 backdrop-blur-xl border-t border-white/5 flex items-center justify-around py-2 z-40">
                    {items.slice(0, 5).map(({ to, icon: Icon, label }) => {
                        const active = location.pathname === to;
                        return (
                            <Link key={to} to={to} className={`flex flex-col items-center gap-1 py-1 px-3 ${active ? "text-brand-400" : "text-white/50"}`}>
                                <Icon size={20} />
                                <span className="text-[10px]">{label}</span>
                            </Link>
                        );
                    })}
                </nav>
            </div>
        </div>
    );
}
