'use client';

import { Info, Github, ShieldCheck, FileText, Cpu, Zap } from 'lucide-react';

export default function AboutSection({ systemInfo }) {
    const version = '1.6.0';
    const engine = 'IOPaint LaMa (Fast Fourier Convolution)';
    const modelFile = 'big-lama.pt (~196 MB)';
    const license = 'Apache License 2.0';
    const device = systemInfo?.cuda_available
        ? `GPU — ${systemInfo.gpu_name || 'CUDA'}`
        : 'CPU';

    return (
        <div className="max-w-3xl mx-auto px-6 py-8 flex flex-col gap-6 select-none animate-fadeIn">
            {/* Header */}
            <div className="flex items-center gap-2 pb-4 border-b border-zinc-800">
                <Info className="size-4 text-orange-500" />
                <span className="font-display font-semibold text-sm text-zinc-100">About — AI Watermark Remover</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Description + version */}
                <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 flex flex-col justify-between gap-3">
                    <div>
                        <h3 className="font-semibold text-zinc-200 text-xs mb-2">Technical Description</h3>
                        <p className="text-zinc-400 text-[11px] leading-relaxed">
                            Traditional watermark removal tools resort to destructive cropping or heavy blurs.
                            This local utility uses OpenCV Top-Hat morphological filters to isolate translucent
                            4-pointed star regions, then runs neural inpainting via the LaMa model
                            (Fast Fourier Convolution) to restore underlying textures at full original resolution.
                            All processing is fully local — no data leaves your machine.
                        </p>
                    </div>

                    <div className="flex flex-col gap-1.5 pt-3 border-t border-zinc-800">
                        <div className="flex justify-between text-[10px] font-mono">
                            <span className="text-zinc-500">VERSION</span>
                            <span className="text-orange-400 font-semibold">{version}</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-mono">
                            <span className="text-zinc-500">ENGINE</span>
                            <span className="text-zinc-300">{engine}</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-mono">
                            <span className="text-zinc-500">MODEL FILE</span>
                            <span className="text-zinc-300">{modelFile}</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-mono">
                            <span className="text-zinc-500">DEVICE</span>
                            <span className="text-emerald-400 font-semibold">{device}</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-mono">
                            <span className="text-zinc-500">LICENSE</span>
                            <span className="text-zinc-400">{license}</span>
                        </div>
                    </div>
                </div>

                {/* Links + security */}
                <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 flex flex-col gap-3">
                    <h3 className="font-semibold text-zinc-200 text-xs mb-1">Source &amp; Security</h3>

                    <a
                        href="https://github.com/Sanster/IOPaint"
                        target="_blank"
                        rel="noreferrer"
                        className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800 hover:border-orange-500/30 text-zinc-300 text-xs flex items-center justify-between transition-colors"
                    >
                        <span className="flex items-center gap-2 text-[11px]">
                            <Github className="size-3.5 text-orange-500" />
                            <span>IOPaint — Neural Inpainting Engine</span>
                        </span>
                        <span className="text-zinc-500 text-[9px] font-mono">Open Source</span>
                    </a>

                    <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800 text-zinc-300 text-[11px] flex items-center gap-2">
                        <ShieldCheck className="size-3.5 text-emerald-400" />
                        <span>Local-first execution — no images uploaded externally</span>
                    </div>

                    <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800 text-zinc-300 text-[11px] flex items-center gap-2">
                        <Cpu className="size-3.5 text-blue-400" />
                        <span>CUDA GPU acceleration supported, CPU fallback automatic</span>
                    </div>

                    <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800 text-zinc-300 text-[11px] flex items-center gap-2">
                        <Zap className="size-3.5 text-yellow-400" />
                        <span>Model loaded once per session — no per-image reload</span>
                    </div>

                    <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800 text-zinc-300 text-[11px] flex items-center gap-2">
                        <FileText className="size-3.5 text-pink-400" />
                        <span>Governed by Apache License 2.0</span>
                    </div>
                </div>
            </div>

            {/* Acknowledgements */}
            <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800">
                <h3 className="font-semibold text-zinc-200 text-xs mb-3">Acknowledgements</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px] font-mono">
                    {[
                        { name: 'IOPaint / LaMa', role: 'Neural inpainting engine', url: 'https://github.com/Sanster/IOPaint' },
                        { name: 'PyTorch', role: 'Deep learning runtime', url: 'https://pytorch.org' },
                        { name: 'FastAPI', role: 'Backend REST API', url: 'https://fastapi.tiangolo.com' },
                        { name: 'OpenCV', role: 'Image processing / detection', url: 'https://opencv.org' },
                        { name: 'Next.js 16', role: 'Frontend framework', url: 'https://nextjs.org' },
                        { name: 'Lucide Icons', role: 'UI icon set', url: 'https://lucide.dev' },
                    ].map(({ name, role, url }) => (
                        <a
                            key={name}
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="p-2 rounded bg-zinc-950/60 border border-zinc-800 hover:border-orange-500/20 transition-colors flex flex-col gap-0.5"
                        >
                            <span className="text-orange-400 font-semibold">{name}</span>
                            <span className="text-zinc-500">{role}</span>
                        </a>
                    ))}
                </div>
            </div>
        </div>
    );
}
