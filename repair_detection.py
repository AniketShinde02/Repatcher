import sys

lines = open('backend/core/detection.py', encoding='utf-8').readlines()

# Lines 347-353 are the broken raw_signals dict body.
# Line 354 onward has the orphaned template-matcher code (originally from another block)
# We keep lines 1-353, inject the closing of the candidates.append block,
# inject the NMS + singleton-detector block, then skip line 354 (which is the old
# "# We will prioritize..." comment that got misplaced) and keep 355 onward.

fixed = lines[:353]  # 0-indexed: [0..352], i.e. lines 1-353 inclusive

# Close the raw_signals dict and the candidates.append call
fixed.append('                "location": (round(cx_rel, 2), round(cy_rel, 2)),\n')
fixed.append('            },\n')
fixed.append('            "signal_scores": {k: round(v, 3) for k, v in signals.items()},\n')
fixed.append('        })\n')
fixed.append('\n')
fixed.append('    # NMS: suppress overlapping lower-score duplicates\n')
fixed.append('    candidates = non_max_suppression(candidates)\n')
fixed.append('\n')
fixed.append('    # Classify candidates by confidence tier\n')
fixed.append('    high_med = [c for c in candidates if c["score"] >= conf_medium]\n')
fixed.append('\n')
fixed.append('    # Template Matching Detector: singleton loaded once per process\n')
fixed.append('    global _gemini_detector\n')
fixed.append('    if _gemini_detector is None:\n')
fixed.append('        from backend.core.sparkle_detector import GeminiSparkleDetector\n')
fixed.append('        _gemini_detector = GeminiSparkleDetector()\n')
fixed.append('    detector = _gemini_detector\n')
fixed.append('    template_res = detector.detect(img)\n')
fixed.append('    t_score = template_res["score"]\n')
fixed.append('    t_bbox = template_res["bbox"]\n')
fixed.append('\n')
fixed.append('    is_gemini = False\n')
fixed.append('\n')

# Skip line 354 (the orphaned "# We will prioritize..." comment) and append from 355 onward
fixed += lines[354:]

open('backend/core/detection.py', 'w', encoding='utf-8').writelines(fixed)
print(f"Repaired. Total lines: {len(fixed)}")
