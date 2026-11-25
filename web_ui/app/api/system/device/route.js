import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function POST(request) {
    try {
        const formData = await request.formData();
        const backendRes = await fetch(`${config.backendUrl}/system/device`, {
            method: 'POST',
            body: formData,
        });

        if (!backendRes.ok) {
            return NextResponse.json({ success: false, error: 'Failed to update accelerator target' }, { status: backendRes.status });
        }

        const data = await backendRes.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Device update error:", error);
        return NextResponse.json({ success: false, error: 'Backend offline' }, { status: 503 });
    }
}
