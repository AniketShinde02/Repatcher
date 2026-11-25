import React, { useState, useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, Download } from 'lucide-react';

export default function BatchPreviewModal({ items, initialIndex = 0, batchId, onClose }) {
    const [currentIndex, setCurrentIndex] = useState(initialIndex);
    const [viewMode, setViewMode] = useState('split'); // 'split', 'original', 'result'
    
    // items should be [{ name: "filename.jpg", file: File(original) }, ...]
    const currentItem = items[currentIndex];

    const handlePrev = () => setCurrentIndex(i => (i > 0 ? i - 1 : items.length - 1));
    const handleNext = () => setCurrentIndex(i => (i < items.length - 1 ? i + 1 : 0));

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'ArrowLeft') handlePrev();
            if (e.key === 'ArrowRight') handleNext();
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [items.length]);

    if (!currentItem) return null;

    const originalUrl = currentItem.file ? URL.createObjectURL(currentItem.file) : null;
    const resultUrl = `/api/batch/${batchId}/download/${currentItem.name}`;

    return (
        <div className="fixed inset-0 z-[100] bg-black/95 flex flex-col font-sans">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950">
                <div className="flex items-center gap-4 text-zinc-200">
                    <span className="font-mono text-sm uppercase tracking-wider">Preview ({currentIndex + 1} / {items.length})</span>
                    <span className="text-xs text-zinc-500 font-mono truncate max-w-xs">{currentItem.name}</span>
                    
                    <div className="flex items-center gap-1 bg-zinc-900 rounded p-1 ml-4 border border-zinc-800">
                        <button 
                            onClick={() => setViewMode('original')} 
                            className={`px-3 py-1 text-xs rounded font-semibold cursor-pointer ${viewMode === 'original' ? 'bg-orange-600 text-white' : 'hover:bg-zinc-800 text-zinc-400'}`}
                        >
                            Original
                        </button>
                        <button 
                            onClick={() => setViewMode('split')} 
                            className={`px-3 py-1 text-xs rounded font-semibold cursor-pointer ${viewMode === 'split' ? 'bg-orange-600 text-white' : 'hover:bg-zinc-800 text-zinc-400'}`}
                        >
                            Split
                        </button>
                        <button 
                            onClick={() => setViewMode('result')} 
                            className={`px-3 py-1 text-xs rounded font-semibold cursor-pointer ${viewMode === 'result' ? 'bg-orange-600 text-white' : 'hover:bg-zinc-800 text-zinc-400'}`}
                        >
                            Result
                        </button>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <a 
                        href={resultUrl}
                        download={currentItem.name}
                        className="flex items-center gap-2 px-4 py-2 rounded border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 text-sm font-semibold transition-colors cursor-pointer"
                    >
                        <Download className="size-4" />
                        <span>Download This</span>
                    </a>
                    <button onClick={onClose} className="p-2 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer">
                        <X className="size-5" />
                    </button>
                </div>
            </div>
            
            {/* Main Area */}
            <div className="flex-1 relative flex items-center justify-center p-4 overflow-hidden">
                <button 
                    onClick={handlePrev}
                    className="absolute left-4 p-3 bg-zinc-900/80 hover:bg-zinc-800 text-white rounded-full z-10 transition-colors border border-zinc-700 cursor-pointer"
                >
                    <ChevronLeft className="size-6" />
                </button>

                <div className="w-full h-full flex items-center justify-center relative">
                    {viewMode === 'original' && (
                        <img src={originalUrl} className="max-w-full max-h-full object-contain" alt="Original" />
                    )}
                    {viewMode === 'result' && (
                        <img src={resultUrl} className="max-w-full max-h-full object-contain" alt="Result" />
                    )}
                    {viewMode === 'split' && (
                        <div className="flex w-full h-full gap-4">
                            <div className="flex-1 flex flex-col items-center justify-center relative border border-zinc-800 rounded bg-zinc-900/50">
                                <span className="absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] font-mono text-zinc-400">ORIGINAL</span>
                                <img src={originalUrl} className="max-w-full max-h-full object-contain p-2" alt="Original" />
                            </div>
                            <div className="flex-1 flex flex-col items-center justify-center relative border border-zinc-800 rounded bg-zinc-900/50">
                                <span className="absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] font-mono text-emerald-400">RESULT</span>
                                <img src={resultUrl} className="max-w-full max-h-full object-contain p-2" alt="Result" />
                            </div>
                        </div>
                    )}
                </div>

                <button 
                    onClick={handleNext}
                    className="absolute right-4 p-3 bg-zinc-900/80 hover:bg-zinc-800 text-white rounded-full z-10 transition-colors border border-zinc-700 cursor-pointer"
                >
                    <ChevronRight className="size-6" />
                </button>
            </div>
            
            {/* Footer with Thumbnails */}
            <div className="h-24 border-t border-zinc-800 bg-zinc-950 flex items-center px-4 gap-2 overflow-x-auto custom-scrollbar flex-nowrap shrink-0">
                {items.map((item, idx) => (
                    <button
                        key={item.name}
                        onClick={() => setCurrentIndex(idx)}
                        className={`shrink-0 w-16 h-16 rounded overflow-hidden border-2 transition-colors cursor-pointer ${idx === currentIndex ? 'border-orange-500' : 'border-transparent hover:border-zinc-700'}`}
                        title={item.name}
                    >
                        {item.file && (
                            <img 
                                src={URL.createObjectURL(item.file)} 
                                className="w-full h-full object-cover" 
                                alt="thumb"
                                onLoad={(e) => URL.revokeObjectURL(e.target.src)} 
                            />
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}
