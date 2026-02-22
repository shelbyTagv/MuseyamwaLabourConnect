import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import useAuthStore from "../hooks/useAuth";
import toast from "react-hot-toast";
import {
    Plus, MapPin, Briefcase, Clock, CheckCircle2, AlertCircle, Coins
} from "lucide-react";

const STATUS_COLORS = {
    requested: "badge-brand",
    offered: "badge-gold",
    assigned: "badge-blue",
    en_route: "badge-gold",
    on_site: "badge-green",
    completed: "badge-green",
    rated: "badge-green",
    cancelled: "badge-rose",
    disputed: "badge-rose",
};

export default function EmployerDashboard() {
    const { user } = useAuthStore();
    const [jobs, setJobs] = useState([]);
    const [wallet, setWallet] = useState(null);
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({ title: "", description: "", category: "", budget_min: "", budget_max: "" });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [jobsRes, walletRes] = await Promise.all([
                api.get("/jobs/"),
                api.get("/tokens/wallet"),
            ]);
            setJobs(jobsRes.data);
            setWallet(walletRes.data);
        } catch (err) {
            toast.error("Failed to load data");
        } finally {
            setLoading(false);
        }
    };

    const createJob = async (e) => {
        e.preventDefault();
        try {
            await api.post("/jobs/", {
                ...form,
                budget_min: form.budget_min ? Number(form.budget_min) : null,
                budget_max: form.budget_max ? Number(form.budget_max) : null,
            });
            toast.success("Job posted!");
            setShowCreate(false);
            setForm({ title: "", description: "", category: "", budget_min: "", budget_max: "" });
            loadData();
        } catch (err) {
            toast.error(err.response?.data?.detail || "Failed to create job");
        }
    };

    if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="space-y-6 animate-fade-in pb-20 lg:pb-0">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold">Welcome, {user?.full_name} 👋</h1>
                    <p className="text-white/50 mt-1">Manage your jobs and find workers</p>
                </div>
                <div className="flex items-center gap-3">
                    <Link to="/tokens" className="glass-card px-4 py-2 flex items-center gap-2 text-sm">
                        <Coins size={16} className="text-amber-400" />
                        <span className="font-semibold">{wallet?.balance || 0}</span> tokens
                    </Link>
                    <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
                        <Plus size={18} /> Post Job
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                    { label: "Total Jobs", value: jobs.length, icon: Briefcase, color: "text-brand-400" },
                    { label: "Active", value: jobs.filter(j => ["requested", "offered", "assigned", "en_route", "on_site"].includes(j.status)).length, icon: Clock, color: "text-amber-400" },
                    { label: "Completed", value: jobs.filter(j => ["completed", "rated"].includes(j.status)).length, icon: CheckCircle2, color: "text-emerald-400" },
                    { label: "Tokens", value: wallet?.balance || 0, icon: Coins, color: "text-amber-400" },
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

            {/* Find Workers CTA */}
            <Link to="/employer/map" className="glass-card-hover p-6 flex items-center gap-4 group">
                <div className="w-12 h-12 rounded-xl bg-brand-600/20 flex items-center justify-center">
                    <MapPin size={24} className="text-brand-400" />
                </div>
                <div>
                    <h3 className="font-semibold group-hover:text-brand-300 transition-colors">Find Workers Near You</h3>
                    <p className="text-sm text-white/50">View live heatmap of available workers with profession tags</p>
                </div>
            </Link>

            {/* Jobs List */}
            <div>
                <h2 className="text-lg font-semibold mb-4">Your Jobs</h2>
                {jobs.length === 0 ? (
                    <div className="glass-card p-12 text-center">
                        <Briefcase size={48} className="text-white/20 mx-auto mb-4" />
                        <p className="text-white/50">No jobs yet. Post your first job!</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {jobs.map((job) => (
                            <Link key={job.id} to={`/jobs/${job.id}`} className="glass-card-hover p-4 flex items-center justify-between">
                                <div>
                                    <h3 className="font-medium">{job.title}</h3>
                                    <p className="text-sm text-white/50 mt-1">{job.category}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                    {job.budget_max && <span className="text-sm text-white/50">${job.budget_min}–${job.budget_max}</span>}
                                    <span className={STATUS_COLORS[job.status] || "badge-brand"}>{job.status}</span>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Job Modal */}
            {showCreate && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in p-4">
                    <form onSubmit={createJob} className="glass-card p-6 w-full max-w-lg space-y-4">
                        <h2 className="text-xl font-bold">Post a New Job</h2>
                        <div>
                            <label className="input-label">Title</label>
                            <input className="input-field" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Fix bathroom plumbing" />
                        </div>
                        <div>
                            <label className="input-label">Description</label>
                            <textarea className="input-field min-h-[100px]" required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Describe the work needed..." />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="input-label">Category</label>
                                <select className="input-field" required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                                    <option value="">Select</option>
                                    {["Plumbing", "Electrical", "Carpentry", "Painting", "Cleaning", "Gardening", "Masonry", "Welding", "Other"].map(c => (
                                        <option key={c} value={c}>{c}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="input-label">Budget Range ($)</label>
                                <div className="flex gap-2">
                                    <input type="number" className="input-field" value={form.budget_min} onChange={(e) => setForm({ ...form, budget_min: e.target.value })} placeholder="Min" />
                                    <input type="number" className="input-field" value={form.budget_max} onChange={(e) => setForm({ ...form, budget_max: e.target.value })} placeholder="Max" />
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-3 justify-end pt-2">
                            <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                            <button type="submit" className="btn-primary">Post Job (2 tokens)</button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}
