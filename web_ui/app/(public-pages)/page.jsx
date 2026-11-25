'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/navbar';
import WatermarkEditor from '@/components/watermark-editor';
import BatchProcessor from '@/components/batch-processor';
import SettingsPanel from '@/components/settings-panel';
import AboutSection from '@/components/about-section';

export default function Page() {
    const [activeTab, setActiveTab] = useState('editor');
    const [systemInfo, setSystemInfo] = useState({
        gpu: '',
        ram: '',
        vram: '',
        cuda_available: false,
    });

    useEffect(() => {
        let isMounted = true;
        const fetchSystemInfo = async () => {
            try {
                const res = await fetch('/api/system');
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    if (isMounted) {
                        setSystemInfo({
                            gpu: errorData.gpu_label || 'Backend Offline',
                            ram: '',
                            vram: '',
                            cuda_available: false,
                        });
                    }
                    return;
                }
                const data = await res.json();
                if (!isMounted) return;

                const gpuLabel = data.gpu_label;
                const ramLabel = data.ram_total_gb ? `${data.ram_total_gb} GB` : '';
                const vramLabel = data.vram_total_gb ? `${data.vram_total_gb} GB` : '';

                setSystemInfo({
                    gpu: gpuLabel,
                    ram: ramLabel,
                    vram: vramLabel,
                    cuda_available: data.cuda_available ?? false,
                    gpu_name: data.gpu_name ?? 'None',
                    model_loaded: data.model_loaded ?? false,
                });
            } catch {
                if (isMounted) {
                    setSystemInfo({
                        gpu: 'Backend Offline',
                        ram: '',
                        vram: '',
                        cuda_available: false,
                    });
                }
            }
        };

        fetchSystemInfo();
        return () => { isMounted = false; };
    }, []);

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-200 font-sans selection:bg-orange-600 selection:text-white flex flex-col">
            {/* Software App Navbar Header */}
            <Navbar activeTab={activeTab} setActiveTab={setActiveTab} systemInfo={systemInfo} />

            {/* View Switcher */}
            <main>
                {activeTab === 'editor' && <WatermarkEditor />}
                {activeTab === 'batch' && <BatchProcessor />}
                {activeTab === 'settings' && <SettingsPanel systemInfo={systemInfo} />}
                {activeTab === 'about' && <AboutSection systemInfo={systemInfo} />}
            </main>
        </div>
    );
}

