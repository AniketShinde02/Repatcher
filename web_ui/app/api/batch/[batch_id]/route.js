import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function GET(request, { params }) {
    const { batch_id } = await params;
    try {
        const backendRes = await fetch(`${config.backendUrl}/batch/${batch_id}`, {
            cache: 'no-store',
        });

        if (!backendRes.ok) {
            return NextResponse.json({ success: false, error: 'Failed to retrieve batch status' }, { status: backendRes.status });
        }

        const data = await backendRes.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ success: false, error: 'Backend offline' }, { status: 503 });
    }
}
