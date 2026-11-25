'use client';

import { Cpu, Sparkles } from 'lucide-react';
import { branding } from '@/config/branding';

export default function Navbar({ activeTab, setActiveTab, systemInfo }) {
    const navItems = [
        { id: 'editor', name: 'Single Editor' },
        { id: 'batch', name: 'Batch Queue' },
        { id: 'settings', name: 'Settings' },
        { id: 'about', name: 'About' },
    ];

    const isOffline = systemInfo?.gpu === 'Backend Offline';

    return (
        <header className="sticky top-0 z-50 flex w-full items-center justify-between px-6 py-3 bg-zinc-900 border-b border-zinc-800 shadow-md">
            {/* Tool Brand */}
            <div 
                onClick={() => setActiveTab('editor')}
                className="flex items-center gap-2.5 cursor-pointer group"
            >
                <div className="size-7 rounded bg-orange-600 flex items-center justify-center text-white shadow-sm">
                    <Sparkles className="size-4" />
                </div>
                <div>
                    <span className="font-display font-bold text-sm text-zinc-100 tracking-tight block">
                        {branding.productName}
                    </span>
                </div>
            </div>

            {/* Desktop Toolbar Navigation Pills */}
            <div className="flex items-center gap-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => setActiveTab(item.id)}
                        className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                            activeTab === item.id
                                ? 'bg-zinc-800 text-white border border-zinc-700/80'
                                : 'text-zinc-400 hover:text-zinc-200'
                        }`}
                    >
                        {item.name}
                    </button>
                ))}
            </div>

            {/* Hardware Status / Desktop Info */}
            <div className="flex items-center gap-2">
                <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-[10px] font-mono font-medium ${
                    isOffline 
                        ? 'bg-red-500/10 border-red-500/30 text-red-400' 
                        : 'bg-zinc-950 border-zinc-800 text-zinc-400'
                }`}>
                    <Cpu className="size-3 shrink-0" />
                    <span>{systemInfo?.gpu || 'Initializing Diagnostics...'}</span>
                </div>
            </div>
        </header>
    );
}
