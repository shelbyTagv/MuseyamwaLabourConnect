import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../services/api";
import useAuthStore from "../hooks/useAuth";
import toast from "react-hot-toast";
import { ArrowLeft, Clock, CheckCircle2, Star, Send, DollarSign } from "lucide-react";

const STATUS_FLOW = ["requested", "offered", "assigned", "en_route", "on_site", "completed", "rated"];

export default function JobDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuthStore();
    const [job, setJob] = useState(null);
    const [offers, setOffers] = useState([]);
    const [rating, setRating] = useState({ stars: 5, comment: "", tags: [] });
    const [showOffer, setShowOffer] = useState(false);
    const [offerAmount, setOfferAmount] = useState("");
    const [loading, setLoading] = useState(true);

    useEffect(() => { loadJob(); }, [id]);

    const loadJob = async () => {
        try {
            const [jobRes, offersRes] = await Promise.all([
                api.get(`/jobs/${id}`),
                api.get(`/offers/job/${id}`),
            ]);
            setJob(jobRes.data);
            setOffers(offersRes.data);
        } catch { toast.error("Job not found"); }
        finally { setLoading(false); }
    };

    const updateStatus = async (status) => {
        try {
            await api.patch(`/jobs/${id}/status`, { status });
            toast.success(`Job status updated to ${status}`);
            loadJob();
        } catch (err) { toast.error(err.response?.data?.detail || "Update failed"); }
    };

    const submitOffer = async () => {
        try {
            const toUser = user.role === "employer" ? job.worker_id : job.employer_id;
            await api.post("/offers/", {
                job_id: id, to_user_id: toUser || job.employer_id,
                amount: Number(offerAmount),
            });
            toast.success("Offer sent!");
            setShowOffer(false);
            loadJob();
        } catch (err) { toast.error(err.response?.data?.detail || "Failed"); }
    };

    const submitRating = async () => {
        try {
            const ratedId = user.id === job.employer_id ? job.worker_id : job.employer_id;
            await api.post("/ratings/", { job_id: id, rated_id: ratedId, ...rating });
            toast.success("Rating submitted!");
            loadJob();
        } catch (err) { toast.error(err.response?.data?.detail || "Failed"); }
    };

    if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" /></div>;
    if (!job) return <p className="text-white/50">Job not found</p>;

    const isEmployer = user?.id === job.employer_id;
    const isWorker = user?.id === job.worker_id;
    const currentIdx = STATUS_FLOW.indexOf(job.status);

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in pb-20 lg:pb-0">
            <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-white/50 hover:text-white text-sm">
                <ArrowLeft size={16} /> Back
            </button>

            {/* Header */}
            <div className="glass-card p-6">
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-2xl font-bold">{job.title}</h1>
                        <p className="text-white/50 mt-1">{job.category}</p>
                    </div>
                    <span className="badge-brand text-sm">{job.status}</span>
                </div>
                <p className="text-white/70 mt-4 leading-relaxed">{job.description}</p>
                {job.budget_max && (
                    <p className="mt-3 text-sm text-white/50 flex items-center gap-1">
                        <DollarSign size={14} /> Budget: ${job.budget_min}–${job.budget_max}
                        {job.agreed_price && <span className="text-emerald-400 ml-2">(Agreed: ${job.agreed_price})</span>}
                    </p>
                )}
            </div>

            {/* Status Timeline */}
            <div className="glass-card p-6">
                <h3 className="font-semibold mb-4">Progress</h3>
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                    {STATUS_FLOW.map((s, i) => (
                        <div key={s} className="flex items-center gap-2 flex-shrink-0">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold
                ${i <= currentIdx ? "bg-brand-500 text-white" : "bg-white/10 text-white/30"}`}>
                                {i <= currentIdx ? <CheckCircle2 size={16} /> : i + 1}
                            </div>
                            <span className={`text-xs capitalize ${i <= currentIdx ? "text-brand-300" : "text-white/30"}`}>{s}</span>
                            {i < STATUS_FLOW.length - 1 && <div className={`w-6 h-0.5 ${i < currentIdx ? "bg-brand-500" : "bg-white/10"}`} />}
                        </div>
                    ))}
                </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-3">
                {isEmployer && job.status === "requested" && (
                    <button onClick={() => setShowOffer(true)} className="btn-primary text-sm flex items-center gap-2">
                        <Send size={16} /> Send Offer
                    </button>
                )}
                {isWorker && job.status === "assigned" && (
                    <button onClick={() => updateStatus("en_route")} className="btn-primary text-sm">Mark En Route</button>
                )}
                {isWorker && job.status === "en_route" && (
                    <button onClick={() => updateStatus("on_site")} className="btn-primary text-sm">Arrived On Site</button>
                )}
                {(isEmployer || isWorker) && job.status === "on_site" && (
                    <button onClick={() => updateStatus("completed")} className="btn-primary text-sm">Mark Completed</button>
                )}
                {(isEmployer || isWorker) && job.status === "completed" && (
                    <button onClick={() => document.getElementById("rating-section")?.scrollIntoView()} className="btn-primary text-sm flex items-center gap-2">
                        <Star size={16} /> Rate
                    </button>
                )}
            </div>

            {/* Offers */}
            {offers.length > 0 && (
                <div className="glass-card p-6">
                    <h3 className="font-semibold mb-4">Offers</h3>
                    <div className="space-y-3">
                        {offers.map((o) => (
                            <div key={o.id} className="bg-white/5 rounded-xl p-3 flex items-center justify-between">
                                <div>
                                    <p className="font-medium">${o.amount}</p>
                                    {o.message && <p className="text-sm text-white/50 mt-1">{o.message}</p>}
                                </div>
                                <span className={`text-xs capitalize ${o.status === "accepted" ? "text-emerald-400" : o.status === "rejected" ? "text-rose-400" : "text-white/50"}`}>
                                    {o.status}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Offer Modal */}
            {showOffer && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <div className="glass-card p-6 w-full max-w-sm space-y-4">
                        <h3 className="text-lg font-bold">Send Offer</h3>
                        <input type="number" className="input-field" placeholder="Amount ($)" value={offerAmount} onChange={(e) => setOfferAmount(e.target.value)} />
                        <div className="flex gap-3 justify-end">
                            <button onClick={() => setShowOffer(false)} className="btn-secondary">Cancel</button>
                            <button onClick={submitOffer} className="btn-primary">Send</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Rating Section */}
            {job.status === "completed" && (isEmployer || isWorker) && (
                <div id="rating-section" className="glass-card p-6">
                    <h3 className="font-semibold mb-4">Rate This Job</h3>
                    <div className="flex items-center gap-2 mb-4">
                        {[1, 2, 3, 4, 5].map((s) => (
                            <button key={s} onClick={() => setRating({ ...rating, stars: s })}
                                className={`text-2xl transition-colors ${s <= rating.stars ? "text-amber-400" : "text-white/20"}`}>
                                ★
                            </button>
                        ))}
                    </div>
                    <textarea className="input-field mb-4" placeholder="Leave a comment..." value={rating.comment}
                        onChange={(e) => setRating({ ...rating, comment: e.target.value })} />
                    <div className="flex flex-wrap gap-2 mb-4">
                        {["Professional", "Punctual", "Skilled", "Friendly", "Efficient"].map((tag) => (
                            <button key={tag} onClick={() => {
                                const tags = rating.tags.includes(tag) ? rating.tags.filter(t => t !== tag) : [...rating.tags, tag];
                                setRating({ ...rating, tags });
                            }} className={`badge cursor-pointer ${rating.tags.includes(tag) ? "badge-brand" : "bg-white/5 text-white/50 border border-white/10"}`}>
                                {tag}
                            </button>
                        ))}
                    </div>
                    <button onClick={submitRating} className="btn-primary text-sm">Submit Rating</button>
                </div>
            )}
        </div>
    );
}
