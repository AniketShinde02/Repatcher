import requests
import time
import sys
from pathlib import Path

BACKEND_URL = "http://localhost:8000"

def test_api_end_to_end(count: int = 5):
    stage_dir = Path("backend/temp/stage_input")
    all_imgs = sorted(list(stage_dir.glob("7bb111e7*")))
    if not all_imgs:
        all_imgs = sorted(list(Path(".").glob("*.jpeg"))) + sorted(list(Path(".").glob("*.png")))
        
    imgs = all_imgs[:count]
    print(f"=== E2E API Test with {len(imgs)} images ===")
    for p in imgs:
        print(f" - {p.name}")
        
    files = []
    for path in imgs:
        files.append(('files', (path.name, open(path, 'rb'), 'image/jpeg')))
        
    print("\n1. Submitting batch to POST /batch...")
    resp = requests.post(f"{BACKEND_URL}/batch", files=files)
    if resp.status_code != 200:
        print(f"FAILED to initiate batch: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    batch_id = data.get("batch_id")
    print(f"Batch created! batch_id: {batch_id}")
    
    print("2. Polling GET /batch/{batch_id}...")
    start_t = time.time()
    last_status = None
    
    while True:
        status_resp = requests.get(f"{BACKEND_URL}/batch/{batch_id}")
        if status_resp.status_code != 200:
            print(f"Poll Error: {status_resp.status_code} {status_resp.text}")
            time.sleep(0.5)
            continue
            
        status_data = status_resp.json()
        status = status_data.get("status")
        processed = status_data.get("processed", 0)
        total = status_data.get("total", 0)
        completed = status_data.get("completed", 0)
        failed = status_data.get("failed", 0)
        skipped = status_data.get("skipped", 0)
        items = status_data.get("items", [])
        
        current_summary = f"Status: {status} | Processed: {processed}/{total} (Comp: {completed}, Fail: {failed}, Skip: {skipped})"
        if current_summary != last_status:
            print(f"[{time.time() - start_t:.2f}s] {current_summary}")
            for item in items:
                print(f"   -> {item['filename']}: {item['status']} ({item.get('error', '')})")
            last_status = current_summary
            
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            print(f"\nBatch Finalized in {time.time() - start_t:.2f}s!")
            print(f"Total time: {status_data.get('total_time_sec')}s | Avg per img: {status_data.get('avg_time_per_image')}s")
            break
            
        time.sleep(0.5)
        if time.time() - start_t > 60:
            print("\nTIMEOUT: Batch did not complete within 60 seconds!")
            sys.exit(1)

if __name__ == "__main__":
    count = 5
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    test_api_end_to_end(count)
