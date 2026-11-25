import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function GET(request, { params }) {
    const resolvedParams = await params;
    const batch_id = resolvedParams.batch_id;
    try {
        const backendRes = await fetch(`${config.backendUrl}/batch/${batch_id}/download`, {
            method: 'GET',
        });

        if (!backendRes.ok) {
            return new NextResponse('Error generating ZIP', { status: backendRes.status });
        }

        const headers = new Headers();
        const ct = backendRes.headers.get('content-type');
        const cd = backendRes.headers.get('content-disposition');
        const cl = backendRes.headers.get('content-length');
        
        if (ct) headers.set('content-type', ct);
        if (cd) headers.set('content-disposition', cd);
        if (cl) headers.set('content-length', cl);

        return new NextResponse(backendRes.body, {
            status: backendRes.status,
            headers,
        });
    } catch {
        console.error('[batch/download] Error proxying GET request:', error);
        return new NextResponse('Backend offline', { status: 503 });
    }
}

export async function POST(request, { params }) {
    const resolvedParams = await params;
    const batch_id = resolvedParams.batch_id;
    try {
        const body = await request.json();
        const backendRes = await fetch(`${config.backendUrl}/batch/${batch_id}/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!backendRes.ok) {
            return new NextResponse('Error generating ZIP', { status: backendRes.status });
        }

        const headers = new Headers();
        const ct = backendRes.headers.get('content-type');
        const cd = backendRes.headers.get('content-disposition');
        const cl = backendRes.headers.get('content-length');
        
        if (ct) headers.set('content-type', ct);
        if (cd) headers.set('content-disposition', cd);
        if (cl) headers.set('content-length', cl);

        return new NextResponse(backendRes.body, {
            status: backendRes.status,
            headers,
        });
    } catch {
        console.error('[batch/download] Error proxying POST request:', error);
        return new NextResponse('Backend offline', { status: 503 });
    }
}
