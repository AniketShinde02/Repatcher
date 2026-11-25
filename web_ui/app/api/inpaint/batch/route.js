import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function POST(request) {
    try {
        const formData = await request.formData();
        const backendRes = await fetch(`${config.backendUrl}/batch`, {
            method: 'POST',
            body: formData,
        });

        if (!backendRes.ok) {
            const errData = await backendRes.json().catch(() => ({}));
            return NextResponse.json({ success: false, error: errData.detail || 'Batch initiation failed' }, { status: backendRes.status });
        }

        const data = await backendRes.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ success: false, error: 'Backend offline' }, { status: 503 });
    }
}
