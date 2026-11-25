'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import {
    Layers, Upload, CheckCircle2, RefreshCw,
    AlertTriangle, Eye, XCircle, MinusCircle, SkipForward, Trash2, StopCircle, Download, CheckSquare, Square
} from 'lucide-react';
import ReferenceMaskEditor from './reference-mask-editor';
import BatchPreviewModal from './batch-preview-modal';

const STATUS_CONFIG = {
    queued:       { label: 'Queued',        color: 'text-zinc-500',     border: 'border-zinc-800',     bg: 'bg-zinc-950/40',       icon: MinusCircle },
    detecting:    { label: 'Detecting...',  color: 'text-orange-400',   border: 'border-orange-500/20', bg: 'bg-orange-500/5',       icon: Eye },
    needs_review: { label: 'Needs Review',  color: 'text-amber-400',   border: 'border-amber-500/20', bg: 'bg-amber-500/5',       icon: AlertTriangle },
    processing:   { label: 'Processing...', color: 'text-pink-400',    border: 'border-pink-500/20',  bg: 'bg-pink-500/5',        icon: RefreshCw },
    completed:    { label: 'Completed',     color: 'text-emerald-400', border: 'border-emerald-500/20 bg-emerald-500/5', icon: CheckCircle2 },
    skipped:      { label: 'Skipped',       color: 'text-zinc-500',     border: 'border-zinc-800',     bg: 'bg-zinc-950/40',       icon: SkipForward },
    failed:       { label: 'Failed',        color: 'text-red-400',      border: 'border-red-500/20',   bg: 'bg-red-500/5',         icon: XCircle },
};

const mapBackendStatus = (status) => {
    if (!status) return 'queued';
    const s = status.toLowerCase();
    if (s === 'removed' || s === 'completed' || s === 'no_watermark') return 'completed';
    if (s === 'review_required') return 'needs_review';
    if (s === 'validating' || s === 'saving' || s === 'processing' || s === 'detecting') return 'processing';
    if (s === 'failed' || s === 'removal_failed' || s === 'error') return 'failed';
    if (s === 'skipped') return 'skipped';
    return s;
};

