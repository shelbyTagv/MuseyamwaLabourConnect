import { useState, useEffect, useRef } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import { Coins, ArrowUpCircle, ArrowDownCircle, Plus, Smartphone, CheckCircle, XCircle, Loader2 } from "lucide-react";

export default function TokenWallet() {
    const [wallet, setWallet] = useState(null);
    const [transactions, setTransactions] = useState([]);
    const [showPurchase, setShowPurchase] = useState(false);
    const [purchaseForm, setPurchaseForm] = useState({ amount: 10, method: "ecocash", phone: "" });
    const [loading, setLoading] = useState(true);
    const [purchasing, setPurchasing] = useState(false);

    // Payment status tracking
    const [paymentStatus, setPaymentStatus] = useState(null);
    const [activePaymentId, setActivePaymentId] = useState(null);
    const pollRef = useRef(null);

    useEffect(() => { loadData(); return () => clearInterval(pollRef.current); }, []);

    const loadData = async () => {
        try {
            const [wRes, tRes] = await Promise.all([
                api.get("/tokens/wallet"),
                api.get("/tokens/transactions"),
            ]);
            setWallet(wRes.data);
            setTransactions(tRes.data);
        } catch { toast.error("Failed to load wallet"); }
        finally { setLoading(false); }
    };

    const purchase = async () => {
        if (!purchaseForm.phone) { toast.error("Please enter your phone number"); return; }
        setPurchasing(true);
        setPaymentStatus("pending");

        try {
            const res = await api.post("/tokens/purchase", purchaseForm);
            const paymentId = res.data.id;
            setActivePaymentId(paymentId);
            setShowPurchase(false);
            toast.success("📲 Check your phone! Enter your PIN to complete payment.");

            let attempts = 0;
            pollRef.current = setInterval(async () => {
                attempts++;
                try {
                    const statusRes = await api.get(`/tokens/purchase/${paymentId}/status`);
                    const status = statusRes.data.status;

                    if (status === "completed") {
                        clearInterval(pollRef.current);
                        setPaymentStatus("success");
                        setPurchasing(false);
                        toast.success(`🎉 ${purchaseForm.amount} tokens added to your wallet!`);
                        loadData();
                        setTimeout(() => { setPaymentStatus(null); setActivePaymentId(null); }, 5000);
                    } else if (status === "failed") {
                        clearInterval(pollRef.current);
                        setPaymentStatus("failed");
                        setPurchasing(false);
                        toast.error("Payment was not completed. Please try again.");
                        setTimeout(() => { setPaymentStatus(null); setActivePaymentId(null); }, 5000);
                    }
                } catch { /* keep polling */ }

                if (attempts >= 24) {
                    clearInterval(pollRef.current);
                    setPaymentStatus(null);
                    setPurchasing(false);
                    setActivePaymentId(null);
                    toast.error("Payment verification timed out. If you completed payment, your tokens will be credited shortly.");
                }
            }, 5000);

        } catch (err) {
            setPurchasing(false);
            setPaymentStatus(null);
            toast.error(err.response?.data?.detail || "Could not initiate payment. Please try again.");
        }
    };

    if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in pb-20 lg:pb-0">
            {/* Payment Status Banner */}
            {paymentStatus && (
                <div className={`glass-card p-4 flex items-center gap-4 border
                    ${paymentStatus === "pending" ? "border-amber-500/30 bg-amber-500/5" :
                        paymentStatus === "success" ? "border-emerald-500/30 bg-emerald-500/5" :
                            "border-rose-500/30 bg-rose-500/5"}`}>
                    {paymentStatus === "pending" && (
                        <>
                            <Loader2 size={24} className="text-amber-400 animate-spin flex-shrink-0" />
                            <div>
                                <p className="font-medium text-amber-300">Waiting for payment...</p>
                                <p className="text-sm text-white/50 mt-0.5">Check your phone and enter your PIN to confirm</p>
                            </div>
                        </>
                    )}
                    {paymentStatus === "success" && (
                        <>
                            <CheckCircle size={24} className="text-emerald-400 flex-shrink-0" />
                            <div>
                                <p className="font-medium text-emerald-300">Payment successful!</p>
                                <p className="text-sm text-white/50 mt-0.5">Tokens have been added to your wallet</p>
                            </div>
                        </>
                    )}
                    {paymentStatus === "failed" && (
                        <>
                            <XCircle size={24} className="text-rose-400 flex-shrink-0" />
                            <div>
                                <p className="font-medium text-rose-300">Payment failed</p>
                                <p className="text-sm text-white/50 mt-0.5">Please try again or use a different payment method</p>
                            </div>
                        </>
                    )}
                </div>
            )}

            {/* Balance Card */}
            <div className="glass-card p-8 text-center relative overflow-hidden">
                <div className="absolute top-0 right-0 w-40 h-40 bg-brand-500/10 rounded-full blur-[60px]" />
                <Coins size={40} className="text-amber-400 mx-auto mb-3" />
                <p className="text-sm text-white/50 mb-1">Token Balance</p>
                <p className="text-5xl font-bold gradient-text">{wallet?.balance || 0}</p>
                <p className="text-sm text-white/40 mt-2">≈ ${((wallet?.balance || 0) * 0.50).toFixed(2)} USD</p>
                <button
                    onClick={() => setShowPurchase(true)}
                    disabled={purchasing}
                    className="btn-primary mt-6 flex items-center gap-2 mx-auto disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {purchasing ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                    {purchasing ? "Processing..." : "Buy Tokens"}
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
                <div className="glass-card p-4 text-center">
                    <p className="text-2xl font-bold text-emerald-400">{wallet?.total_purchased || 0}</p>
                    <p className="text-xs text-white/50 mt-1">Total Purchased</p>
                </div>
                <div className="glass-card p-4 text-center">
                    <p className="text-2xl font-bold text-rose-400">{wallet?.total_spent || 0}</p>
                    <p className="text-xs text-white/50 mt-1">Total Spent</p>
                </div>
            </div>

            {/* Transactions */}
            <div>
                <h2 className="text-lg font-semibold mb-4">Transaction History</h2>
                {transactions.length === 0 ? (
                    <div className="glass-card p-8 text-center">
                        <p className="text-white/50">No transactions yet</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {transactions.map((tx) => (
                            <div key={tx.id} className="glass-card p-4 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    {tx.amount > 0 ? (
                                        <ArrowUpCircle size={20} className="text-emerald-400" />
                                    ) : (
                                        <ArrowDownCircle size={20} className="text-rose-400" />
                                    )}
                                    <div>
                                        <p className="text-sm font-medium">{tx.description || tx.type}</p>
                                        <p className="text-xs text-white/40">{new Date(tx.created_at).toLocaleString()}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className={`font-semibold ${tx.amount > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                        {tx.amount > 0 ? "+" : ""}{tx.amount}
                                    </p>
                                    <p className="text-xs text-white/40">Bal: {tx.balance_after}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Purchase Modal */}
            {showPurchase && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <div className="glass-card p-6 w-full max-w-sm space-y-5">
                        <h2 className="text-xl font-bold flex items-center gap-2"><Coins size={20} className="text-amber-400" /> Buy Tokens</h2>

                        <div>
                            <label className="input-label">Token Amount</label>
                            <div className="grid grid-cols-3 gap-2">
                                {[5, 10, 20, 50, 100].map((a) => (
                                    <button key={a} onClick={() => setPurchaseForm({ ...purchaseForm, amount: a })}
                                        className={`py-2 rounded-xl text-sm font-medium transition-all
                      ${purchaseForm.amount === a ? "bg-brand-600/30 border border-brand-500/50 text-brand-300" : "bg-white/5 border border-white/10 text-white/60"}`}>
                                        {a} tokens
                                    </button>
                                ))}
                            </div>
                            <p className="text-xs text-white/40 mt-2">Cost: ${(purchaseForm.amount * 0.50).toFixed(2)} USD</p>
                        </div>

                        <div>
                            <label className="input-label">Payment Method</label>
                            <div className="grid grid-cols-2 gap-2">
                                {[{ v: "ecocash", l: "EcoCash" }, { v: "innbucks", l: "Innbucks" }].map(({ v, l }) => (
                                    <button key={v} onClick={() => setPurchaseForm({ ...purchaseForm, method: v })}
                                        className={`py-2 rounded-xl text-sm font-medium flex items-center justify-center gap-2 transition-all
                      ${purchaseForm.method === v ? "bg-brand-600/30 border border-brand-500/50 text-brand-300" : "bg-white/5 border border-white/10 text-white/60"}`}>
                                        <Smartphone size={16} /> {l}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="input-label">Phone Number</label>
                            <input className="input-field" placeholder="e.g. 0771234567 or +263771234567"
                                value={purchaseForm.phone}
                                onChange={(e) => setPurchaseForm({ ...purchaseForm, phone: e.target.value })} />
                            <p className="text-xs text-white/40 mt-1">You'll receive a payment prompt on this number</p>
                        </div>

                        <div className="flex gap-3 justify-end pt-2">
                            <button onClick={() => setShowPurchase(false)} className="btn-secondary">Cancel</button>
                            <button onClick={purchase} disabled={purchasing} className="btn-primary flex items-center gap-2 disabled:opacity-50">
                                {purchasing ? <Loader2 size={16} className="animate-spin" /> : <Smartphone size={16} />}
                                Pay ${(purchaseForm.amount * 0.50).toFixed(2)}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
