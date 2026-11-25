import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function GET() {
    try {
        const backendRes = await fetch(`${config.backendUrl}/models`, {
            cache: 'no-store',
        });

        if (!backendRes.ok) {
            return NextResponse.json({ models: [], error: 'Backend error' }, { status: backendRes.status });
        }

        const data = await backendRes.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ models: [], error: 'Backend offline' }, { status: 503 });
    }
}
