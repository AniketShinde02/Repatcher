'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import {
    Upload, Sparkles, Image as ImageIcon, Download,
    RefreshCw, ShieldAlert, CheckCircle2,
    AlertTriangle, XCircle, Eye, Move, Edit2, Eraser, ZoomIn, ZoomOut, Maximize2, Trash2, ChevronDown, ChevronUp
} from 'lucide-react';

const CONFIDENCE_CONFIG = {
    HIGH:   { label: 'Watermark detected.', color: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5', icon: CheckCircle2 },
    MEDIUM: { label: 'Possible watermark detected. Review before processing.', color: 'text-amber-400 border-amber-500/20 bg-amber-500/5', icon: AlertTriangle },
    LOW:    { label: 'No confident watermark detected.', color: 'text-zinc-400 border-zinc-700 bg-zinc-800/10', icon: ShieldAlert },
    NONE:   { label: 'No confident watermark detected.', color: 'text-zinc-500 border-zinc-850 bg-zinc-900/10', icon: XCircle },
};

export default function WatermarkEditor() {
    const [imageFile, setImageFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [processedUrl, setProcessedUrl] = useState(null);
    const [metadata, setMetadata] = useState(null);

    // Detection / Mask state
    const [detectResult, setDetectResult] = useState(null);
    const [isDetecting, setIsDetecting] = useState(false);
    
    // UI Mode / Canvas state
    const [toolMode, setToolMode] = useState('navigate'); // 'navigate', 'draw', 'erase'
    const [brushSize, setBrushSize] = useState(24);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const [isDrawing, setIsDrawing] = useState(false);
    const [panStart, setPanStart] = useState({ x: 0, y: 0 });

    // Detection Star parameters
    const [sensitivity, setSensitivity] = useState(160);
    const [padding, setPadding] = useState(12);

    // Processing state
    const [isProcessing, setIsProcessing] = useState(false);
    const [statusLog, setStatusLog] = useState('');
    const [errorMsg, setErrorMsg] = useState('');

    // Comparison slider pos
    const [sliderPos, setSliderPos] = useState(50);
    const [isDraggingSlider, setIsDraggingSlider] = useState(false);

    // Model status
    const [models, setModels] = useState([]);
    const [activeModelId, _setActiveModelId] = useState('lama');
    const [showDiagnostics, setShowDiagnostics] = useState(false);

    const fileInputRef = useRef(null);
    const canvasRef = useRef(null);
    const imageRef = useRef(null);
    const viewportRef = useRef(null);
    const sliderContainerRef = useRef(null);

    // Canvas smooth painting refs
    const lastX = useRef(null);
    const lastY = useRef(null);
    const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 });
    const [showCursor, setShowCursor] = useState(false);

    // Download format and comparison mode
    const [downloadFormat, setDownloadFormat] = useState('png'); // 'png', 'jpg', 'webp'
    const [comparisonMode, setComparisonMode] = useState('slider'); // 'slider', 'split'

    // Fetch models list
    const fetchModels = async () => {
        try {
            const res = await fetch('/api/models');
            if (res.ok) {
                const data = await res.json();
                setModels(data.models || []);
            }
        } catch (err) {
            console.error('Error fetching models in editor:', err);
        }
    };

    useEffect(() => {
        fetchModels();
    }, []);

    // Poll downloads if any model is currently downloading
    useEffect(() => {
        const isDownloading = models.some(m => m.status === 'downloading');
        if (!isDownloading) return;

        const interval = setInterval(fetchModels, 1500);
        return () => clearInterval(interval);
    }, [models]);

    const handleDownload = async (modelId) => {
        try {
            setModels(prev => prev.map(m => m.id === modelId ? { ...m, status: 'downloading', download_progress: 0 } : m));
            const res = await fetch(`/api/models/${modelId}/download`, { method: 'POST' });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                alert(errData.error || 'Failed to start download');
            }
            fetchModels();
        } catch (err) {
            alert('Failed to initiate download: ' + err.message);
        }
    };

    const activeModel = models.find(m => m.id === activeModelId);
    const isModelInstalled = activeModel ? activeModel.is_downloaded : true; // Keep true initially to prevent layout flash

    // ─── File load ────────────────────────────────────────────────────────
    const loadImage = useCallback((file) => {
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const allowedExts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'];
        const isImageMime = file.type.startsWith('image/');

        if (!allowedExts.includes(ext) && !isImageMime) {
            setErrorMsg(`Unsupported file type: "${file.name}". Only images (JPG, PNG, WEBP, BMP, TIFF) are supported.`);
            return;
        }
        setImageFile(file);
        setPreviewUrl(URL.createObjectURL(file));
        setProcessedUrl(null);
        setDetectResult(null);
        setStatusLog('');
        setErrorMsg('');
        setZoom(1);
        setPan({ x: 0, y: 0 });
        setToolMode('navigate');

        const img = new Image();
        img.onload = () => setMetadata({
            name: file.name,
            width: img.naturalWidth,
            height: img.naturalHeight,
            size: (file.size / 1024).toFixed(1) + ' KB',
            type: file.type.split('/')[1]?.toUpperCase() || 'PNG'
        });
        img.src = URL.createObjectURL(file);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file) loadImage(file);
    }, [loadImage]);

    // Initialize/Resize mask canvas when previewUrl/image changes
    useEffect(() => {
        if (!previewUrl || !canvasRef.current || !metadata) return;
        const canvas = canvasRef.current;
        canvas.width = metadata.width;
        canvas.height = metadata.height;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }, [previewUrl, metadata]);

    // Load auto-detection mask into canvas
    const loadDetectionMask = (maskB64) => {
        if (!canvasRef.current || !maskB64) return;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        const maskImg = new Image();
        maskImg.onload = () => {
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = canvas.width;
            tempCanvas.height = canvas.height;
            const tempCtx = tempCanvas.getContext('2d');
            tempCtx.drawImage(maskImg, 0, 0, canvas.width, canvas.height);

            const imgData = tempCtx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imgData.data;
            for (let i = 0; i < data.length; i += 4) {
                if (data[i] > 20 || data[i+1] > 20 || data[i+2] > 20) {
                    data[i] = 239;     // R
                    data[i+1] = 68;    // G
                    data[i+2] = 68;    // B
                    data[i+3] = 153;   // Alpha (~0.6 opacity)
                } else {
                    data[i+3] = 0;     // Transparent background
                }
            }
            ctx.putImageData(imgData, 0, 0);
        };
        maskImg.src = `data:image/png;base64,${maskB64}`;
    };

    // ─── STEP 1: Scan / Detect ───────────────────────────────────────────
    const runDetect = async () => {
        if (!imageFile) return;
        setIsDetecting(true);
        setStatusLog('Scanning image for candidate stars...');
        setErrorMsg('');

        try {
            const form = new FormData();
            form.append('file', imageFile);
            form.append('sensitivity', sensitivity);
            form.append('padding', padding);

            const res = await fetch('/api/detect', { method: 'POST', body: form });
            const data = await res.json();
            
            if (!res.ok || !data.success) {
                throw new Error(data.error || `Server error: ${res.status}`);
            }

            setDetectResult(data);
            if (data.mask_png_b64) {
                loadDetectionMask(data.mask_png_b64);
                setToolMode('draw');
            }

            if (data.confidence_level === 'HIGH') {
                setStatusLog('Detection complete. Watermark identified.');
            } else if (data.confidence_level === 'MEDIUM') {
                setStatusLog('Detection finished. Possible watermark found. Review required.');
            } else {
                setStatusLog('Scanning complete. No confident watermark detected.');
            }
        } catch (err) {
            setErrorMsg(`Detection failed: ${err.message}`);
            setStatusLog('');
        } finally {
            setIsDetecting(false);
        }
    };

    // Export transparent red mask as solid black/white binary mask
    const getBinaryMaskBlob = () => {
        return new Promise((resolve) => {
            const maskCanvas = canvasRef.current;
            if (!maskCanvas) return resolve(null);

            const exportCanvas = document.createElement('canvas');
            exportCanvas.width = maskCanvas.width;
            exportCanvas.height = maskCanvas.height;
            const exportCtx = exportCanvas.getContext('2d');

            exportCtx.fillStyle = 'black';
            exportCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);

            const maskCtx = maskCanvas.getContext('2d');
            const imgData = maskCtx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
            const data = imgData.data;

            for (let i = 0; i < data.length; i += 4) {
                const alpha = data[i+3];
                if (alpha > 10) {
                    data[i] = 255;
                    data[i+1] = 255;
                    data[i+2] = 255;
                    data[i+3] = 255;
                } else {
                    data[i] = 0;
                    data[i+1] = 0;
                    data[i+2] = 0;
                    data[i+3] = 255;
                }
            }
            exportCtx.putImageData(imgData, 0, 0);
            exportCanvas.toBlob((blob) => resolve(blob), 'image/png');
        });
    };

    // ─── STEP 2: Inpaint Execution ─────────────────────────────────────────
    const runInpaint = async () => {
        if (!imageFile) return;

        // Guard: Validate the mask canvas has painted pixels before calling backend
        const canvas = canvasRef.current;
        if (canvas) {
            const ctx = canvas.getContext('2d');
            const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imgData.data;
            let hasMaskPixels = false;
            for (let i = 3; i < data.length; i += 4) {
                if (data[i] > 10) { hasMaskPixels = true; break; }
            }
            if (!hasMaskPixels) {
                setErrorMsg('No area selected. Use the Paint tool to mark the watermark region before processing.');
                return;
            }
        }

        setIsProcessing(true);
        setStatusLog('Executing LaMa neural inpainting at full resolution...');
        setErrorMsg('');

        try {
            const form = new FormData();
            form.append('file', imageFile);

            const maskBlob = await getBinaryMaskBlob();
            if (maskBlob) {
                form.append('mask_file', maskBlob, 'mask.png');
            }

            form.append('sensitivity', sensitivity);
            form.append('padding', padding);

            const res = await fetch('/api/inpaint/single', { method: 'POST', body: form });
            const data = await res.json();

            if (!res.ok || !data.success) {
                throw new Error(data.error || `Server error: ${res.status}`);
            }

            if (data.resultUrl) {
                setProcessedUrl(data.resultUrl);
                setStatusLog('Watermark removed. Background textures preserved.');
                fetchModels(); // Refresh load and inference diagnostics
            } else {
                throw new Error('Inpainting succeeded but no image was returned.');
            }
        } catch (err) {
            setErrorMsg(`Processing error: ${err.message}`);
            setStatusLog('');
        } finally {
            setIsProcessing(false);
        }
    };


    // ─── Viewport Interaction ─────────────────────────────────────────────
    const handleZoom = (factor) => {
        if (factor === 0) {
            setZoom(1);
            setPan({ x: 0, y: 0 });
        } else {
            setZoom(z => Math.max(0.25, Math.min(8, z + factor)));
        }
    };

    const handleCanvasInteractionStart = (e) => {
        if (e.preventDefault) e.preventDefault();
        if (toolMode === 'navigate') {
            setIsPanning(true);
            setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
        } else {
            setIsDrawing(true);
            const canvas = canvasRef.current;
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) * (canvas.width / rect.width);
            const y = (e.clientY - rect.top) * (canvas.height / rect.height);
            
            lastX.current = x;
            lastY.current = y;
            drawMaskPixel(x, y, true);
        }
    };

    const handleCanvasInteractionMove = (e) => {
        if (e.preventDefault) e.preventDefault();
        
        // Track visual brush cursor overlay position
        if (toolMode !== 'navigate' && viewportRef.current) {
            const vRect = viewportRef.current.getBoundingClientRect();
            setCursorPos({
                x: e.clientX - vRect.left,
                y: e.clientY - vRect.top
            });
            setShowCursor(true);
        }

        if (isPanning && toolMode === 'navigate') {
            setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
        } else if (isDrawing && toolMode !== 'navigate') {
            const canvas = canvasRef.current;
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) * (canvas.width / rect.width);
            const y = (e.clientY - rect.top) * (canvas.height / rect.height);
            
            drawMaskPixel(x, y, false);
            
            lastX.current = x;
            lastY.current = y;
        }
    };

    const handleCanvasInteractionEnd = () => {
        setIsPanning(false);
        setIsDrawing(false);
        lastX.current = null;
        lastY.current = null;
    };

    const drawMaskPixel = (x, y, isStart) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.lineWidth = brushSize;

        if (toolMode === 'draw') {
            ctx.globalCompositeOperation = 'source-over';
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.85)';
            ctx.beginPath();
            if (isStart || lastX.current === null) {
                ctx.moveTo(x, y);
                ctx.lineTo(x, y);
                ctx.stroke();
            } else {
                ctx.moveTo(lastX.current, lastY.current);
                ctx.lineTo(x, y);
                ctx.stroke();
            }
        } else if (toolMode === 'erase') {
            ctx.globalCompositeOperation = 'destination-out';
            ctx.strokeStyle = 'rgba(0, 0, 0, 1)';
            ctx.beginPath();
            if (isStart || lastX.current === null) {
                ctx.moveTo(x, y);
                ctx.lineTo(x, y);
                ctx.stroke();
            } else {
                ctx.moveTo(lastX.current, lastY.current);
                ctx.lineTo(x, y);
                ctx.stroke();
            }
        }
    };

    const clearMask = () => {
        if (!canvasRef.current) return;
        const canvas = canvasRef.current;
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
        setStatusLog('Manual mask cleared.');
    };

    // Before/After split comparison logic
    const handleSliderMove = useCallback((clientX) => {
        if (!sliderContainerRef.current) return;
        const rect = sliderContainerRef.current.getBoundingClientRect();
        const pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
        setSliderPos(pct);
    }, []);

    const confConfig = detectResult ? (CONFIDENCE_CONFIG[detectResult.confidence_level] ?? CONFIDENCE_CONFIG.NONE) : null;
    const ConfIcon = confConfig?.icon;
    const diag = activeModel?.diagnostics || {};

    return (
        <div className="flex flex-col lg:flex-row h-[calc(100vh-50px)] bg-zinc-950 text-zinc-200">
            {/* Sidebar Controls */}
            <aside className="w-full lg:w-[320px] bg-zinc-900 border-b lg:border-b-0 lg:border-r border-zinc-800 flex flex-col overflow-y-auto shrink-0 select-none">
                
                {/* Upload & Info Section */}
                <div className="p-4 border-b border-zinc-800 flex flex-col gap-3">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Source Document</span>
                    
                    {!imageFile ? (
                        <div
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className="rounded bg-zinc-950 border border-dashed border-zinc-850 hover:border-orange-500/40 p-5 flex flex-col items-center justify-center cursor-pointer transition-colors group"
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/jpeg,image/jpg,image/png,image/webp,image/bmp,image/tiff"
                                onChange={(e) => { if (e.target.files?.[0]) loadImage(e.target.files[0]); }}
                                className="hidden"
                            />
                            <Upload className="size-4 text-zinc-600 group-hover:text-orange-500 transition-colors mb-1.5" />
                            <span className="text-zinc-400 font-medium text-xs">Load Image</span>
                        </div>
                    ) : (
                        <div className="p-3 rounded bg-zinc-950 border border-zinc-850 text-[10px] font-mono flex flex-col gap-1 text-zinc-400">
                            <div className="flex justify-between">
                                <span className="text-zinc-600">FILE</span>
                                <span className="text-zinc-300 truncate max-w-[160px]">{metadata?.name}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-600">RESOLUTION</span>
                                <span className="text-zinc-300">{metadata?.width}×{metadata?.height}</span>
                            </div>
                            <button
                                onClick={() => { setImageFile(null); setPreviewUrl(null); setProcessedUrl(null); }}
                                className="mt-2 py-1 rounded bg-zinc-900 border border-zinc-800 text-[10px] text-red-400 hover:bg-red-500/10 hover:border-red-500/20 transition-colors"
                            >
                                Start Over
                            </button>
                        </div>
                    )}

                    {errorMsg && (
                        <div className="p-2 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-[10px] font-mono flex items-start gap-1.5">
                            <XCircle className="size-3.5 shrink-0 mt-0.5" />
                            <span>{errorMsg}</span>
                        </div>
                    )}
                </div>

                {/* Canvas Workspace Editing controls */}
                {imageFile && !processedUrl && (
                    <div className="p-4 border-b border-zinc-800 flex flex-col gap-4">
                        <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Canvas Workspace Tools</span>

                        {/* Tool Modes */}
                        <div className="grid grid-cols-3 gap-1 bg-zinc-950 p-1 rounded border border-zinc-850">
                            {[
                                { id: 'navigate', name: 'Pan', icon: Move },
                                { id: 'draw', name: 'Paint', icon: Edit2 },
                                { id: 'erase', name: 'Erase', icon: Eraser },
                            ].map((tool) => {
                                const ToolIcon = tool.icon;
                                return (
                                    <button
                                        key={tool.id}
                                        onClick={() => setToolMode(tool.id)}
                                        className={`py-1 rounded text-[10px] font-medium flex items-center justify-center gap-1 transition-all ${
                                            toolMode === tool.id
                                                ? 'bg-zinc-850 text-white border border-zinc-700/80'
                                                : 'text-zinc-500 hover:text-zinc-300'
                                        }`}
                                    >
                                        <ToolIcon className="size-3 text-orange-500" />
                                        <span>{tool.name}</span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* Brush Size */}
                        {toolMode !== 'navigate' && (
                            <div className="flex flex-col gap-1">
                                <div className="flex justify-between text-[11px]">
                                    <span className="text-zinc-400">Brush Diameter</span>
                                    <span className="font-mono text-orange-500 font-bold">{brushSize}px</span>
                                </div>
                                <input
                                    type="range"
                                    min="4"
                                    max="400"
                                    value={brushSize}
                                    onChange={(e) => setBrushSize(Number(e.target.value))}
                                    className="w-full accent-orange-600 bg-zinc-850 rounded h-1 cursor-pointer"
                                />
                            </div>
                        )}

                        {/* Navigation Zoom Controls */}
                        <div className="flex items-center justify-between border-t border-zinc-850 pt-3">
                            <span className="text-[10px] text-zinc-500 font-mono">Zoom: {Math.round(zoom * 100)}%</span>
                            <div className="flex gap-1">
                                <button onClick={() => handleZoom(0.25)} className="p-1 rounded bg-zinc-850 hover:bg-zinc-800 text-zinc-300 border border-zinc-800">
                                    <ZoomIn className="size-3.5" />
                                </button>
                                <button onClick={() => handleZoom(-0.25)} className="p-1 rounded bg-zinc-850 hover:bg-zinc-800 text-zinc-300 border border-zinc-800">
                                    <ZoomOut className="size-3.5" />
                                </button>
                                <button onClick={() => handleZoom(0)} className="p-1 rounded bg-zinc-850 hover:bg-zinc-800 text-zinc-300 border border-zinc-800">
                                    <Maximize2 className="size-3.5" />
                                </button>
                            </div>
                        </div>

                        {/* Clear Mask */}
                        <button
                            onClick={clearMask}
                            className="w-full py-1.5 rounded bg-zinc-850 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-[10px] font-semibold flex items-center justify-center gap-1 cursor-pointer"
                        >
                            <Trash2 className="size-3.5" />
                            <span>Clear Custom Mask</span>
                        </button>
                    </div>
                )}

                {/* Scan & Parameters settings */}
                {imageFile && !processedUrl && (
                    <div className="p-4 border-b border-zinc-800 flex flex-col gap-3">
                        <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Candidate Scanning</span>
                        <div className="flex flex-col gap-3">
                            {[
                                { label: 'Star Sensitivity', val: sensitivity, set: setSensitivity, min: 140, max: 230 },
                                { label: 'Border Padding', val: padding, set: setPadding, min: 4, max: 20, suffix: ' px' },
                            ].map(({ label, val, set, min, max, suffix = '' }) => (
                                <div key={label} className="flex flex-col gap-1">
                                    <div className="flex justify-between text-[11px]">
                                        <span className="text-zinc-400 font-medium">{label}</span>
                                        <span className="font-mono text-orange-500 font-bold">{val}{suffix}</span>
                                    </div>
                                    <input type="range" min={min} max={max} value={val}
                                        onChange={e => set(Number(e.target.value))}
                                        className="w-full accent-orange-600 bg-zinc-850 rounded h-1 cursor-pointer" />
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={runDetect}
                            disabled={isDetecting || isProcessing}
                            className="w-full mt-2 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-750 text-[10px] font-semibold flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-40"
                        >
                            {isDetecting ? <RefreshCw className="size-3 animate-spin text-orange-500" /> : <Eye className="size-3 text-orange-500" />}
                            <span>Scan Candidate Areas</span>
                        </button>
                    </div>
                )}

                {/* Diagnostic metrics accordion */}
                {imageFile && activeModel?.is_loaded && (
                    <div className="px-4 py-2 border-b border-zinc-800 flex flex-col gap-1">
                        <button
                            onClick={() => setShowDiagnostics(!showDiagnostics)}
                            className="w-full py-1.5 flex items-center justify-between text-[10px] font-mono text-zinc-400 hover:text-zinc-200 transition-colors"
                        >
                            <span>DIAGNOSTICS & METRICS</span>
                            {showDiagnostics ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                        </button>
                        {showDiagnostics && (
                            <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-850 text-[9px] font-mono flex flex-col gap-1 text-zinc-400 mb-2">
                                <div className="flex justify-between">
                                    <span className="text-zinc-650">LOAD TIME</span>
                                    <span className="text-orange-400 font-semibold">{diag.load_time_sec}s</span>
                                </div>
                                {diag.inference_time_sec && (
                                    <div className="flex justify-between">
                                        <span className="text-zinc-650">INFERENCE TIME</span>
                                        <span className="text-orange-400 font-semibold">{diag.inference_time_sec}s</span>
                                    </div>
                                )}
                                <div className="flex justify-between">
                                    <span className="text-zinc-650">RAM FOOTPRINT</span>
                                    <span className="text-emerald-400 font-semibold">+{diag.ram_usage_mb} MB</span>
                                </div>
                                {diag.vram_usage_mb && (
                                    <div className="flex justify-between">
                                        <span className="text-zinc-650">VRAM FOOTPRINT</span>
                                        <span className="text-emerald-400 font-semibold">+{diag.vram_usage_mb} MB</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Execution Section */}
                {imageFile && (
                    <div className="p-4 mt-auto flex flex-col gap-3">
                        {detectResult && confConfig && (
                            <div className={`p-2.5 rounded border ${confConfig.color} flex items-start gap-2`}>
                                <ConfIcon className="size-3.5 shrink-0 mt-0.5" />
                                <span className="text-[10px] font-medium leading-normal">{confConfig.label}</span>
                            </div>
                        )}

                        {!processedUrl ? (
                            !isModelInstalled ? (
                                <div className="flex flex-col gap-2">
                                    <div className="p-2.5 rounded border border-amber-500/20 bg-amber-500/5 text-amber-400 flex items-start gap-2">
                                        <AlertTriangle className="size-4 shrink-0 mt-0.5 text-orange-500" />
                                        <div className="flex flex-col gap-0.5">
                                            <span className="text-[10px] font-semibold leading-none">Model Not Installed</span>
                                            <p className="text-[9px] leading-normal text-zinc-400">The model weights for LaMa ({activeModel?.expected_size_mb || 350} MB) must be installed locally before processing.</p>
                                        </div>
                                    </div>
                                    {activeModel?.status === 'downloading' ? (
                                        <div className="p-2.5 rounded bg-zinc-950/40 border border-zinc-850 flex flex-col gap-1 text-[10px] font-mono">
                                            <div className="flex justify-between text-zinc-400">
                                                <span>Downloading weights...</span>
                                                <span className="text-orange-500 font-bold">{activeModel.download_progress}%</span>
                                            </div>
                                            <div className="w-full bg-zinc-900 rounded-full h-1.5 overflow-hidden">
                                                <div className="bg-orange-500 h-1.5 rounded-full transition-all duration-300" style={{ width: `${activeModel.download_progress}%` }} />
                                            </div>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => handleDownload(activeModelId)}
                                            className="w-full py-2 rounded bg-orange-650 hover:bg-orange-600 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
                                        >
                                            <Download className="size-3.5" />
                                            <span>Install Model Weights</span>
                                        </button>
                                    )}
                                </div>
                            ) : (
                                <button
                                    onClick={runInpaint}
                                    disabled={isProcessing}
                                    className="w-full py-2 rounded bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white font-semibold text-xs flex items-center justify-center gap-2 cursor-pointer"
                                >
                                    {isProcessing ? <RefreshCw className="size-3.5 animate-spin" /> : <Sparkles className="size-3.5" />}
                                    <span>{isProcessing ? 'Removing Watermark...' : 'Run Neural Inpainting'}</span>
                                </button>
                            )
                        ) : (
                            <button
                                onClick={() => { setProcessedUrl(null); setDetectResult(null); }}
                                className="w-full py-2 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/80 text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer"
                            >
                                <span>Reset / Edit Again</span>
                            </button>
                        )}

                        {statusLog && (
                            <p className="text-[9px] font-mono text-zinc-400 bg-zinc-950 p-2 rounded border border-zinc-800">
                                {statusLog}
                            </p>
                        )}
                    </div>
                )}
            </aside>

            {/* Viewport Canvas Space */}
            <main className="flex-1 flex flex-col p-4 overflow-hidden relative">
                
                {/* Workspace headers */}
                <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80 mb-4 shrink-0">
                    <div className="flex items-center gap-2 font-mono text-[10px]">
                        <span className="text-zinc-500 uppercase">Status:</span>
                        <span className="text-zinc-300 font-semibold">
                            {!imageFile ? 'NO IMAGE' : isProcessing ? 'PROCESSING...' : processedUrl ? 'COMPLETED' : isDetecting ? 'SCANNING...' : 'MASK READY'}
                        </span>
                    </div>

                    {processedUrl && (
                        <div className="flex items-center gap-2">
                            <div className="flex items-center rounded border border-zinc-700/80 bg-zinc-900 overflow-hidden">
                                <button
                                    onClick={() => setComparisonMode('slider')}
                                    className={`px-2 py-1 text-[10px] font-mono uppercase transition-colors ${comparisonMode === 'slider' ? 'bg-orange-600 text-white font-bold' : 'text-zinc-400 hover:text-zinc-200'}`}
                                >
                                    Slider
                                </button>
                                <button
                                    onClick={() => setComparisonMode('split')}
                                    className={`px-2 py-1 text-[10px] font-mono uppercase transition-colors ${comparisonMode === 'split' ? 'bg-orange-600 text-white font-bold' : 'text-zinc-400 hover:text-zinc-200'}`}
                                >
                                    Split
                                </button>
                            </div>
                            
                            <div className="flex items-center bg-emerald-600/10 border border-emerald-500/20 rounded ml-2">
                                <select 
                                    value={downloadFormat}
                                    onChange={e => setDownloadFormat(e.target.value)}
                                    className="bg-transparent text-emerald-400 text-[10px] font-mono font-semibold outline-none border-r border-emerald-500/20 px-2 py-1 cursor-pointer hover:bg-emerald-600/20"
                                >
                                    <option value="png">PNG</option>
                                    <option value="jpg">JPG</option>
                                    <option value="webp">WEBP</option>
                                </select>
                                <button
                                    onClick={() => {
                                        const a = document.createElement('a');
                                        a.href = processedUrl; // Note: processedUrl is the default format returned by backend. For simplicity, we just trigger download. Real format conversion requires drawing to canvas.
                                        a.download = `cleaned_${imageFile?.name ? imageFile.name.split('.')[0] : 'image'}.${downloadFormat}`;
                                        a.click();
                                    }}
                                    className="flex items-center gap-1 px-2.5 py-1 text-emerald-400 hover:bg-emerald-600/20 text-[10px] font-semibold transition-all"
                                >
                                    <Download className="size-3" />
                                    <span>Export</span>
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Main viewport area */}
                <div 
                    ref={viewportRef}
                    className="flex-1 relative rounded bg-zinc-900 border border-zinc-800 overflow-hidden flex items-center justify-center"
                >
                    {!previewUrl ? (
                        <div className="flex flex-col items-center gap-2 text-zinc-500 p-8 text-center max-w-sm font-sans">
                            <ImageIcon className="size-8 text-zinc-600 mb-1 stroke-[1.5]" />
                            <p className="text-xs font-medium text-zinc-400">Canvas Viewport</p>
                            <p className="text-[11px] text-zinc-600">Please select an image file in the left sidebar to initialize the precision canvas editor.</p>
                        </div>
                    ) : (
                        /* Mask Editing Viewport with zoom/pan */
                        <div
                            ref={viewportRef}
                            onMouseDown={handleCanvasInteractionStart}
                            onMouseMove={handleCanvasInteractionMove}
                            onMouseUp={handleCanvasInteractionEnd}
                            onMouseLeave={() => { handleCanvasInteractionEnd(); setShowCursor(false); }}
                            onMouseEnter={() => { if (toolMode !== 'navigate') setShowCursor(true); }}
                            onTouchStart={(e) => {
                                const touch = e.touches[0];
                                handleCanvasInteractionStart({
                                    clientX: touch.clientX,
                                    clientY: touch.clientY,
                                    preventDefault: () => e.preventDefault()
                                });
                            }}
                            onTouchMove={(e) => {
                                const touch = e.touches[0];
                                handleCanvasInteractionMove({
                                    clientX: touch.clientX,
                                    clientY: touch.clientY,
                                    preventDefault: () => e.preventDefault()
                                });
                            }}
                            onTouchEnd={handleCanvasInteractionEnd}
                            className={`w-full h-full relative overflow-hidden flex items-center justify-center ${
                                toolMode === 'navigate' || processedUrl ? 'cursor-grab active:cursor-grabbing' : 'cursor-none'
                            }`}
                        >
                            <div
                                style={{
                                    aspectRatio: metadata ? `${metadata.width} / ${metadata.height}` : 'auto',
                                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                                    transition: isPanning ? 'none' : 'transform 0.15s ease-out'
                                }}
                                className={`relative max-w-full max-h-[80vh] select-none shrink-0 ${comparisonMode === 'split' && processedUrl ? 'flex gap-2' : ''}`}
                            >
                                {comparisonMode === 'split' && processedUrl ? (
                                    <>
                                        <div className="flex-1 relative h-full">
                                            <img src={previewUrl} alt="Original" className="w-full h-full object-contain pointer-events-none" />
                                            <span className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/60 text-white text-[9px] font-mono">BEFORE</span>
                                        </div>
                                        <div className="flex-1 relative h-full">
                                            <img src={processedUrl} alt="Processed" className="w-full h-full object-contain pointer-events-none" />
                                            <span className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-emerald-600/80 text-white text-[9px] font-mono">AFTER</span>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <img
                                            ref={imageRef}
                                            src={processedUrl || previewUrl}
                                            alt="Viewport source"
                                            className="w-full h-full object-cover pointer-events-none"
                                        />
                                        
                                        {!processedUrl && (
                                            <canvas
                                                ref={canvasRef}
                                                className="absolute inset-0 w-full h-full pointer-events-auto"
                                                style={{ imageRendering: 'pixelated' }}
                                            />
                                        )}

                                        {processedUrl && comparisonMode === 'slider' && (
                                            <div
                                                ref={sliderContainerRef}
                                                onMouseDown={(e) => { e.stopPropagation(); setIsDraggingSlider(true); }}
                                                onMouseUp={(e) => { e.stopPropagation(); setIsDraggingSlider(false); }}
                                                onMouseLeave={() => setIsDraggingSlider(false)}
                                                onMouseMove={(e) => { e.stopPropagation(); if (isDraggingSlider) handleSliderMove(e.clientX); }}
                                                className="absolute inset-0 w-full h-full cursor-ew-resize pointer-events-auto"
                                            >
                                                <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ width: `${sliderPos}%` }}>
                                                    <img src={previewUrl} className="absolute inset-0 h-full max-w-none object-cover pointer-events-none" style={{ width: sliderContainerRef.current?.clientWidth || '100%' }} />
                                                    <span className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/60 text-white text-[9px] font-mono">BEFORE</span>
                                                </div>
                                                <div className="absolute top-0 bottom-0 w-0.5 bg-white cursor-ew-resize shadow-[0_0_4px_rgba(0,0,0,0.5)]" style={{ left: `calc(${sliderPos}% - 1px)` }}>
                                                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-8 bg-white rounded-sm shadow border border-zinc-300 flex items-center justify-center">
                                                        <div className="flex gap-0.5">
                                                            <div className="w-0.5 h-3 bg-zinc-400 rounded-full" />
                                                            <div className="w-0.5 h-3 bg-zinc-400 rounded-full" />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>

                            {/* Cursor Brush Size Preview Circle */}
                            {showCursor && toolMode !== 'navigate' && !processedUrl && canvasRef.current && (
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: cursorPos.x,
                                        top: cursorPos.y,
                                        width: brushSize * (canvasRef.current.getBoundingClientRect().width / canvasRef.current.width),
                                        height: brushSize * (canvasRef.current.getBoundingClientRect().width / canvasRef.current.width),
                                        transform: 'translate(-50%, -50%)',
                                        border: toolMode === 'erase' ? '1px dashed rgba(255, 255, 255, 0.9)' : '1px solid rgba(255, 255, 255, 0.8)',
                                        boxShadow: '0 0 0 1px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(0, 0, 0, 0.5)',
                                        borderRadius: '50%',
                                        pointerEvents: 'none',
                                        zIndex: 50,
                                        backgroundColor: toolMode === 'erase' ? 'rgba(0, 0, 0, 0.3)' : 'rgba(239, 68, 68, 0.2)'
                                    }}
                                />
                            )}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
