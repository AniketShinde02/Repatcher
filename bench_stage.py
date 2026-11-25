import time
import cv2
import numpy as np
import psutil
import os
from pathlib import Path

from backend.core.sparkle_detector import GeminiSparkleDetector
from backend.core.deterministic_removal import DeterministicGeminiRemover
from backend.core.cv_utils import safe_imread

img_dir = Path(r'D:\Starter Kit\image_processor_sandbox\processed_images\66b9f031-2fef-4e1f-8873-869c583762ec')
images = list(img_dir.glob('*.jpg'))[:4]

detector = GeminiSparkleDetector()
remover = DeterministicGeminiRemover()

results = []
process = psutil.Process(os.getpid())

print(f'--- Stage Timing Benchmark ({len(images)} images) ---')
for img_path in images:
    row = {'file': img_path.name[:45]}
    t0 = time.perf_counter()

    # DECODE
    img = safe_imread(str(img_path))
    t1 = time.perf_counter()
    row['decode_ms'] = round((t1-t0)*1000, 1)

    # DETECT
    det = detector.detect(img)
    t2 = time.perf_counter()
    row['detect_ms'] = round((t2-t1)*1000, 1)
    row['score'] = round(det['score'], 3)
    row['bbox'] = det['bbox']

    # MASK GEN
    mask = detector.generate_mask(img.shape[:2], det['bbox'])
    t3 = time.perf_counter()
    row['mask_ms'] = round((t3-t2)*1000, 1)

    # DETERMINISTIC REMOVE
    bbox = det['bbox']
    cleaned = remover.remove(img, bbox)
    t4 = time.perf_counter()
    row['removal_ms'] = round((t4-t3)*1000, 1)

    # VALIDATION
    roi_before = img[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]].astype(float)
    roi_after  = cleaned[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]].astype(float)
    diff = np.abs(roi_before - roi_after)
    changed = int(np.sum(diff > 5))
    t5 = time.perf_counter()
    row['validate_ms'] = round((t5-t4)*1000, 1)
    row['changed_px'] = changed

    # ENCODE
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
    _, buf = cv2.imencode('.jpg', cleaned, encode_params)
    t6 = time.perf_counter()
    row['encode_ms'] = round((t6-t5)*1000, 1)

    # WRITE
    out_path = Path('debug') / ('bench_' + img_path.name)
    out_path.write_bytes(buf.tobytes())
    t7 = time.perf_counter()
    row['write_ms'] = round((t7-t6)*1000, 1)

    row['total_ms'] = round((t7-t0)*1000, 1)
    row['ram_mb'] = round(process.memory_info().rss / 1e6, 1)
    results.append(row)
    fname = img_path.name[:40]
    line = f"decode={row['decode_ms']}ms detect={row['detect_ms']}ms mask={row['mask_ms']}ms remove={row['removal_ms']}ms validate={row['validate_ms']}ms encode={row['encode_ms']}ms write={row['write_ms']}ms TOTAL={row['total_ms']}ms RAM={row['ram_mb']}MB score={row['score']} changed_px={row['changed_px']}"
    print(fname)
    print('  ' + line)

totals = {k: round(sum(r[k] for r in results), 1) for k in ['decode_ms','detect_ms','mask_ms','removal_ms','validate_ms','encode_ms','write_ms','total_ms']}
avg_total = totals['total_ms']/len(results)
print()
print('--- Totals ---')
for k,v in totals.items():
    print(f'  {k}: {v}ms')
print(f'  avg_per_image: {round(avg_total,1)}ms')
print(f'  throughput: {round(1000/avg_total,2)} img/s')
