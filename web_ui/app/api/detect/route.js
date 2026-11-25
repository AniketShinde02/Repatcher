import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function POST(request) {
    try {
        const formData = await request.formData();

        const backendRes = await fetch(`${config.backendUrl}/detect`, {
            method: 'POST',
            body: formData,
        });

        if (!backendRes.ok) {
            const err = await backendRes.json().catch(() => ({}));
            let errorMsg = err?.detail?.message || 'Detection failed';
            if (backendRes.status === 429) errorMsg = 'Too many requests. Please wait and try again.';
            return NextResponse.json(
                { success: false, error: errorMsg },
                { status: backendRes.status }
            );
        }

        const data = await backendRes.json();
        return NextResponse.json({ success: true, ...data });
    } catch {
        console.error('[/api/detect] Backend unreachable:', error.message);
        return NextResponse.json({
            success: false,
            detected: false,
            confidence: 0,
            confidence_level: 'NONE',
            detections: [],
            error: 'Backend offline — processing engine is unreachable.',
            mask_png_b64: null,
        }, { status: 503 });
    }
}
