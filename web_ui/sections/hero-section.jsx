'use client';

import { Sparkles, ArrowRight, ShieldCheck, Zap, Image as ImageIcon, Layers } from 'lucide-react';
import { motion } from 'framer-motion';

export default function HeroSection({ setActiveTab }) {
    return (
        <section className="relative flex flex-col items-center pt-16 pb-20 px-6 overflow-hidden">
            {/* Genesis Background Ambient Glow Orbs */}
            <motion.div 
                className="fixed inset-0 overflow-hidden -z-20 pointer-events-none"
                initial={{ opacity: 0.4 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8 }}
            >
                <div className="absolute rounded-full top-80 left-2/5 -translate-x-1/2 size-130 bg-[#D10A8A] blur-[120px] opacity-40" />
                <div className="absolute rounded-full top-80 right-0 -translate-x-1/2 size-130 bg-[#2E08CF] blur-[120px] opacity-40" />
                <div className="absolute rounded-full top-0 left-1/2 -translate-x-1/2 size-130 bg-[#F26A06] blur-[100px] opacity-50" />
            </motion.div>

            {/* Genesis Top Glass Pill */}
            <motion.div 
                className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/20 backdrop-blur-xl text-white text-xs mb-6 shadow-xl"
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1 }}
            >
                <Sparkles className="size-3.5 text-[#F26A06]" />
                <span>OpenCV Candidate Scoring & IOPaint LaMa Engine</span>
                <span className="bg-[#F26A06]/30 text-orange-200 px-2 py-0.5 rounded-full text-[10px] font-mono border border-[#F26A06]/40">100% Local</span>
            </motion.div>

            {/* Genesis Hero Heading */}
            <motion.h1 
                className="text-center text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-white max-w-4xl leading-[1.15]"
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
            >
                Surgically Erase Watermarks <br />
                <span className="bg-gradient-to-r from-[#F26A06] via-orange-400 to-[#D10A8A] bg-clip-text text-transparent">
                    Without Touching Your Background
                </span>
            </motion.h1>

            {/* Subtitle */}
            <motion.p 
                className="text-center text-slate-300 text-base md:text-lg max-w-2xl mt-6 leading-relaxed"
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
            >
                Privacy-first, local-execution AI image inpainting utility. Reconstructs background skin, fabric, and textures under translucent Gemini stars with zero quality loss.
            </motion.p>

            {/* Genesis Action Buttons */}
            <motion.div 
                className="flex flex-col sm:flex-row items-center gap-4 mt-8 w-full sm:w-auto"
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
            >
                <button 
                    onClick={() => setActiveTab('editor')}
                    className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3.5 rounded-full bg-gradient-to-r from-[#F26A06] to-[#D10A8A] hover:opacity-95 text-white font-bold text-sm shadow-xl shadow-orange-500/25 transition-all active:scale-95 cursor-pointer"
                >
                    <ImageIcon className="size-4.5" />
                    <span>Single Image Editor</span>
                    <ArrowRight className="size-4" />
                </button>

                <button 
                    onClick={() => setActiveTab('batch')}
                    className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-white font-semibold text-sm backdrop-blur-xl transition-all active:scale-95 cursor-pointer"
                >
                    <Layers className="size-4.5 text-emerald-400" />
                    <span>Batch Queue Processor</span>
                </button>
            </motion.div>

            {/* Feature Cards Grid */}
            <motion.div 
                className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mt-16 w-full"
                initial={{ y: 40, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.5 }}
            >
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl hover:border-[#F26A06]/40 transition-all">
                    <div className="size-10 rounded-xl bg-[#F26A06]/10 border border-[#F26A06]/30 flex items-center justify-center text-[#F26A06] mb-4">
                        <Sparkles className="size-5" />
                    </div>
                    <h3 className="font-bold text-white text-base mb-2">Multi-Signal Candidate Scoring</h3>
                    <p className="text-slate-400 text-xs leading-relaxed">
                        8-signal geometric descriptor evaluates aspect ratio, solidity, extent, isoperimetric quotient Q, and intensity.
                    </p>
                </div>

                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl hover:border-emerald-500/40 transition-all">
                    <div className="size-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4">
                        <Zap className="size-5" />
                    </div>
                    <h3 className="font-bold text-white text-base mb-2">IOPaint LaMa Neural Engine</h3>
                    <p className="text-slate-400 text-xs leading-relaxed">
                        PyTorch CUDA accelerated neural inpainting. Reconstructs complex background textures at full original resolution.
                    </p>
                </div>

                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl hover:border-purple-500/40 transition-all">
                    <div className="size-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-4">
                        <ShieldCheck className="size-5" />
                    </div>
                    <h3 className="font-bold text-white text-base mb-2">100% Privacy & Local</h3>
                    <p className="text-slate-400 text-xs leading-relaxed">
                        Zero telemetry, zero image ingestion, zero cloud API dependencies. All processing happens on your local GPU.
                    </p>
                </div>
            </motion.div>
        </section>
    );
}