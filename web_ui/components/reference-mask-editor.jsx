import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Check, Edit2, Eraser } from 'lucide-react';

export default function ReferenceMaskEditor({ imageFile, onSave, onCancel }) {
    const [imageUrl, setImageUrl] = useState(null);
    const imageRef = useRef(null);
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    
    const [toolMode, setToolMode] = useState('draw'); // 'draw', 'erase'
    const [brushSize, setBrushSize] = useState(30);
    const [isDrawing, setIsDrawing] = useState(false);
    
    // Zoom/Pan state
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const [lastPan, setLastPan] = useState({ x: 0, y: 0 });

    useEffect(() => {
        if (imageFile) {
            const url = URL.createObjectURL(imageFile);
            setImageUrl(url);
            return () => URL.revokeObjectURL(url);
        }
    }, [imageFile]);

    const resizeCanvas = useCallback(() => {
        if (!imageRef.current || !canvasRef.current) return;
        const img = imageRef.current;
        const canvas = canvasRef.current;
        if (img.clientWidth && img.clientHeight) {
            canvas.width = img.clientWidth;
            canvas.height = img.clientHeight;
        }
    }, []);

    useEffect(() => {
        window.addEventListener('resize', resizeCanvas);
        return () => window.removeEventListener('resize', resizeCanvas);
    }, [resizeCanvas]);

    const getCoordinates = (e) => {
        if (!canvasRef.current) return null;
        const rect = canvasRef.current.getBoundingClientRect();
        
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;

        const x = (clientX - rect.left) / zoom;
        const y = (clientY - rect.top) / zoom;

        return { x, y };
    };

    const drawMaskPixel = (ctx, x, y, size, mode) => {
        ctx.beginPath();
        if (mode === 'erase') {
            ctx.globalCompositeOperation = 'destination-out';
            ctx.fillStyle = 'rgba(0,0,0,1)';
        } else {
            ctx.globalCompositeOperation = 'source-over';
            ctx.fillStyle = 'rgba(239, 68, 68, 0.6)';
        }
        ctx.arc(x, y, size / 2, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.beginPath();
        ctx.lineWidth = size;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        if (mode === 'erase') {
            ctx.strokeStyle = 'rgba(0,0,0,1)';
        } else {
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.6)';
        }
        ctx.moveTo(x, y);
        ctx.lineTo(x, y);
        ctx.stroke();
    };

    const handlePointerDown = (e) => {
        if (e.button === 1 || (e.button === 0 && e.altKey)) {
            setIsPanning(true);
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            setLastPan({ x: clientX - pan.x, y: clientY - pan.y });
            return;
        }

        const coords = getCoordinates(e);
        if (!coords || !canvasRef.current) return;
        
        setIsDrawing(true);
        const ctx = canvasRef.current.getContext('2d');
        
        canvasRef.current._lastX = coords.x;
        canvasRef.current._lastY = coords.y;

        drawMaskPixel(ctx, coords.x, coords.y, brushSize / zoom, toolMode);
    };

    const handlePointerMove = (e) => {
        if (isPanning) {
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            setPan({
                x: clientX - lastPan.x,
                y: clientY - lastPan.y
            });
            return;
        }

        if (!isDrawing) return;
        
        const coords = getCoordinates(e);
        if (!coords || !canvasRef.current) return;

        const ctx = canvasRef.current.getContext('2d');
        const lastX = canvasRef.current._lastX;
        const lastY = canvasRef.current._lastY;

        ctx.beginPath();
        ctx.lineWidth = brushSize / zoom;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        if (toolMode === 'erase') {
            ctx.globalCompositeOperation = 'destination-out';
            ctx.strokeStyle = 'rgba(0,0,0,1)';
        } else {
            ctx.globalCompositeOperation = 'source-over';
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.6)';
        }

        ctx.moveTo(lastX, lastY);
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();

        canvasRef.current._lastX = coords.x;
        canvasRef.current._lastY = coords.y;
    };

    const handlePointerUp = () => {
        setIsDrawing(false);
        setIsPanning(false);
    };

    const handleWheel = (e) => {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            const zoomDelta = e.deltaY > 0 ? 0.9 : 1.1;
            setZoom(prev => Math.min(Math.max(0.1, prev * zoomDelta), 5));
        }
    };

    const handleSave = () => {
        if (!canvasRef.current || !imageRef.current) return;
        
        const sourceCanvas = canvasRef.current;
        const img = imageRef.current;
        
        const exportCanvas = document.createElement('canvas');
        exportCanvas.width = img.naturalWidth;
        exportCanvas.height = img.naturalHeight;
        
        const ctx = exportCanvas.getContext('2d');
        
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
        
        // Scale drawing
        const scaleX = img.naturalWidth / img.clientWidth;
        const scaleY = img.naturalHeight / img.clientHeight;
        ctx.scale(scaleX, scaleY);
        ctx.drawImage(sourceCanvas, 0, 0);
        
        // Reset scale for image data operations
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        
        const imageData = ctx.getImageData(0, 0, exportCanvas.width, exportCanvas.height);
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            if (data[i] > 0) {
                data[i] = 255;
                data[i+1] = 255;
                data[i+2] = 255;
            } else {
                data[i] = 0;
                data[i+1] = 0;
                data[i+2] = 0;
            }
            data[i+3] = 255;
        }
        ctx.putImageData(imageData, 0, 0);
        
        exportCanvas.toBlob((blob) => {
            const file = new File([blob], 'reference_mask.png', { type: 'image/png' });
            onSave(file);
        }, 'image/png');
    };

    if (!imageFile) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-black/90 flex flex-col font-sans">
            <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950">
                <div className="flex items-center gap-4 text-zinc-200">
                    <span className="font-mono text-sm uppercase tracking-wider">Create Reference Mask</span>
                    <div className="flex items-center gap-2 bg-zinc-900 rounded p-1">
                        <button 
                            onClick={() => setToolMode('draw')} 
                            className={`p-2 rounded ${toolMode === 'draw' ? 'bg-orange-600 text-white' : 'hover:bg-zinc-800 text-zinc-400'}`}
                            title="Draw Mask"
                        >
                            <Edit2 className="size-4" />
                        </button>
                        <button 
                            onClick={() => setToolMode('erase')} 
                            className={`p-2 rounded ${toolMode === 'erase' ? 'bg-orange-600 text-white' : 'hover:bg-zinc-800 text-zinc-400'}`}
                            title="Erase Mask"
                        >
                            <Eraser className="size-4" />
                        </button>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-zinc-500">BRUSH</span>
                        <input 
                            type="range" min="1" max="100" 
                            value={brushSize} onChange={(e) => setBrushSize(Number(e.target.value))}
                            className="w-24 accent-orange-500" 
                        />
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onCancel} className="px-4 py-2 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 text-sm font-semibold transition-colors cursor-pointer">
                        Cancel
                    </button>
                    <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-colors cursor-pointer">
                        <Check className="size-4" />
                        <span>Confirm Mask</span>
                    </button>
                </div>
            </div>
            
            <div 
                ref={containerRef}
                className="flex-1 relative overflow-hidden flex items-center justify-center select-none"
                onWheel={handleWheel}
            >
                <div 
                    style={{
                        transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                        transformOrigin: 'center',
                    }}
                    className="relative"
                >
                    <img 
                        ref={imageRef}
                        src={imageUrl} 
                        alt="Reference" 
                        className="max-w-[80vw] max-h-[80vh] object-contain pointer-events-none"
                        onLoad={resizeCanvas}
                    />
                    <canvas
                        ref={canvasRef}
                        onPointerDown={handlePointerDown}
                        onPointerMove={handlePointerMove}
                        onPointerUp={handlePointerUp}
                        onPointerLeave={handlePointerUp}
                        className={`absolute inset-0 w-full h-full ${isPanning ? 'cursor-grab active:cursor-grabbing' : 'cursor-crosshair'}`}
                        style={{ touchAction: 'none' }}
                    />
                </div>
                <div className="absolute bottom-4 left-4 bg-zinc-900/80 p-2 rounded text-[10px] font-mono text-zinc-400 pointer-events-none border border-zinc-800">
                    Tip: Scroll with Ctrl/Cmd to Zoom. Middle-click or Alt+Drag to Pan.
                </div>
            </div>
        </div>
    );
}
