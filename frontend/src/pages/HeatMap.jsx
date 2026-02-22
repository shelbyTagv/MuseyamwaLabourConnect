import { useState, useEffect } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import { MapPin, Users, Filter } from "lucide-react";

export default function HeatMap() {
    const [workers, setWorkers] = useState([]);
    const [heatData, setHeatData] = useState([]);
    const [filter, setFilter] = useState("");
    const [loading, setLoading] = useState(true);
    const [center] = useState([-17.8292, 31.0522]); // Harare default
    const [leaflet, setLeaflet] = useState(null);

    // Dynamically import react-leaflet at runtime (avoids top-level await)
    useEffect(() => {
        import("react-leaflet")
            .then((mod) => setLeaflet(mod))
            .catch(() => setLeaflet(null));
    }, []);

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [workersRes, heatRes] = await Promise.all([
                api.get("/locations/nearby", { params: { latitude: center[0], longitude: center[1], radius_km: 30 } }),
                api.get("/locations/heatmap"),
            ]);
            setWorkers(workersRes.data);
            setHeatData(heatRes.data);
        } catch { toast.error("Failed to load map data"); }
        finally { setLoading(false); }
    };

    const filtered = filter
        ? workers.filter((w) => w.profession_tags?.some((t) => t.toLowerCase().includes(filter.toLowerCase())))
        : workers;

    if (!leaflet) {
        return (
            <div className="glass-card p-12 text-center">
                <MapPin size={48} className="text-white/20 mx-auto mb-4" />
                <p className="text-white/50">Loading map...</p>
            </div>
        );
    }

    const { MapContainer, TileLayer, Circle, Popup } = leaflet;

    return (
        <div className="space-y-4 animate-fade-in pb-20 lg:pb-0">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <MapPin size={24} className="text-brand-400" /> Find Workers
                    </h1>
                    <p className="text-white/50 mt-1">{filtered.length} workers online near you</p>
                </div>
                <div className="flex items-center gap-2">
                    <Filter size={16} className="text-white/40" />
                    <select className="input-field !w-auto" value={filter} onChange={(e) => setFilter(e.target.value)}>
                        <option value="">All Professions</option>
                        {["Plumber", "Electrician", "Carpenter", "Painter", "Cleaner", "Gardener", "Mason", "Welder"].map((p) => (
                            <option key={p} value={p}>{p}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Map */}
            <div className="glass-card overflow-hidden h-[60vh]">
                {loading ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <MapContainer center={center} zoom={12} className="h-full w-full" scrollWheelZoom>
                        <TileLayer
                            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                        />
                        {/* Worker markers */}
                        {filtered.map((w, i) => (
                            <Circle key={i} center={[w.latitude, w.longitude]} radius={200}
                                pathOptions={{ color: "#14b8a6", fillColor: "#14b8a6", fillOpacity: 0.3, weight: 1 }}>
                                <Popup>
                                    <div className="text-sm">
                                        <p className="font-bold">{w.full_name}</p>
                                        {w.profession_tags && <p className="text-xs">{w.profession_tags.join(", ")}</p>}
                                        {w.rating && <p className="text-xs">⭐ {w.rating.toFixed(1)}</p>}
                                    </div>
                                </Popup>
                            </Circle>
                        ))}
                        {/* Heatmap density circles */}
                        {heatData.map((h, i) => (
                            <Circle key={`heat-${i}`} center={[h.latitude, h.longitude]} radius={h.count * 100}
                                pathOptions={{ color: "#f59e0b", fillColor: "#f59e0b", fillOpacity: 0.15, weight: 0 }} />
                        ))}
                    </MapContainer>
                )}
            </div>

            {/* Worker list below map */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.slice(0, 12).map((w, i) => (
                    <div key={i} className="glass-card-hover p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-teal-400 flex items-center justify-center text-sm font-bold flex-shrink-0">
                                {w.full_name?.charAt(0)}
                            </div>
                            <div className="min-w-0">
                                <p className="font-medium text-sm truncate">{w.full_name}</p>
                                {w.profession_tags && <p className="text-xs text-white/40 truncate">{w.profession_tags.join(", ")}</p>}
                            </div>
                            {w.rating && <span className="ml-auto text-xs text-amber-400">⭐ {w.rating.toFixed(1)}</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
