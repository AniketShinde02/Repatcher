import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

export async function GET(request, { params }) {
    // Await params as required by Next.js 14+
    const resolvedParams = await params;
    const batch_id = resolvedParams.batch_id;
    const filename = resolvedParams.filename;
    
    try {
        const fetchUrl = `${config.backendUrl}/batch/${batch_id}/download/${encodeURIComponent(filename)}`;
        const backendRes = await fetch(fetchUrl, {
            method: 'GET',
        });

        if (!backendRes.ok) {
            const errorMsg = await backendRes.text().catch(() => 'File not found');
            return new NextResponse(errorMsg, { status: backendRes.status });
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
        console.error('[batch download] Error proxying file:', error);
        return new NextResponse('Backend offline or unavailable', { status: 503 });
    }
}
