import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import useAuthStore from "../hooks/useAuth";
import { useGeolocation } from "../hooks/useGeolocation";
import { useWebSocket } from "../hooks/useWebSocket";
import toast from "react-hot-toast";
import {
    Power, PowerOff, Briefcase, Star, Coins, MapPin, Clock
} from "lucide-react";

export default function EmployeeDashboard() {
    const { user } = useAuthStore();
    const [isOnline, setIsOnline] = useState(user?.is_online || false);
    const [jobs, setJobs] = useState([]);
    const [wallet, setWallet] = useState(null);
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);

    const { position } = useGeolocation(isOnline, 15000);
    const token = localStorage.getItem("access_token");

    // Send location updates via WebSocket when online
    const { send } = useWebSocket("/locations/ws", isOnline ? token : null, (data) => {
        // handle location ack
    });

    // Send position when it changes
    useEffect(() => {
        if (position && isOnline) {
            send(position);
            // Also update via REST as fallback
            api.post("/locations/update", position).catch(() => { });
        }
    }, [position, isOnline]);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [jobsRes, walletRes, profileRes] = await Promise.all([
                api.get("/jobs/"),
                api.get("/tokens/wallet"),
                api.get("/users/me/profile"),
            ]);
            setJobs(jobsRes.data);
            setWallet(walletRes.data);
            setProfile(profileRes.data);
        } catch {
            toast.error("Failed to load data");
        } finally {
            setLoading(false);
        }
    };

    const toggleOnline = async () => {
        try {
            const newStatus = !isOnline;
            await api.put("/users/me", { is_online: newStatus });
            setIsOnline(newStatus);
            toast.success(newStatus ? "You are now online! Employers can find you." : "You are now offline.");
        } catch {
            toast.error("Failed to toggle status");
        }
    };

    if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="space-y-6 animate-fade-in pb-20 lg:pb-0">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold">Hello, {user?.full_name} 👋</h1>
                    <p className="text-white/50 mt-1">
                        {isOnline ? "You're visible to employers" : "Toggle online to start receiving jobs"}
                    </p>
                </div>
                <button onClick={toggleOnline}
                    className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all duration-300
            ${isOnline
                            ? "bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 shadow-lg shadow-emerald-500/20"
                            : "bg-white/5 border border-white/10 text-white/60 hover:bg-white/10"
                        }`}>
                    {isOnline ? <Power size={18} /> : <PowerOff size={18} />}
                    {isOnline ? "Online" : "Go Online"}
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                    { label: "Rating", value: profile?.average_rating?.toFixed(1) || "0.0", icon: Star, color: "text-amber-400" },
                    { label: "Jobs Done", value: profile?.total_jobs_completed || 0, icon: Briefcase, color: "text-brand-400" },
                    { label: "Tokens", value: wallet?.balance || 0, icon: Coins, color: "text-amber-400" },
                    { label: "Status", value: isOnline ? "Online" : "Offline", icon: isOnline ? Power : PowerOff, color: isOnline ? "text-emerald-400" : "text-white/40" },
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

            {/* Skills */}
            {profile?.profession_tags?.length > 0 && (
                <div className="glass-card p-4">
                    <h3 className="text-sm font-medium text-white/50 mb-3">Your Skills</h3>
                    <div className="flex flex-wrap gap-2">
                        {profile.profession_tags.map((tag) => (
                            <span key={tag} className="badge-brand">{tag}</span>
                        ))}
                    </div>
                </div>
            )}

            {/* GPS Status */}
            {isOnline && position && (
                <div className="glass-card p-4 flex items-center gap-3">
                    <MapPin size={18} className="text-emerald-400 animate-pulse-soft" />
                    <span className="text-sm text-white/60">
                        GPS active: {position.latitude.toFixed(4)}, {position.longitude.toFixed(4)}
                    </span>
                </div>
            )}

            {/* Jobs */}
            <div>
                <h2 className="text-lg font-semibold mb-4">Your Jobs</h2>
                {jobs.length === 0 ? (
                    <div className="glass-card p-12 text-center">
                        <Briefcase size={48} className="text-white/20 mx-auto mb-4" />
                        <p className="text-white/50">No jobs yet. Go online to receive job requests!</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {jobs.map((job) => (
                            <Link key={job.id} to={`/jobs/${job.id}`} className="glass-card-hover p-4 block">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-medium">{job.title}</h3>
                                        <p className="text-sm text-white/50 mt-1">{job.category}</p>
                                    </div>
                                    <span className={`badge ${job.status === "completed" || job.status === "rated" ? "badge-green" : "badge-brand"}`}>
                                        {job.status}
                                    </span>
                                </div>
                                {job.budget_max && (
                                    <p className="text-sm text-white/40 mt-2">${job.budget_min}–${job.budget_max}</p>
                                )}
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
