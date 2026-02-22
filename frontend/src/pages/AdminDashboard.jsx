import { useState, useEffect } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import {
    Users, Briefcase, Coins, TrendingUp, Shield, UserCheck, UserX, Eye
} from "lucide-react";

export default function AdminDashboard() {
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [logs, setLogs] = useState([]);
    const [tab, setTab] = useState("overview");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAll();
    }, []);

    const loadAll = async () => {
        try {
            const [statsRes, usersRes, logsRes] = await Promise.all([
                api.get("/admin/dashboard"),
                api.get("/admin/users?size=50"),
                api.get("/admin/audit-logs?size=20"),
            ]);
            setStats(statsRes.data);
            setUsers(usersRes.data);
            setLogs(logsRes.data);
        } catch {
            toast.error("Failed to load admin data");
        } finally {
            setLoading(false);
        }
    };

    const updateUser = async (userId, updates) => {
        try {
            await api.patch(`/admin/users/${userId}`, updates);
            toast.success("User updated");
            loadAll();
        } catch (err) {
            toast.error(err.response?.data?.detail || "Update failed");
        }
    };

    if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="space-y-6 animate-fade-in pb-20 lg:pb-0">
            <div className="flex items-center gap-3 mb-2">
                <Shield size={28} className="text-brand-400" />
                <h1 className="text-2xl font-bold">Admin Dashboard</h1>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2">
                {["overview", "users", "audit"].map((t) => (
                    <button key={t} onClick={() => setTab(t)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium capitalize transition-all
              ${tab === t ? "bg-brand-600/20 text-brand-300 border border-brand-500/30" : "text-white/50 hover:text-white hover:bg-white/5"}`}>
                        {t}
                    </button>
                ))}
            </div>

            {/* Overview */}
            {tab === "overview" && stats && (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { label: "Total Users", value: stats.total_users, icon: Users, color: "text-brand-400" },
                            { label: "Employers", value: stats.total_employers, icon: Briefcase, color: "text-blue-400" },
                            { label: "Workers", value: stats.total_employees, icon: Users, color: "text-teal-400" },
                            { label: "Online Now", value: stats.online_workers, icon: Eye, color: "text-emerald-400" },
                            { label: "Total Jobs", value: stats.total_jobs, icon: Briefcase, color: "text-amber-400" },
                            { label: "Active Jobs", value: stats.active_jobs, icon: TrendingUp, color: "text-orange-400" },
                            { label: "Completed", value: stats.completed_jobs, icon: Briefcase, color: "text-emerald-400" },
                            { label: "Revenue", value: `$${stats.total_revenue_usd.toFixed(2)}`, icon: Coins, color: "text-amber-400" },
                        ].map(({ label, value, icon: Icon, color }) => (
                            <div key={label} className="glass-card p-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center ${color}`}>
                                        <Icon size={20} />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{value}</p>
                                        <p className="text-xs text-white/50">{label}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Users */}
            {tab === "users" && (
                <div className="space-y-3">
                    {users.map((u) => (
                        <div key={u.id} className="glass-card p-4 flex items-center justify-between">
                            <div>
                                <p className="font-medium">{u.full_name}</p>
                                <p className="text-sm text-white/50">{u.email} · <span className="capitalize">{u.role}</span></p>
                            </div>
                            <div className="flex items-center gap-2">
                                {!u.is_verified && (
                                    <button onClick={() => updateUser(u.id, { is_verified: true })}
                                        className="badge-green cursor-pointer hover:opacity-80 flex items-center gap-1">
                                        <UserCheck size={14} /> Verify
                                    </button>
                                )}
                                {u.is_verified && <span className="badge-green">Verified</span>}
                                {u.is_suspended ? (
                                    <button onClick={() => updateUser(u.id, { is_suspended: false })}
                                        className="badge-brand cursor-pointer hover:opacity-80">Unsuspend</button>
                                ) : (
                                    <button onClick={() => updateUser(u.id, { is_suspended: true })}
                                        className="badge-rose cursor-pointer hover:opacity-80 flex items-center gap-1">
                                        <UserX size={14} /> Suspend
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Audit Logs */}
            {tab === "audit" && (
                <div className="space-y-2">
                    {logs.map((log) => (
                        <div key={log.id} className="glass-card p-3 flex items-center justify-between text-sm">
                            <div>
                                <span className="font-medium">{log.action}</span>
                                {log.entity_type && <span className="text-white/40 ml-2">({log.entity_type})</span>}
                            </div>
                            <span className="text-white/30 text-xs">{new Date(log.created_at).toLocaleString()}</span>
                        </div>
                    ))}
                    {logs.length === 0 && <p className="text-white/50 text-center py-8">No audit logs yet</p>}
                </div>
            )}
        </div>
    );
}
