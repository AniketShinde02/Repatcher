/**
 * Next.js /api/system proxy route
 * Forwards system hardware diagnostics request to FastAPI backend.
 * Never returns hardcoded hardware strings.
 */

import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function GET() {
    try {
        const backendRes = await fetch(`${config.backendUrl}/system`, {
            cache: 'no-store',
        });

        if (!backendRes.ok) {
            return NextResponse.json({
                cuda_available: false,
                gpu_name: 'Unavailable (Backend Error)',
                gpu_label: 'Backend Offline',
                platform: 'Unknown',
                ram_total_gb: 0,
                vram_total_gb: 0,
                model_loaded: false,
                offline: true,
            }, { status: backendRes.status });
        }

        const data = await backendRes.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({
            cuda_available: false,
            gpu_name: 'None (Backend Offline)',
            gpu_label: 'Backend Offline',
            platform: 'Unknown',
            ram_total_gb: 0,
            vram_total_gb: 0,
            model_loaded: false,
            offline: true,
            error: 'Could not connect to processing engine',
        }, { status: 503 });
    }
}
