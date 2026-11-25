import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function POST(request, { params }) {
    const { model_id } = await params;
    try {
        const backendRes = await fetch(`${config.backendUrl}/models/${model_id}/download`, {
            method: 'POST',
        });

        if (!backendRes.ok) {
            const errData = await backendRes.json().catch(() => ({}));
            return NextResponse.json({ success: false, error: errData.detail || 'Download initiation failed' }, { status: backendRes.status });
        }

        const data = await backendRes.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ success: false, error: 'Backend offline' }, { status: 503 });
    }
}
