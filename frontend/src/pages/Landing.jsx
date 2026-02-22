import { Link } from "react-router-dom";
import { ArrowRight, Star } from "lucide-react";

export default function Landing() {
    return (
        <div className="min-h-screen bg-surface-950 overflow-hidden">
            {/* ── Hero ── */}
            <div className="relative">
                {/* Glow effects */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-brand-600/20 rounded-full blur-[120px]" />
                <div className="absolute top-40 right-20 w-[300px] h-[300px] bg-teal-400/10 rounded-full blur-[80px]" />

                <header className="relative z-10 flex items-center justify-between px-6 lg:px-16 py-6">
                    <h1 className="text-2xl font-extrabold gradient-text tracking-tight">MuseyamwaLabourConnect</h1>
                    <div className="flex items-center gap-4">
                        <Link to="/login" className="text-sm text-white/70 hover:text-white transition-colors">Sign In</Link>
                        <Link to="/register" className="btn-primary text-sm !py-2 !px-5">Get Started</Link>
                    </div>
                </header>

                <section className="relative z-10 max-w-5xl mx-auto text-center px-6 pt-20 pb-32">
                    <div className="badge-brand mb-6">
                        <Star size={14} className="mr-1" /> Zimbabwe's #1 Labour Marketplace
                    </div>
                    <h2 className="text-4xl md:text-6xl lg:text-7xl font-extrabold leading-tight mb-6">
                        Hire Skilled Workers
                        <span className="block gradient-text mt-2">Near You, Instantly</span>
                    </h2>
                    <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-10 leading-relaxed">
                        MuseyamwaLabourConnect connects employers with verified, GPS-tracked skilled workers
                        in real-time. Tokenized, secure, and built for Zimbabwe.
                    </p>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Link to="/register" className="btn-primary text-lg flex items-center gap-2">
                            Start Hiring <ArrowRight size={20} />
                        </Link>
                        <Link to="/register?role=employee" className="btn-secondary text-lg">
                            Find Work
                        </Link>
                    </div>
                </section>
            </div>



            {/* ── How It Works ── */}
            <section className="py-24 px-6 lg:px-16 bg-white/[0.02]">
                <h3 className="text-3xl font-bold text-center mb-16">How It Works</h3>
                <div className="max-w-3xl mx-auto space-y-8">
                    {[
                        { step: "1", title: "Create an Account", desc: "Register as an employer or worker. Purchase tokens via EcoCash or Innbucks." },
                        { step: "2", title: "Post or Browse Jobs", desc: "Employers post jobs; workers toggle online and appear on the live map." },
                        { step: "3", title: "Connect & Negotiate", desc: "Send offers, negotiate prices, and agree on terms — all in real-time." },
                        { step: "4", title: "Work & Rate", desc: "Complete the job, pay directly, and rate each other to build reputation." },
                    ].map(({ step, title, desc }) => (
                        <div key={step} className="flex items-start gap-6">
                            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-brand-500 to-teal-400 flex items-center justify-center text-lg font-bold">
                                {step}
                            </div>
                            <div>
                                <h4 className="text-lg font-semibold mb-1">{title}</h4>
                                <p className="text-white/50">{desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── Footer ── */}
            <footer className="py-12 px-6 lg:px-16 border-t border-white/5 text-center space-y-1">
                <p className="text-sm text-white/30">
                    © 2026 MuseyamwaLabourConnect. All rights reserved.
                </p>
                <p className="text-xs text-white/20">
                    Designed & Developed by <span className="text-brand-400/70 font-medium">TAGV Engineering Solutions (Pvt) Ltd</span>
                </p>
            </footer>
        </div>
    );
}
