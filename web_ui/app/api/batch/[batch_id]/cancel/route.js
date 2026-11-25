import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function POST(request, { params }) {
    const { batch_id } = await params;
    try {
        const backendRes = await fetch(`${config.backendUrl}/batch/${batch_id}/cancel`, {
            method: 'POST',
        });

        if (!backendRes.ok) {
            return NextResponse.json({ success: false, error: 'Failed to cancel batch' }, { status: backendRes.status });
        }

        const data = await backendRes.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Batch cancel error:", error);
        return NextResponse.json({ success: false, error: 'Backend offline' }, { status: 503 });
    }
}
