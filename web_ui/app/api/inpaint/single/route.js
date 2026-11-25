/**
 * Next.js /api/inpaint/single proxy route
 *
 * 9A Quality Contract:
 * - Does NOT hardcode .png extension or image/png MIME type
 * - Forwards raw multipart form to FastAPI /process
 * - Returns result in source format with correct MIME type
 * - Never silently converts JPEG → PNG
 */

import { NextResponse } from 'next/server';
import { config } from '@/config/runtime';

// MIME → file extension map for download filename
const MIME_EXT = {
    'image/jpeg': '.jpg',
    'image/png':  '.png',
    'image/webp': '.webp',
    'image/bmp':  '.bmp',
    'image/tiff': '.tiff',
};

export async function POST(request) {
    try {
        const formData = await request.formData();

        // Forward the entire formData to FastAPI /process
        const backendRes = await fetch(`${config.backendUrl}/process`, {
            method: 'POST',
            body: formData,
        });

        if (!backendRes.ok) {
            const err = await backendRes.json().catch(() => ({}));
            let errorMsg = err?.detail?.message || 'Processing failed';
            if (backendRes.status === 429) errorMsg = 'Too many requests. Please wait and try again.';
            if (backendRes.status === 413) errorMsg = 'Image file is too large to process.';
            
            return NextResponse.json(
                { success: false, error: errorMsg },
                { status: backendRes.status }
            );
        }

        const processData = await backendRes.json();
        const { job_id, source_format } = processData;

        if (!job_id) {
            return NextResponse.json({ success: false, error: 'No job_id returned' }, { status: 500 });
        }

        // Fetch the result image from FastAPI /job/{job_id}
        const jobRes = await fetch(`${config.backendUrl}/job/${job_id}`);

        if (!jobRes.ok) {
            return NextResponse.json({ success: false, error: 'Could not retrieve job output' }, { status: 500 });
        }

        // Get actual MIME type from FastAPI response (format-preserving)
        const mime = jobRes.headers.get('content-type') || 'image/png';
        const ext  = MIME_EXT[mime] || source_format || '.jpg';

        const imageBuffer = Buffer.from(await jobRes.arrayBuffer());
        const base64 = imageBuffer.toString('base64');

        // Return data URI with correct MIME type — not always image/png
        return NextResponse.json({
            success:    true,
            resultUrl:  `data:${mime};base64,${base64}`,
            format:     ext,
            mime:       mime,
            detections: processData.detections,
            confidence: processData.confidence_level,
            message:    processData.message,
        });

    } catch (error) {
        console.error('[/api/inpaint/single] Backend unreachable:', error.message);
        return NextResponse.json(
            { success: false, error: 'Backend offline — processing engine is unreachable.' },
            { status: 503 }
        );
    }
}
