import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import api from "../services/api";
import useAuthStore from "../hooks/useAuth";
import toast from "react-hot-toast";
import { User, Star, Briefcase, MapPin, Save } from "lucide-react";

export default function Profile() {
    const { userId } = useParams();
    const { user: currentUser } = useAuthStore();
    const isOwnProfile = !userId || userId === currentUser?.id;
    const [profile, setProfile] = useState(null);
    const [editing, setEditing] = useState(false);
    const [form, setForm] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => { loadProfile(); }, [userId]);

    const loadProfile = async () => {
        try {
            const endpoint = isOwnProfile ? "/users/me/profile" : `/users/${userId}/profile`;
            const { data } = await api.get(endpoint);
            setProfile(data);
            setForm(data);
        } catch { toast.error("Profile not found"); }
        finally { setLoading(false); }
    };

    const saveProfile = async () => {
        try {
            await api.put("/users/me/profile", {
                bio: form.bio,
                profession_tags: form.profession_tags,
                skills: form.skills,
                experience_years: form.experience_years,
            });
            toast.success("Profile updated!");
            setEditing(false);
            loadProfile();
        } catch { toast.error("Update failed"); }
    };

    if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in pb-20 lg:pb-0">
            {/* Profile Header */}
            <div className="glass-card p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-40 h-40 bg-brand-500/10 rounded-full blur-[60px]" />
                <div className="relative flex flex-col sm:flex-row items-center gap-6">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-500 to-teal-400 flex items-center justify-center text-3xl font-bold flex-shrink-0">
                        {profile?.user_name?.charAt(0) || <User size={32} />}
                    </div>
                    <div className="text-center sm:text-left">
                        <h1 className="text-2xl font-bold">{profile?.user_name}</h1>
                        <p className="text-white/50 capitalize">{profile?.role}</p>
                        <div className="flex items-center gap-4 mt-2 justify-center sm:justify-start">
                            <span className="flex items-center gap-1 text-sm text-amber-400">
                                <Star size={14} /> {profile?.average_rating?.toFixed(1) || "0.0"}
                            </span>
                            <span className="flex items-center gap-1 text-sm text-white/50">
                                <Briefcase size={14} /> {profile?.total_jobs_completed || 0} jobs
                            </span>
                        </div>
                    </div>
                    {isOwnProfile && !editing && (
                        <button onClick={() => setEditing(true)} className="btn-secondary text-sm sm:ml-auto">
                            Edit Profile
                        </button>
                    )}
                </div>
            </div>

            {/* Bio */}
            <div className="glass-card p-6">
                <h3 className="font-semibold mb-3">About</h3>
                {editing ? (
                    <textarea className="input-field min-h-[100px]" value={form.bio || ""}
                        onChange={(e) => setForm({ ...form, bio: e.target.value })} placeholder="Tell employers about yourself..." />
                ) : (
                    <p className="text-white/70">{profile?.bio || "No bio yet"}</p>
                )}
            </div>

            {/* Skills & Tags */}
            <div className="glass-card p-6">
                <h3 className="font-semibold mb-3">Skills & Professions</h3>
                {editing ? (
                    <div>
                        <label className="input-label">Profession Tags (comma separated)</label>
                        <input className="input-field mb-3" value={(form.profession_tags || []).join(", ")}
                            onChange={(e) => setForm({ ...form, profession_tags: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
                            placeholder="Plumber, Electrician, Carpenter" />
                        <label className="input-label">Skills (comma separated)</label>
                        <input className="input-field mb-3" value={(form.skills || []).join(", ")}
                            onChange={(e) => setForm({ ...form, skills: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
                            placeholder="Pipe fitting, Wiring, Tiling" />
                        <label className="input-label">Years of Experience</label>
                        <input type="number" className="input-field" value={form.experience_years || ""}
                            onChange={(e) => setForm({ ...form, experience_years: Number(e.target.value) })} />
                    </div>
                ) : (
                    <div>
                        {profile?.profession_tags?.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-3">
                                {profile.profession_tags.map((t) => <span key={t} className="badge-brand">{t}</span>)}
                            </div>
                        )}
                        {profile?.skills?.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-3">
                                {profile.skills.map((s) => <span key={s} className="badge-gold">{s}</span>)}
                            </div>
                        )}
                        {profile?.experience_years && (
                            <p className="text-sm text-white/50">{profile.experience_years} years experience</p>
                        )}
                    </div>
                )}
            </div>

            {/* Save button */}
            {editing && (
                <div className="flex gap-3 justify-end">
                    <button onClick={() => setEditing(false)} className="btn-secondary">Cancel</button>
                    <button onClick={saveProfile} className="btn-primary flex items-center gap-2">
                        <Save size={16} /> Save Changes
                    </button>
                </div>
            )}
        </div>
    );
}
