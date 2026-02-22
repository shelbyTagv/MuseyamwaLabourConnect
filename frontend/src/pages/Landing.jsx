import { Link } from "react-router-dom";
import {
    ArrowRight, Star, MapPin, Shield, Coins, Zap, Users, Briefcase,
    Phone, CheckCircle2, TrendingUp, Clock, MessageCircle, Award
} from "lucide-react";

export default function Landing() {
    return (
        <div className="min-h-screen bg-surface-950 overflow-hidden text-white">

            {/* ════════════════════════════════════════════════════
                HERO
            ════════════════════════════════════════════════════ */}
            <div className="relative">
                {/* Animated glow layers */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-brand-600/20 rounded-full blur-[140px] animate-pulse" />
                <div className="absolute top-32 right-10 w-[350px] h-[350px] bg-teal-400/10 rounded-full blur-[90px]" />
                <div className="absolute top-60 left-10 w-[250px] h-[250px] bg-amber-400/10 rounded-full blur-[70px]" />

                <header className="relative z-10 flex items-center justify-between px-6 lg:px-16 py-6">
                    <h1 className="text-2xl font-extrabold gradient-text tracking-tight">MuseyamwaLabourConnect</h1>
                    <div className="flex items-center gap-4">
                        <Link to="/login" className="text-sm text-white/70 hover:text-white transition-colors">Sign In</Link>
                        <Link to="/register" className="btn-primary text-sm !py-2 !px-5">Join Free</Link>
                    </div>
                </header>

                <section className="relative z-10 max-w-5xl mx-auto text-center px-6 pt-16 pb-28">
                    <div className="inline-flex items-center gap-2 bg-brand-500/10 border border-brand-500/20 text-brand-300 text-sm font-semibold px-4 py-2 rounded-full mb-8">
                        <Star size={14} /> Trusted by Workers & Employers Across Zimbabwe
                    </div>

                    <h2 className="text-4xl md:text-6xl lg:text-7xl font-extrabold leading-[1.1] mb-6">
                        Your Skills Deserve
                        <span className="block gradient-text mt-2">Real Opportunities</span>
                    </h2>

                    <p className="text-lg md:text-xl text-white/60 max-w-2xl mx-auto mb-4 leading-relaxed">
                        Whether you're a plumber in Mbare, an electrician in Bulawayo, or a painter in Mutare —
                        <strong className="text-white/90"> get found by employers near you, today.</strong>
                    </p>
                    <p className="text-base text-white/40 max-w-xl mx-auto mb-10">
                        No office needed. No CV needed. Just your phone, your skills, and MuseyamwaLabourConnect.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
                        <Link to="/register?role=employee" className="btn-primary text-lg flex items-center gap-2 group">
                            I'm Looking for Work <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link to="/register?role=employer" className="btn-secondary text-lg">
                            I Need to Hire Workers
                        </Link>
                    </div>

                    {/* Trust stats */}
                    <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                        {[
                            { value: "Free", label: "To Sign Up" },
                            { value: "GPS", label: "Live Tracking" },
                            { value: "24/7", label: "Always Open" },
                        ].map(({ value, label }) => (
                            <div key={label} className="text-center">
                                <p className="text-2xl md:text-3xl font-extrabold gradient-text">{value}</p>
                                <p className="text-xs text-white/40 mt-1">{label}</p>
                            </div>
                        ))}
                    </div>
                </section>
            </div>

            {/* ════════════════════════════════════════════════════
                WHY US — Pain points of informal workers
            ════════════════════════════════════════════════════ */}
            <section className="py-20 px-6 lg:px-16 bg-white/[0.02]">
                <div className="max-w-5xl mx-auto">
                    <p className="text-brand-400 text-sm font-semibold uppercase tracking-wider text-center mb-3">Why MuseyamwaLabourConnect?</p>
                    <h3 className="text-3xl md:text-4xl font-bold text-center mb-4">
                        Built for the Hustlers. Built for <span className="gradient-text">Real Work.</span>
                    </h3>
                    <p className="text-white/50 text-center max-w-2xl mx-auto mb-16">
                        We know the struggle — waiting at road junctions for work, relying on word-of-mouth,
                        missing out on jobs because someone else got there first. That ends here.
                    </p>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[
                            {
                                icon: MapPin,
                                title: "Get Found on the Map",
                                desc: "Toggle online and your GPS shows employers exactly where you are. No more walking around looking for jobs — jobs come to you.",
                                color: "text-emerald-400",
                            },
                            {
                                icon: Coins,
                                title: "Affordable Tokens",
                                desc: "No monthly subscriptions. Buy only what you need — starting from just $0.50. Pay with EcoCash or Innbucks.",
                                color: "text-amber-400",
                            },
                            {
                                icon: Phone,
                                title: "Works on Any Phone",
                                desc: "Our app works on smartphones with basic data — even on slow networks. No need for a fancy phone or laptop.",
                                color: "text-blue-400",
                            },
                            {
                                icon: Shield,
                                title: "Verified & Safe",
                                desc: "Every user is phone-verified with OTP. You know who you're working with. Build your reputation with ratings.",
                                color: "text-purple-400",
                            },
                            {
                                icon: MessageCircle,
                                title: "Chat Directly",
                                desc: "No middlemen. Message employers or workers directly in the app. Negotiate your rate, agree on terms, get the job done.",
                                color: "text-teal-400",
                            },
                            {
                                icon: TrendingUp,
                                title: "Build Your Reputation",
                                desc: "Every completed job builds your profile. Get rated, collect reviews, and stand out. Your hard work finally has a record.",
                                color: "text-rose-400",
                            },
                        ].map(({ icon: Icon, title, desc, color }) => (
                            <div key={title} className="glass-card p-6 hover:bg-white/[0.06] transition-all duration-300 group">
                                <div className={`w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-4 ${color} group-hover:scale-110 transition-transform`}>
                                    <Icon size={24} />
                                </div>
                                <h4 className="text-lg font-semibold mb-2">{title}</h4>
                                <p className="text-sm text-white/50 leading-relaxed">{desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ════════════════════════════════════════════════════
                HOW IT WORKS — Simple steps
            ════════════════════════════════════════════════════ */}
            <section className="py-20 px-6 lg:px-16">
                <div className="max-w-4xl mx-auto">
                    <p className="text-brand-400 text-sm font-semibold uppercase tracking-wider text-center mb-3">Simple as 1-2-3</p>
                    <h3 className="text-3xl md:text-4xl font-bold text-center mb-16">
                        Start Earning in <span className="gradient-text">Under 5 Minutes</span>
                    </h3>

                    <div className="space-y-10">
                        {[
                            {
                                step: "1",
                                title: "Sign Up for Free",
                                desc: "Create your account with just your name, phone number, and skills. It takes 2 minutes. No documents, no fees.",
                                icon: Phone,
                            },
                            {
                                step: "2",
                                title: "Go Online & Get Visible",
                                desc: "Toggle your status to 'Online' and you'll appear on the live map. Employers in your area can see your skills, location, and ratings instantly.",
                                icon: MapPin,
                            },
                            {
                                step: "3",
                                title: "Get Hired & Get Paid",
                                desc: "Employers send you job offers with a price. Accept, negotiate, or counter. Complete the work, get rated, and grow your reputation. Payment is between you and the employer — direct, no middlemen.",
                                icon: Briefcase,
                            },
                        ].map(({ step, title, desc, icon: Icon }) => (
                            <div key={step} className="flex items-start gap-6 group">
                                <div className="flex-shrink-0 w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-teal-400 flex items-center justify-center text-xl font-bold shadow-lg shadow-brand-500/20 group-hover:scale-110 transition-transform">
                                    {step}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <Icon size={18} className="text-brand-400" />
                                        <h4 className="text-xl font-semibold">{title}</h4>
                                    </div>
                                    <p className="text-white/50 leading-relaxed">{desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ════════════════════════════════════════════════════
                FOR EMPLOYERS — Hiring side
            ════════════════════════════════════════════════════ */}
            <section className="py-20 px-6 lg:px-16 bg-white/[0.02]">
                <div className="max-w-5xl mx-auto">
                    <p className="text-amber-400 text-sm font-semibold uppercase tracking-wider text-center mb-3">For Employers</p>
                    <h3 className="text-3xl md:text-4xl font-bold text-center mb-4">
                        Need a Worker? <span className="gradient-text">Find One in Seconds.</span>
                    </h3>
                    <p className="text-white/50 text-center max-w-2xl mx-auto mb-12">
                        Stop wasting time searching. Our live map shows you verified, skilled workers near your location — ready to work right now.
                    </p>

                    <div className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
                        {[
                            { icon: MapPin, text: "See workers on a live GPS map" },
                            { icon: Users, text: "Filter by trade: plumber, electrician, carpenter, etc." },
                            { icon: Award, text: "Check ratings & reviews before hiring" },
                            { icon: MessageCircle, text: "Chat & negotiate directly in the app" },
                            { icon: Clock, text: "Post a job and get responses in minutes" },
                            { icon: Shield, text: "All workers are phone-verified via OTP" },
                        ].map(({ icon: Icon, text }) => (
                            <div key={text} className="flex items-center gap-4 glass-card p-4 hover:bg-white/[0.06] transition-colors">
                                <CheckCircle2 size={18} className="text-emerald-400 flex-shrink-0" />
                                <span className="text-sm text-white/70">{text}</span>
                            </div>
                        ))}
                    </div>

                    <div className="text-center mt-10">
                        <Link to="/register?role=employer" className="btn-primary text-lg inline-flex items-center gap-2 group">
                            Start Hiring Now <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </Link>
                    </div>
                </div>
            </section>

            {/* ════════════════════════════════════════════════════
                TOKEN PRICING — Transparent costs
            ════════════════════════════════════════════════════ */}
            <section className="py-20 px-6 lg:px-16">
                <div className="max-w-4xl mx-auto text-center">
                    <p className="text-brand-400 text-sm font-semibold uppercase tracking-wider mb-3">Simple, Affordable Pricing</p>
                    <h3 className="text-3xl md:text-4xl font-bold mb-4">
                        No Subscriptions. <span className="gradient-text">Pay As You Go.</span>
                    </h3>
                    <p className="text-white/50 max-w-xl mx-auto mb-12">
                        Buy tokens when you need them. Each action costs a small number of tokens —
                        way cheaper than newspaper ads or recruitment agencies.
                    </p>

                    <div className="grid sm:grid-cols-3 gap-6 max-w-3xl mx-auto mb-10">
                        {[
                            { action: "Send a Message", cost: "1 Token", icon: MessageCircle, color: "text-teal-400" },
                            { action: "Send a Job Offer", cost: "1 Token", icon: Briefcase, color: "text-blue-400" },
                            { action: "Post a Job", cost: "2 Tokens", icon: Zap, color: "text-amber-400" },
                        ].map(({ action, cost, icon: Icon, color }) => (
                            <div key={action} className="glass-card p-6 text-center">
                                <Icon size={28} className={`mx-auto mb-3 ${color}`} />
                                <p className="font-semibold mb-1">{action}</p>
                                <p className="text-2xl font-extrabold gradient-text">{cost}</p>
                            </div>
                        ))}
                    </div>

                    <div className="glass-card p-6 max-w-md mx-auto">
                        <p className="text-sm text-white/60 mb-2">Token Packs start from:</p>
                        <p className="text-3xl font-extrabold">
                            <span className="gradient-text">$0.50</span>
                            <span className="text-base text-white/40 font-normal ml-2">for 10 tokens</span>
                        </p>
                        <p className="text-xs text-white/30 mt-2">Pay via EcoCash, Innbucks, or Bank Transfer</p>
                    </div>
                </div>
            </section>

            {/* ════════════════════════════════════════════════════
                TRADES WE COVER
            ════════════════════════════════════════════════════ */}
            <section className="py-16 px-6 lg:px-16 bg-white/[0.02]">
                <div className="max-w-5xl mx-auto text-center">
                    <h3 className="text-2xl font-bold mb-8">Every Trade. Every Skill. <span className="gradient-text">One Platform.</span></h3>
                    <div className="flex flex-wrap justify-center gap-3">
                        {[
                            "Plumbing", "Electrical", "Carpentry", "Painting", "Masonry",
                            "Welding", "Gardening", "Cleaning", "Tiling", "Roofing",
                            "Fencing", "Pest Control", "Moving", "Driving", "Cooking",
                            "Sewing", "Hairdressing", "Auto Mechanic", "Construction",
                        ].map((trade) => (
                            <span key={trade} className="badge-brand !text-sm !px-4 !py-2">{trade}</span>
                        ))}
                        <span className="badge-gold !text-sm !px-4 !py-2">& Many More...</span>
                    </div>
                </div>
            </section>

            {/* ════════════════════════════════════════════════════
                FINAL CTA
            ════════════════════════════════════════════════════ */}
            <section className="py-24 px-6 lg:px-16 relative">
                <div className="absolute inset-0 bg-gradient-to-t from-brand-600/10 to-transparent" />
                <div className="relative z-10 max-w-3xl mx-auto text-center">
                    <h3 className="text-3xl md:text-5xl font-extrabold mb-6 leading-tight">
                        Stop Waiting at the Junction.
                        <span className="block gradient-text mt-2">Start Getting Hired.</span>
                    </h3>
                    <p className="text-lg text-white/50 max-w-xl mx-auto mb-8">
                        Join thousands of skilled workers and employers across Zimbabwe
                        who are already using MuseyamwaLabourConnect to find work and hire talent.
                    </p>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Link to="/register?role=employee" className="btn-primary text-lg flex items-center gap-2 group">
                            Find Work Now <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link to="/register?role=employer" className="btn-secondary text-lg">
                            Hire a Worker
                        </Link>
                    </div>
                    <p className="text-xs text-white/30 mt-6">Free to register • No subscriptions • Pay only when you use it</p>
                </div>
            </section>

            {/* ════════════════════════════════════════════════════
                FOOTER
            ════════════════════════════════════════════════════ */}
            <footer className="py-12 px-6 lg:px-16 border-t border-white/5">
                <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="text-center md:text-left">
                        <h4 className="text-lg font-bold gradient-text">MuseyamwaLabourConnect</h4>
                        <p className="text-xs text-white/30 mt-1">Zimbabwe's tokenized labour marketplace</p>
                    </div>
                    <div className="flex items-center gap-6 text-sm text-white/40">
                        <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
                        <Link to="/register" className="hover:text-white transition-colors">Register</Link>
                    </div>
                </div>
                <div className="max-w-5xl mx-auto mt-8 pt-6 border-t border-white/5 text-center space-y-1">
                    <p className="text-sm text-white/30">
                        © 2026 MuseyamwaLabourConnect. All rights reserved.
                    </p>
                    <p className="text-xs text-white/20">
                        Designed & Developed by <span className="text-brand-400/70 font-medium">TAGV Engineering Solutions (Pvt) Ltd</span>
                    </p>
                </div>
            </footer>
        </div>
    );
}
