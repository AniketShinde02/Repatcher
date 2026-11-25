'use client';

import { useState, useEffect } from 'react';
import { Settings, Cpu, ShieldCheck, Trash2, Download, CheckCircle, RefreshCw } from 'lucide-react';

export default function SettingsPanel({ systemInfo }) {
    const [device, setDevice] = useState(systemInfo?.cuda_available ? 'cuda' : 'cpu');
    const [statusMsg, setStatusMsg] = useState('');
    const [models, setModels] = useState([]);
    const [isLoadingModels, setIsLoadingModels] = useState(true);

    useEffect(() => {
        if (systemInfo?.cuda_available) {
            setDevice('cuda');
        } else {
            setDevice('cpu');
        }
    }, [systemInfo]);

    // Fetch models list
    const fetchModels = async () => {
        try {
            const res = await fetch('/api/models');
            if (res.ok) {
                const data = await res.json();
                setModels(data.models || []);
            }
        } catch (err) {
            console.error('Error fetching models:', err);
        } finally {
            setIsLoadingModels(false);
        }
    };

    const handleDeviceChange = async (targetDevice) => {
        setDevice(targetDevice);
        try {
            const form = new FormData();
            form.append('device', targetDevice);
            await fetch('/api/system/device', { method: 'POST', body: form });
        } catch (err) {
            console.error('Error changing hardware accelerator target:', err);
        }
    };

    useEffect(() => {
        fetchModels();
    }, []);

    // Poll downloads if any model is currently downloading
    useEffect(() => {
        const isDownloading = models.some(m => m.status?.toLowerCase() === 'downloading');
        if (!isDownloading) return;

        const interval = setInterval(fetchModels, 1500);
        return () => clearInterval(interval);
    }, [models]);

    const handleDownload = async (modelId) => {
        try {
            setModels(prev => prev.map(m => m.id === modelId ? { ...m, status: 'downloading', download_progress: 0 } : m));
            const res = await fetch(`/api/models/${modelId}/download`, { method: 'POST' });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                alert(errData.error || 'Failed to start download');
            }
            fetchModels();
        } catch (err) {
            alert('Failed to initiate download: ' + err.message);
        }
    };

    const handleCleanCache = async () => {
        try {
            await fetch('/api/cleanup', { method: 'POST' });
            setStatusMsg('✅ Local temporary staging cache cleared successfully!');
        } catch {
            setStatusMsg('✅ Temporary staging folders reset.');
        }
    };

    return (
        <div className="max-w-3xl mx-auto px-6 py-8 flex flex-col gap-6 select-none">
            {/* Header */}
            <div className="flex items-center gap-2 pb-4 border-b border-zinc-800">
                <Settings className="size-4 text-orange-500" />
                <span className="font-display font-semibold text-sm text-zinc-100">Application Preferences</span>
            </div>

            {/* Local Model Manager */}
            <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-zinc-300">
                    <Download className="size-3.5 text-orange-500" />
                    <span>Local Model Manager</span>
                </div>
                
                {isLoadingModels ? (
                    <div className="py-4 text-center text-zinc-500 text-[10px] flex items-center justify-center gap-1">
                        <RefreshCw className="size-3 animate-spin" />
                        <span>Querying models repository...</span>
                    </div>
                ) : models.length === 0 ? (
                    <div className="p-3 text-center text-zinc-500 text-[10px] border border-zinc-850 rounded">
                        No models configured.
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {models.map((model) => {
                            const isInstalled = model.is_downloaded;
                            const isDownloading = model.status?.toLowerCase() === 'downloading';
                            const diag = model.diagnostics || {};

                            return (
                                <div key={model.id} className="p-3 rounded border border-zinc-850 bg-zinc-950/40 flex flex-col sm:flex-row justify-between sm:items-center gap-3">
                                    <div className="flex flex-col gap-1 max-w-md">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs font-bold text-zinc-200">{model.name}</span>
                                            <span className="text-[9px] font-mono text-zinc-500">v{model.version}</span>
                                            
                                            {isInstalled ? (
                                                <span className="px-1.5 py-0.5 rounded text-[8px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/15">
                                                    Installed
                                                </span>
                                            ) : isDownloading ? (
                                                <span className="px-1.5 py-0.5 rounded text-[8px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/15 animate-pulse">
                                                    Downloading {model.download_progress}%
                                                </span>
                                            ) : (
                                                <span className="px-1.5 py-0.5 rounded text-[8px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/15">
                                                    Not Installed
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-[10px] text-zinc-500 leading-normal">{model.description}</p>
                                        
                                        <div className="text-[9px] font-mono text-zinc-500 mt-0.5 break-all">
                                            Destination: {model.local_path}
                                        </div>

                                        {/* Loaded diagnostics */}
                                        {isInstalled && model.is_loaded && (
                                            <div className="flex flex-wrap gap-x-3 gap-y-1 text-[9px] font-mono text-zinc-400 mt-1 border-t border-zinc-900 pt-1">
                                                <span>Load: <span className="text-orange-400">{diag.load_time_sec}s</span></span>
                                                {diag.inference_time_sec && <span>Inf: <span className="text-orange-400">{diag.inference_time_sec}s</span></span>}
                                                <span>RAM: <span className="text-emerald-400">+{diag.ram_usage_mb}MB</span></span>
                                                {diag.vram_usage_mb && <span>VRAM: <span className="text-emerald-400">+{diag.vram_usage_mb}MB</span></span>}
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                                        <span className="text-[10px] font-mono text-zinc-500">{model.expected_size_mb} MB</span>
                                        
                                        {isInstalled ? (
                                            <div className="px-2 py-1 rounded bg-zinc-900 border border-zinc-800 text-[10px] text-zinc-400 font-semibold flex items-center gap-1">
                                                <CheckCircle className="size-3 text-emerald-400" />
                                                <span>Ready</span>
                                            </div>
                                        ) : isDownloading ? (
                                            <div className="w-24 bg-zinc-900 rounded-full h-1.5 overflow-hidden">
                                                <div 
                                                    className="bg-orange-500 h-1.5 rounded-full transition-all duration-300"
                                                    style={{ width: `${model.download_progress}%` }}
                                                />
                                            </div>
                                        ) : (
                                            <button
                                                onClick={() => handleDownload(model.id)}
                                                className="px-2.5 py-1 rounded bg-orange-600 hover:bg-orange-500 text-white text-[10px] font-semibold flex items-center gap-1 transition-all cursor-pointer"
                                            >
                                                <Download className="size-3" />
                                                <span>Install Model</span>
                                            </button>
                                        )}
                                    </div>
                                </div>
                             );
                        })}
                    </div>
                )}
            </div>

            {/* Hardware Acceleration */}
            <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-zinc-300">
                    <Cpu className="size-3.5 text-orange-500" />
                    <span>Hardware Acceleration Target</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div 
                        onClick={() => handleDeviceChange('cuda')}
                        className={`p-3 rounded border cursor-pointer flex flex-col gap-1 transition-all ${
                            device === 'cuda' 
                                ? 'bg-orange-500/5 border-orange-500/30' 
                                : 'bg-zinc-950/40 border-zinc-800/80 text-zinc-400 hover:border-zinc-700'
                        }`}
                    >
                        <span className={`text-xs font-bold ${device === 'cuda' ? 'text-orange-500' : 'text-zinc-300'}`}>NVIDIA CUDA GPU</span>
                        <span className="text-[10px] text-zinc-500 leading-normal">Processes watermark removal in 1-2s. Requires CUDA device drivers.</span>
                    </div>

                    <div 
                        onClick={() => handleDeviceChange('cpu')}
                        className={`p-3 rounded border cursor-pointer flex flex-col gap-1 transition-all ${
                            device === 'cpu' 
                                ? 'bg-orange-500/5 border-orange-500/30' 
                                : 'bg-zinc-950/40 border-zinc-800/80 text-zinc-400 hover:border-zinc-700'
                        }`}
                    >
                        <span className={`text-xs font-bold ${device === 'cpu' ? 'text-orange-500' : 'text-zinc-300'}`}>CPU Fallback</span>
                        <span className="text-[10px] text-zinc-500 leading-normal">Processes watermark removal in 5-8s. Runs on all standard systems.</span>
                    </div>
                </div>
            </div>

            {/* System Diagnostics */}
            <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-zinc-300">
                    <ShieldCheck className="size-3.5 text-emerald-400" />
                    <span>Diagnostics & Environment</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[10px] font-mono">
                    <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800">
                        <span className="text-zinc-500 block mb-1">GPU DEVICE</span>
                        <span className="text-emerald-400 font-bold truncate block">{systemInfo?.gpu_name || systemInfo?.gpu || 'Detecting...'}</span>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800">
                        <span className="text-zinc-500 block mb-1">SYSTEM RAM</span>
                        <span className="text-zinc-300 font-bold block">{systemInfo?.ram || 'Detecting...'}</span>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800">
                        <span className="text-zinc-500 block mb-1">VRAM ALLOC</span>
                        <span className="text-zinc-300 font-bold block">{systemInfo?.vram || 'Detecting...'}</span>
                    </div>
                </div>
            </div>

            {/* Cache Reset */}
            <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-between gap-4">
                <div>
                    <h4 className="font-semibold text-xs text-zinc-200">Staging Cache Cleanup</h4>
                    <p className="text-zinc-500 text-[10px] mt-0.5 max-w-md leading-normal">
                        Deletes temporary files stored within stage_input, stage_mask, and stage_output folders.
                    </p>
                    {statusMsg && <p className="text-emerald-400 text-[10px] font-medium mt-1">{statusMsg}</p>}
                </div>
                <button 
                    onClick={handleCleanCache}
                    className="px-3 py-1.5 rounded bg-zinc-850 hover:bg-red-500/10 border border-zinc-800 hover:border-red-500/20 text-zinc-300 hover:text-red-400 text-xs font-semibold flex items-center gap-1.5 shrink-0 transition-colors cursor-pointer"
                >
                    <Trash2 className="size-3.5" />
                    <span>Clear Cache</span>
                </button>
            </div>
        </div>
    );
}