export default function BatchProcessor() {
    const [fileQueue, setFileQueue] = useState([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sensitivity, setSensitivity] = useState(160);
    const [padding, setPadding] = useState(12);
    const [skipLowConf, setSkipLowConf] = useState(true);
    const [outputFormat, setOutputFormat] = useState('source');
    const [batchLog, setBatchLog] = useState('');
    const [stats, setStats] = useState({ completed: 0, skipped: 0, failed: 0 });
    const [activeBatchId, setActiveBatchId] = useState(null);
    const [batchRecord, setBatchRecord] = useState(null); // Persisted final batch summary

    // Reference Settings
    const [referenceImage, setReferenceImage] = useState(null);
    const [referenceMask, setReferenceMask] = useState(null);
    const [showRefMasker, setShowRefMasker] = useState(false);

    // Selection & Preview State
    const [selectedItems, setSelectedItems] = useState(new Set());
    const [previewItems, setPreviewItems] = useState(null);
    const [previewInitialIndex, setPreviewInitialIndex] = useState(0);

    // selection helpers
    const toggleSelection = (name) => {
        const next = new Set(selectedItems);
        if (next.has(name)) next.delete(name);
        else next.add(name);
        setSelectedItems(next);
    };

    const selectAll = () => setSelectedItems(new Set(fileQueue.map(i => i.name)));
    const clearSelection = () => setSelectedItems(new Set());


    const fileInputRef = useRef(null);
    const ALLOWED_EXTS = new Set(['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif']);

    const addFilesToQueue = useCallback((files) => {
        const validFiles = files.filter(f => {
            const ext = '.' + f.name.split('.').pop().toLowerCase();
            return ALLOWED_EXTS.has(ext) || f.type.startsWith('image/');
        });

        const newItems = validFiles.map((file, idx) => ({
            id: `${Date.now()}-${idx}`,
            file,
            name: file.name,
            size: (file.size / 1024).toFixed(1) + ' KB',
            status: 'queued',
            confidence: null,
            confidence_level: null,
            message: '',
        }));

        const rejected = files.length - validFiles.length;
        if (rejected > 0) {
            setBatchLog(prev => `${prev}\n⚠️ Unsupported file type: ${rejected} file(s) rejected.`);
        }
        setFileQueue(prev => [...prev, ...newItems]);
    }, []);

    const updateItemByName = (name, patch) => {
        setFileQueue(prev => prev.map(it => it.name === name ? { ...it, ...patch } : it));
    };

    const removeFile = (id) => {
        setFileQueue(prev => {
            const item = prev.find(it => it.id === id);
            if (item) {
                const nextSel = new Set(selectedItems);
                nextSel.delete(item.name);
                setSelectedItems(nextSel);
            }
            return prev.filter(it => it.id !== id);
        });
    };
    const clearQueue = () => { 
        setFileQueue([]); 
        setBatchLog(''); 
        setStats({ completed: 0, skipped: 0, failed: 0 }); 
        setActiveBatchId(null); 
        setBatchRecord(null); 
        setSelectedItems(new Set());
    };

    // Smart Batch Execution using backend asynchronous BatchManager
    const processBatch = async () => {
        if (fileQueue.length === 0) return;
        setIsProcessing(true);
        setStats({ completed: 0, skipped: 0, failed: 0 });
        setBatchRecord(null);
        setBatchLog(`▶ Initiating smart batch session for ${fileQueue.length} files...\n`);

        try {
            const form = new FormData();
            fileQueue.forEach(item => {
                form.append('files', item.file);
            });
            form.append('sensitivity', sensitivity);
            form.append('padding', padding);
            form.append('skip_low_confidence', skipLowConf);
            form.append('output_format', outputFormat);
            
            if (referenceImage) form.append('reference_image', referenceImage);
            if (referenceMask) form.append('reference_mask', referenceMask);

            const res = await fetch('/api/inpaint/batch', { method: 'POST', body: form });
            const data = await res.json();

            if (!res.ok || !data.success) {
                throw new Error(data.error || `Server returned error: ${res.status}`);
            }

            setActiveBatchId(data.batch_id);
            setBatchLog(prev => `${prev}✓ Batch job queued successfully (ID: ${data.batch_id.slice(0,8)}). Running diagnostics...\n`);
        } catch (err) {
            setBatchLog(prev => `${prev}✗ Failed to start batch: ${err.message}\n`);
            setIsProcessing(false);
        }
    };

    // Cancel batch job
    const handleCancelBatch = async () => {
        if (!activeBatchId) return;
        try {
            setBatchLog(prev => `${prev}\n⚠️ Requesting cancellation...\n`);
            const res = await fetch(`/api/batch/${activeBatchId}/cancel`, { method: 'POST' });
            if (res.ok) {
                setBatchLog(prev => `${prev}✓ Cancellation command sent to backend queue.\n`);
            } else {
                setBatchLog(prev => `${prev}✗ Failed to send cancel command.\n`);
            }
        } catch (err) {
            setBatchLog(prev => `${prev}✗ Error cancelling batch: ${err.message}\n`);
        }
    };

    // Retry failed items only
    const retryFailed = async () => {
        const failedItems = fileQueue.filter(item => item.status === 'failed');
        if (failedItems.length === 0) return;

        setIsProcessing(true);
        setStats(prev => ({ ...prev, failed: 0 }));
        setBatchRecord(null);
        setBatchLog(prev => `${prev}\n▶ Retrying ${failedItems.length} failed items...\n`);

        try {
            const form = new FormData();
            failedItems.forEach(item => {
                form.append('files', item.file);
            });
            form.append('sensitivity', sensitivity);
            form.append('padding', padding);
            form.append('skip_low_confidence', skipLowConf);
            form.append('output_format', outputFormat);
            
            if (referenceImage) form.append('reference_image', referenceImage);
            if (referenceMask) form.append('reference_mask', referenceMask);

            const res = await fetch('/api/inpaint/batch', { method: 'POST', body: form });
            const data = await res.json();

            if (!res.ok || !data.success) {
                throw new Error(data.error || `Server returned error: ${res.status}`);
            }

            // Set failed items back to queued state for UI visual progress
            failedItems.forEach(item => {
                updateItemByName(item.name, { status: 'queued', message: '' });
            });

            setActiveBatchId(data.batch_id);
            setBatchLog(prev => `${prev}✓ Retry batch job queued successfully (ID: ${data.batch_id.slice(0,8)}).\n`);
        } catch (err) {
            setBatchLog(prev => `${prev}✗ Failed to start retry batch: ${err.message}\n`);
            setIsProcessing(false);
        }
    };

    // Polling active batch progress
    useEffect(() => {
        if (!activeBatchId) return;

        let isPolling = true;
        const poll = async () => {
            try {
                const res = await fetch(`/api/batch/${activeBatchId}`);
                if (!res.ok) return;

                const data = await res.json();
                if (!isPolling) return;

                // Sync each item's status matching filename
                (data.items || []).forEach(item => {
                    const frontendStatus = mapBackendStatus(item.status);
                    updateItemByName(item.filename, {
                        status: frontendStatus,
                        confidence: item.confidence,
                        confidence_level: item.confidence_level,
                        message: item.error || (frontendStatus === 'completed' ? 'Done.' : '')
                    });
                });

                // Update counts
                setStats({
                    completed: data.completed,
                    skipped: data.skipped,
                    failed: data.failed
                });

                if (data.status === 'COMPLETED' || data.status === 'CANCELLED') {
                    const statusLabel = data.status === 'CANCELLED' ? 'CANCELLED' : 'COMPLETED';
                    const summaryMsg = `\n✅ Batch ${statusLabel.toLowerCase()} — ${data.completed} processed, ${data.skipped} skipped, ${data.failed} failed.\nDevice: ${data.device.toUpperCase()}\nAverage: ${data.avg_time_per_image}s / image\nTotal Duration: ${data.total_time_sec}s\n`;
                    setBatchLog(prev => `${prev}${summaryMsg}`);
                    
                    // Persist final stats summary in component state
                    setBatchRecord({
                        batch_id: activeBatchId,
                        status: statusLabel,
                        device: data.device.toUpperCase(),
                        avg_time_per_image: data.avg_time_per_image,
                        total_time_sec: data.total_time_sec,
                        output_dir: data.output_directory || './processed_images'
                    });

                    setActiveBatchId(null);
                    setIsProcessing(false);
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        };

        const interval = setInterval(poll, 1000);
        return () => {
            isPolling = false;
            clearInterval(interval);
        };
    }, [activeBatchId]);

    const reviewCount    = fileQueue.filter(i => i.status === 'needs_review').length;
    const failedCount    = fileQueue.filter(i => i.status === 'failed').length;

    const handleDownloadSelectedZip = async () => {
        if (!batchRecord?.batch_id || selectedItems.size === 0) return;
        const res = await fetch(`/api/batch/${batchRecord.batch_id}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filenames: Array.from(selectedItems) })
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `batch_selection_${batchRecord.batch_id}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        }
    };

    const handleDownloadSelected = async () => {
        if (!batchRecord?.batch_id || selectedItems.size === 0) return;
        const items = fileQueue.filter(i => selectedItems.has(i.name) && i.status === 'completed');
        for (const item of items) {
            const url = `/api/batch/${batchRecord.batch_id}/download/${item.name}`;
            const a = document.createElement('a');
            a.href = url;
            a.download = ''; // Let backend Content-Disposition define the true filename and extension
            document.body.appendChild(a);
            a.click();
            a.remove();
            await new Promise(r => setTimeout(r, 200));
        }
    };

    const handleDownloadAll = async () => {
        if (!batchRecord?.batch_id) return;
        const items = fileQueue.filter(i => i.status === 'completed');
        for (const item of items) {
            const url = `/api/batch/${batchRecord.batch_id}/download/${item.name}`;
            const a = document.createElement('a');
            a.href = url;
            a.download = ''; // Let backend specify correct extension
            document.body.appendChild(a);
            a.click();
            a.remove();
            await new Promise(r => setTimeout(r, 200));
        }
    };

    const handlePreviewSelected = () => {
        if (!batchRecord?.batch_id || selectedItems.size === 0) return;
        const itemsToPreview = fileQueue.filter(i => selectedItems.has(i.name) && i.status === 'completed');
        if (itemsToPreview.length > 0) {
            setPreviewItems(itemsToPreview);
            setPreviewInitialIndex(0);
        }
    };

    const handlePreviewSingle = (itemName) => {
        if (!batchRecord?.batch_id) return;
        const completedItems = fileQueue.filter(i => i.status === 'completed');
        const idx = completedItems.findIndex(i => i.name === itemName);
        if (idx >= 0) {
            setPreviewItems(completedItems);
            setPreviewInitialIndex(idx);
        }
    };

    return (
        <div className="flex flex-col lg:flex-row h-[calc(100vh-50px)] bg-zinc-950 text-zinc-200">
            {/* Left Column: Sidebar Controls */}
            <aside className="w-full lg:w-[320px] bg-zinc-900 border-b lg:border-b-0 lg:border-r border-zinc-800 p-5 flex flex-col gap-5 overflow-y-auto shrink-0 select-none">
                
                {/* Header title */}
                <div className="flex items-center gap-2">
                    <Layers className="size-4 text-orange-500" />
                    <span className="font-display font-semibold text-sm text-zinc-100">Batch Processing</span>
                </div>

                {/* Dropzone */}
                <div
                    onDragOver={e => e.preventDefault()}
                    onDrop={e => { e.preventDefault(); addFilesToQueue(Array.from(e.dataTransfer.files || [])); }}
                    onClick={() => fileInputRef.current?.click()}
                    className="rounded-lg bg-zinc-950 border border-dashed border-zinc-800 hover:border-orange-500/50 p-6 flex flex-col items-center justify-center cursor-pointer transition-colors group"
                >
                    <input ref={fileInputRef} type="file" multiple
                        accept="image/jpeg,image/jpg,image/png,image/webp,image/bmp,image/tiff"
                        onChange={e => addFilesToQueue(Array.from(e.target.files || []))}
                        className="hidden" />
                    <Upload className="size-5 text-zinc-500 group-hover:text-orange-500 transition-colors mb-2" />
                    <p className="text-zinc-300 font-medium text-xs">Load Images</p>
                    <p className="text-zinc-500 text-[10px] mt-0.5">Drag files or click to add</p>
                </div>

                {/* Settings parameters */}
                <div className="flex flex-col gap-4">
                    {[
                        { label: 'Scan Sensitivity', val: sensitivity, set: setSensitivity, min: 140, max: 230 },
                        { label: 'Edge Padding Bounds', val: padding, set: setPadding, min: 4, max: 20, suffix: ' px' },
                    ].map(({ label, val, set, min, max, suffix = '' }) => (
                        <div key={label} className="flex flex-col gap-1">
                            <div className="flex justify-between text-xs">
                                <span className="text-zinc-400 font-medium">{label}</span>
                                <span className="font-mono text-orange-500 font-bold">{val}{suffix}</span>
                            </div>
                            <input type="range" min={min} max={max} value={val}
                                onChange={e => set(Number(e.target.value))}
                                className="w-full accent-orange-600 bg-zinc-800 rounded h-1 cursor-pointer" />
                        </div>
                    ))}

                    <label className="flex items-center gap-2.5 cursor-pointer select-none">
                        <input
                            type="checkbox"
                            checked={skipLowConf}
                            onChange={() => setSkipLowConf(v => !v)}
                            className="rounded bg-zinc-950 border-zinc-800 text-orange-600 focus:ring-0 focus:ring-offset-0 size-3.5"
                        />
                        <span className="text-xs text-zinc-400">Skip LOW confidence scans</span>
                    </label>

                    {/* Reference Mode Block */}
                    <div className="pt-3 border-t border-zinc-800/80 flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                            <span className="text-zinc-500 font-medium text-[10px] tracking-wider uppercase">Reference Mode</span>
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] text-zinc-400">Reference Image</label>
                            <input type="file" accept="image/*" onChange={e => setReferenceImage(e.target.files[0])} className="text-[10px] text-zinc-400 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[10px] file:font-semibold file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 cursor-pointer" />
                            
                            {referenceImage && (
                                <button 
                                    onClick={() => setShowRefMasker(true)}
                                    className="px-2 py-1 mt-1 text-[10px] bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded border border-zinc-700 transition-colors self-start"
                                >
                                    Draw Mask on Reference
                                </button>
                            )}

                            {referenceMask && (
                                <div className="text-[10px] text-emerald-400 font-medium flex items-center gap-1 mt-1">
                                    <CheckCircle2 className="size-3" />
                                    Mask Ready
                                </div>
                            )}
                        </div>
                    </div>



                    {/* Output Configuration block */}
                    <div className="pt-3 border-t border-zinc-800/80">
                        <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                            <span>Export Format</span>
                            <select
                                value={outputFormat}
                                onChange={(e) => setOutputFormat(e.target.value)}
                                disabled={isProcessing}
                                className="bg-zinc-800 border border-zinc-700 text-zinc-200 text-[10px] px-2 py-1 rounded outline-none cursor-pointer"
                            >
                                <option value="source">Same as source</option>
                                <option value="png">PNG</option>
                                <option value="jpg">JPG</option>
                                <option value="webp">WEBP</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Processing controls */}
                <div className="flex flex-col gap-2 mt-auto">
                    {isProcessing ? (
                        <button
                            onClick={handleCancelBatch}
                            className="w-full py-2 rounded bg-red-600 hover:bg-red-500 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
                        >
                            <StopCircle className="size-3.5" />
                            <span>Cancel Batch</span>
                        </button>
                    ) : (
                        <button
                            disabled={fileQueue.length === 0}
                            onClick={processBatch}
                            className="w-full py-2 rounded bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
                        >
                            <Layers className="size-3.5" />
                            <span>Execute Smart Batch</span>
                        </button>
                    )}
                    
                    {!isProcessing && failedCount > 0 && (
                        <button
                            onClick={retryFailed}
                            className="w-full py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs border border-emerald-500/20 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                        >
                            <RefreshCw className="size-3.5" />
                            <span>Retry Failed ({failedCount})</span>
                        </button>
                    )}

                    <button 
                        onClick={clearQueue} 
                        disabled={isProcessing}
                        className="w-full py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-zinc-300 font-semibold text-xs border border-zinc-700/80 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                        <Trash2 className="size-3.5" />
                        <span>Reset Queue</span>
                    </button>
                </div>
            </aside>

            {/* Right Column: Dominant Queue Workspace */}
            <main className="flex-1 flex flex-col p-6 overflow-hidden">
                
                {/* Stats Counters Header */}
                <div className="flex items-center justify-between pb-4 border-b border-zinc-800/80 mb-4 shrink-0 font-mono text-xs text-zinc-400">
                    <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-zinc-200">QUEUE STATE:</span>
                        <span>{fileQueue.length} loaded</span>
                    </div>

                    <div className="flex items-center gap-3">
                        <span className="text-emerald-400 font-medium">{stats.completed} done</span>
                        <span className="text-zinc-500">{stats.skipped} skipped</span>
                        <span className="text-red-400">{stats.failed} failed</span>
                        {reviewCount > 0 && <span className="text-amber-400 font-bold">{reviewCount} review</span>}
                    </div>
                </div>

                {/* EXPORT TOOLBAR - Appears when completedCount > 0 and batch finishes */}
                {stats.completed > 0 && batchRecord?.batch_id && (
                    <div className="flex items-center gap-3 pb-4 mb-4 border-b border-zinc-800/50">
                        {selectedItems.size > 0 && (
                            <>
                                <button
                                    onClick={handlePreviewSelected}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/20 text-blue-400 text-xs font-semibold transition-colors"
                                >
                                    <Eye className="size-3.5" />
                                    <span>Preview Selected</span>
                                </button>
                                <button
                                    onClick={handleDownloadSelected}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/20 text-emerald-400 text-xs font-semibold transition-colors"
                                >
                                    <Download className="size-3.5" />
                                    <span>Download Selected</span>
                                </button>
                                <button
                                    onClick={handleDownloadSelectedZip}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-orange-600/10 hover:bg-orange-600/20 border border-orange-500/20 text-orange-400 text-xs font-semibold transition-colors"
                                >
                                    <Download className="size-3.5" />
                                    <span>ZIP Selected</span>
                                </button>
                            </>
                        )}
                        
                        <div className="flex-1" />

                        <button
                            onClick={handleDownloadAll}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/20 text-emerald-400 text-xs font-semibold transition-colors"
                        >
                            <Download className="size-3.5" />
                            <span>Download All</span>
                        </button>
                        
                        <a
                            href={`/api/batch/${batchRecord.batch_id}/download`}
                            download={`batch_${batchRecord.batch_id}.zip`}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-orange-600/10 hover:bg-orange-600/20 border border-orange-500/20 text-orange-400 text-xs font-semibold transition-colors"
                        >
                            <Download className="size-3.5" />
                            <span>ZIP All Completed</span>
                        </a>
                    </div>
                )}

                {/* Queue list table-like area */}
                <div className="flex-1 min-h-0 bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col">
                    {/* Selection Header */}
                    {fileQueue.length > 0 && (
                        <div className="flex items-center gap-2 p-2 border-b border-zinc-800 bg-zinc-950/50">
                            <button onClick={selectAll} className="text-[10px] px-2 py-1 bg-zinc-800 hover:bg-zinc-700 rounded text-zinc-300 transition-colors">Select All</button>
                            <button onClick={clearSelection} className="text-[10px] px-2 py-1 bg-zinc-800 hover:bg-zinc-700 rounded text-zinc-300 transition-colors">Select None</button>
                            <span className="text-[10px] text-zinc-500 ml-auto">{selectedItems.size} selected</span>
                        </div>
                    )}
                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {fileQueue.length === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 p-8 text-center">
                            <Layers className="size-8 text-zinc-600 mb-2 stroke-[1.5]" />
                            <p className="text-sm font-medium text-zinc-400">Batch Queue Empty</p>
                            <p className="text-xs text-zinc-600 max-w-xs mt-1">Load image files in the sidebar to populate the smart batch queue.</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-zinc-800/60">
                            {fileQueue.map((item) => {
                                const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.queued;
                                const Icon = cfg.icon;
                                return (
                                    <div key={item.id} className={`flex items-center justify-between p-3.5 ${cfg.bg} transition-colors font-mono text-[11px] ${selectedItems.has(item.name) ? 'ring-1 ring-inset ring-orange-500/30 bg-orange-500/5' : ''}`}>
                                        <div className="flex items-center gap-3 min-w-0 flex-1">
                                            <button 
                                                onClick={() => toggleSelection(item.name)} 
                                                className="text-zinc-500 hover:text-orange-400 transition-colors"
                                            >
                                                {selectedItems.has(item.name) ? <CheckSquare className="size-4 text-orange-500" /> : <Square className="size-4" />}
                                            </button>
                                            <Icon className={`size-4 shrink-0 ${cfg.color} ${item.status === 'processing' || item.status === 'detecting' ? 'animate-spin' : ''}`} />
                                            <span className="text-zinc-200 font-medium truncate max-w-[240px] cursor-default" onClick={() => toggleSelection(item.name)}>{item.name}</span>
                                            <span className="text-zinc-600 font-normal">({item.size})</span>
                                            
                                            {item.confidence !== null && (
                                                <span className="text-zinc-500 font-normal">conf={item.confidence?.toFixed(3)}</span>
                                            )}

                                            {item.message && (
                                                <span className="text-zinc-400 font-normal truncate max-w-[320px]">- {item.message}</span>
                                            )}
                                        </div>

                                        <div className="flex items-center gap-1 shrink-0">
                                            <span className={`px-2 py-0.5 mr-2 rounded border text-[9px] font-bold ${cfg.color} ${cfg.border} bg-black/30`}>
                                                {cfg.label.toUpperCase()}
                                            </span>
                                            
                                            {!isProcessing && item.status === 'completed' && batchRecord?.batch_id && (
                                                <>
                                                    <button 
                                                        onClick={() => handlePreviewSingle(item.name)}
                                                        className="p-1 rounded text-zinc-500 hover:text-blue-400 hover:bg-blue-400/10 transition-colors cursor-pointer"
                                                        title="Preview image"
                                                    >
                                                        <Eye className="size-3.5" />
                                                    </button>
                                                    <a 
                                                        href={`/api/batch/${batchRecord.batch_id}/download/${item.name}`}
                                                        download=""
                                                        className="p-1 rounded text-zinc-500 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                                                        title="Download image"
                                                    >
                                                        <Download className="size-3.5" />
                                                    </a>
                                                </>
                                            )}

                                            {!isProcessing && (
                                                <button onClick={() => removeFile(item.id)} className="p-1 rounded text-zinc-600 hover:text-red-400 hover:bg-red-400/10 transition-colors cursor-pointer" title="Remove from queue">
                                                    <XCircle className="size-3.5" />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                    </div>
                </div>

                {/* Persistent Batch Stats Output Cards */}
                {batchRecord && (
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mt-4 shrink-0 font-mono text-[10px] select-none">
                        <div className="p-2.5 rounded bg-zinc-900 border border-zinc-800">
                            <span className="text-zinc-500 block mb-0.5">BATCH STATUS</span>
                            <span className={`font-bold block ${batchRecord.status === 'CANCELLED' ? 'text-red-400' : 'text-emerald-400'}`}>
                                {batchRecord.status}
                            </span>
                        </div>
                        <div className="p-2.5 rounded bg-zinc-900 border border-zinc-800">
                            <span className="text-zinc-500 block mb-0.5">HARDWARE TARGET</span>
                            <span className="text-zinc-300 font-bold block">{batchRecord.device}</span>
                        </div>
                        <div className="p-2.5 rounded bg-zinc-900 border border-zinc-800">
                            <span className="text-zinc-500 block mb-0.5">TIME / IMAGE</span>
                            <span className="text-orange-400 font-bold block">{batchRecord.avg_time_per_image}s</span>
                        </div>
                        <div className="p-2.5 rounded bg-zinc-900 border border-zinc-800">
                            <span className="text-zinc-500 block mb-0.5">OUTPUT DIRECTORY</span>
                            <span className="text-zinc-400 truncate block font-sans" title={batchRecord.output_dir}>
                                {batchRecord.output_dir}
                            </span>
                        </div>
                    </div>
                )}

                {/* Action Console Log */}
                {batchLog && (
                    <div className="mt-4 shrink-0">
                        <div className="px-3 py-1 bg-zinc-900 border border-zinc-800 border-b-0 rounded-t-lg font-mono text-[10px] text-zinc-500">
                            SYSTEM LOG
                        </div>
                        <textarea
                            readOnly
                            value={batchLog}
                            className="w-full h-24 p-3 rounded-b-lg bg-zinc-900 border border-zinc-800 text-[10px] font-mono text-zinc-400 focus:outline-none resize-none"
                        />
                    </div>
                )}
            </main>
            
            {showRefMasker && referenceImage && (
                <ReferenceMaskEditor
                    imageFile={referenceImage}
                    onCancel={() => setShowRefMasker(false)}
                    onSave={(maskFile) => {
                        setReferenceMask(maskFile);
                        setShowRefMasker(false);
                    }}
                />
            )}

            {previewItems && batchRecord?.batch_id && (
                <BatchPreviewModal
                    items={previewItems}
                    initialIndex={previewInitialIndex}
                    batchId={batchRecord.batch_id}
                    onClose={() => setPreviewItems(null)}
                />
            )}
        </div>
    );
}
