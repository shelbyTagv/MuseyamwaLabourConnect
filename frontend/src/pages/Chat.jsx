import { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import api from "../services/api";
import useAuthStore from "../hooks/useAuth";
import { useWebSocket } from "../hooks/useWebSocket";
import toast from "react-hot-toast";
import { Send, ArrowLeft, MessageCircle } from "lucide-react";

export default function Chat() {
    const { partnerId } = useParams();
    const { user } = useAuthStore();
    const [conversations, setConversations] = useState([]);
    const [messages, setMessages] = useState([]);
    const [activePartner, setActivePartner] = useState(partnerId || null);
    const [text, setText] = useState("");
    const messagesEnd = useRef(null);

    const token = localStorage.getItem("access_token");
    const { send } = useWebSocket("/messages/ws", token, (msg) => {
        if (msg.sender_id === activePartner || msg.receiver_id === activePartner) {
            setMessages((prev) => [...prev, msg]);
        }
    });

    useEffect(() => {
        loadConversations();
    }, []);

    useEffect(() => {
        if (activePartner) loadMessages(activePartner);
    }, [activePartner]);

    useEffect(() => {
        messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const loadConversations = async () => {
        try {
            const { data } = await api.get("/messages/conversations");
            setConversations(data);
        } catch { /* ignore */ }
    };

    const loadMessages = async (pid) => {
        try {
            const { data } = await api.get(`/messages/${pid}`);
            setMessages(data);
        } catch { toast.error("Failed to load messages"); }
    };

    const sendMessage = async () => {
        if (!text.trim() || !activePartner) return;
        try {
            send({ receiver_id: activePartner, content: text });
            await api.post("/messages/", { receiver_id: activePartner, content: text });
            setText("");
            loadMessages(activePartner);
        } catch { toast.error("Failed to send"); }
    };

    return (
        <div className="animate-fade-in pb-20 lg:pb-0">
            <div className="flex h-[calc(100vh-8rem)] lg:h-[calc(100vh-6rem)] gap-4">
                {/* Conversation List */}
                <div className={`${activePartner ? "hidden lg:flex" : "flex"} flex-col w-full lg:w-80 glass-card overflow-hidden`}>
                    <div className="p-4 border-b border-white/5">
                        <h2 className="font-semibold flex items-center gap-2">
                            <MessageCircle size={18} className="text-brand-400" /> Messages
                        </h2>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        {conversations.length === 0 ? (
                            <p className="text-white/40 text-sm text-center p-6">No conversations yet</p>
                        ) : (
                            conversations.map((c) => (
                                <button key={c.partner_id} onClick={() => setActivePartner(c.partner_id)}
                                    className={`w-full text-left p-4 border-b border-white/5 hover:bg-white/5 transition-colors
                    ${activePartner === c.partner_id ? "bg-brand-600/10 border-l-2 border-l-brand-500" : ""}`}>
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-teal-400 flex items-center justify-center text-sm font-bold flex-shrink-0">
                                            {c.partner_name?.charAt(0)}
                                        </div>
                                        <div className="min-w-0">
                                            <p className="font-medium text-sm truncate">{c.partner_name}</p>
                                            <p className="text-xs text-white/40 truncate">{c.last_message}</p>
                                        </div>
                                        {c.unread_count > 0 && (
                                            <span className="ml-auto w-5 h-5 rounded-full bg-brand-500 text-xs flex items-center justify-center font-bold flex-shrink-0">
                                                {c.unread_count}
                                            </span>
                                        )}
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Messages */}
                {activePartner ? (
                    <div className="flex-1 glass-card flex flex-col overflow-hidden">
                        <div className="p-4 border-b border-white/5 flex items-center gap-3">
                            <button onClick={() => setActivePartner(null)} className="lg:hidden text-white/50 hover:text-white">
                                <ArrowLeft size={20} />
                            </button>
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-teal-400 flex items-center justify-center text-xs font-bold">
                                {conversations.find(c => c.partner_id === activePartner)?.partner_name?.charAt(0) || "?"}
                            </div>
                            <p className="font-medium text-sm">
                                {conversations.find(c => c.partner_id === activePartner)?.partner_name || "Chat"}
                            </p>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {messages.map((m, i) => (
                                <div key={i} className={`flex ${m.sender_id === user.id ? "justify-end" : "justify-start"}`}>
                                    <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm
                    ${m.sender_id === user.id
                                            ? "bg-brand-600 text-white rounded-br-md"
                                            : "bg-white/10 text-white/90 rounded-bl-md"}`}>
                                        {m.content}
                                        <p className={`text-[10px] mt-1 ${m.sender_id === user.id ? "text-white/50" : "text-white/30"}`}>
                                            {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                        </p>
                                    </div>
                                </div>
                            ))}
                            <div ref={messagesEnd} />
                        </div>

                        <div className="p-4 border-t border-white/5">
                            <div className="flex gap-2">
                                <input className="input-field flex-1" placeholder="Type a message..."
                                    value={text} onChange={(e) => setText(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && sendMessage()} />
                                <button onClick={sendMessage} className="btn-primary !px-4">
                                    <Send size={18} />
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="hidden lg:flex flex-1 glass-card items-center justify-center">
                        <div className="text-center">
                            <MessageCircle size={48} className="text-white/20 mx-auto mb-3" />
                            <p className="text-white/40">Select a conversation</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
