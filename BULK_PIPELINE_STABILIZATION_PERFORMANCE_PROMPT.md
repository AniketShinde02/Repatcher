# AI Watermark Remover — Bulk Pipeline Stabilization & Performance Hardening
## Production Fix Prompt for Antigravity

> **Status:** The deterministic Gemini-removal direction is accepted, but the implementation is NOT considered production-ready until the benchmark, memory behavior, queue behavior, correctness validation, and Git checkpoint are proven.

---

## 0. NON-NEGOTIABLE RULE

Do NOT redesign the UI.

Do NOT add OmniRoute.

Do NOT add another AI model.

Do NOT rewrite the entire backend.

Do NOT perform a broad cleanup/refactor before creating a rollback checkpoint.

The current objective is:

1. Preserve the currently working watermark-removal state.
2. Find why 4 images currently take roughly 2–4 minutes.
3. Prove where the time is spent.
4. Make Bulk Mode fast, bounded, cancellable, resumable, and memory-safe.
5. Verify the deterministic Gemini path is actually correct.
6. Keep LaMa available only as a fallback for cases that genuinely require inpainting.
7. Make the system dynamically determine safe batch capacity instead of hardcoding an arbitrary maximum image count.
8. Update CHANGELOG.md with every material change.
9. Finish with a reproducible benchmark report.

---

# 1. FIRST: CREATE A REAL ROLLBACK CHECKPOINT

Before editing functional code:

### Inspect Git

Run:

- `git status`
- `git branch --show-current`
- `git log -5 --oneline`
- `git diff --stat`
- `git diff -- backend/core`
- `git ls-files`

Determine whether the repository already has uncommitted work.

### Create a checkpoint

Create a dedicated branch or tag representing the current working state.

Preferred:

`checkpoint/bulk-deterministic-working`

and a tag such as:

`checkpoint-bulk-deterministic-2026-08-27`

Do NOT destroy or reset existing user changes.

If the current tree contains uncommitted changes, preserve them explicitly before proceeding.

The checkpoint must allow a complete return to the exact pre-optimization state.

### Verify rollback

Record:

- branch
- commit SHA
- tag
- working-tree status

Write this into:

`docs/BULK_PIPELINE_CHECKPOINT.md`

---

# 2. FIX .gitignore BEFORE GENERATING MORE ARTIFACTS

Inspect the repository's existing `.gitignore`.

Do not blindly replace it.

Add only appropriate generated/local artifacts.

Likely candidates include:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.pyright/
.ruff_cache/

venv/
.venv/
env/

node_modules/
.next/
dist/
build/

debug/
debug_*/
artifacts/
tmp/
temp/
logs/

processed_images/
backend/temp/
stage_input/

*.log

# Local IDE / agent artifacts
.vscode/
.idea/

# OS
Thumbs.db
.DS_Store
```

IMPORTANT:

Do NOT ignore canonical assets required by the application.

For example, if:

`backend/core/gemini_alpha.npy`

is a real required runtime asset, it must remain tracked.

If it is only an experimental/generated artifact, do not keep it silently in the runtime path. Decide explicitly and document the decision.

Also inspect:

- model files
- test fixtures
- sample images
- generated reports
- local caches
- agent artifacts
- ZIP outputs

Do not commit large generated image batches.

---

# 3. UPDATE CHANGELOG IMMEDIATELY

Add a new entry before implementation begins.

Title:

`## [2026-08-27] — Bulk Pipeline Stabilization & Performance Investigation`

Document:

### Current state

- Deterministic Gemini removal has been introduced.
- LaMa is bypassed for confirmed Gemini watermark cases.
- Current UI test shows GPU is not being heavily utilized during the deterministic path.
- However, the observed end-to-end time for only 4 images is approximately 2–4 minutes.
- Therefore performance is NOT yet accepted.

### Investigation targets

- image decode
- image encode
- disk I/O
- watermark detection
- alpha-map loading
- alpha-map matching
- image copies
- debug artifact generation
- output writing
- queue overhead
- frontend polling
- backend startup/reload
- repeated initialization
- ZIP generation
- unnecessary serial waits
- worker creation/destruction
- thread oversubscription
- model initialization
- hidden LaMa invocation
- CUDA synchronization
- filesystem contention

---

# 4. DO NOT GUESS WHY 4 IMAGES TAKE 2–4 MINUTES

This is mandatory.

Add stage-level timing.

Every image must produce:

```text
decode_ms
detection_ms
mask_generation_ms
deterministic_removal_ms
validation_ms
encode_ms
write_ms
total_ms
```

At batch level also record:

```text
queue_wait_ms
worker_start_ms
initialization_ms
debug_artifact_ms
zip_ms
frontend_submission_ms
frontend_polling_ms
batch_total_ms
```

Use monotonic high-resolution timing.

Do NOT use one giant timer around the whole batch and guess.

---

# 5. ADD A PERFORMANCE REPORT

Create:

`docs/BULK_PERFORMANCE_REPORT.md`

For every benchmark run record:

| Metric | Value |
|---|---|
| Image count | |
| Resolution | |
| Input format | |
| Output format | |
| Total wall time | |
| Average image time | |
| Median image time | |
| P95 image time | |
| Decode total | |
| Detection total | |
| Removal total | |
| Validation total | |
| Encode total | |
| Write total | |
| Queue wait | |
| Peak RAM | |
| Peak VRAM | |
| GPU utilization | |
| CPU utilization | |
| Disk throughput | |
| Failed | |
| Retried | |

---

# 6. IMPORTANT: 150 IMAGES IN 1–3 SECONDS MUST BE VERIFIED, NOT ASSUMED

The historical claim that approximately 150 images completed in 1–3 seconds must be treated as an unverified benchmark.

For 1792×2400 images, the application still has to:

- read compressed JPEG bytes
- decode pixels
- inspect pixels
- locate/validate the watermark
- modify pixels
- encode output
- write output

Therefore do NOT optimize toward a fake number.

Run two benchmarks:

### A. End-to-end benchmark

Includes:

- disk read
- processing
- disk write

### B. Kernel benchmark

Measures only:

- detection
- deterministic removal

This will tell us whether the current slowdown is algorithmic or I/O/orchestration-related.

---

# 7. CHECK FOR THE MOST LIKELY CURRENT BOTTLENECKS

Inspect the implementation for:

## A. Repeated file reads

Bad:

```text
read image
detect
read image again
remove
read image again
validate
```

Preferred:

```text
read once
→ decode once
→ process in memory
→ validate
→ encode once
→ write once
```

Unless a second read is proven necessary.

---

## B. Repeated alpha/template loading

`gemini_alpha.npy` or other immutable detector assets must be loaded once per worker/process, not once per image.

Use worker initialization or a cached immutable object.

---

## C. Repeated detector initialization

Do NOT instantiate the detector for every image if it has immutable state.

Bad:

```python
for image in images:
    detector = GeminiSparkleDetector()
```

Preferred:

```python
detector = GeminiSparkleDetector()

for image in images:
    detector.detect(image)
```

---

## D. Repeated model initialization

LaMa must never be initialized for a Gemini deterministic batch unless a fallback image actually requires it.

---

## E. Debug artifacts

Debug overlays/masks must NOT be generated for every production image.

Debug mode should be opt-in.

Production:

```text
debug_artifacts = false
```

Diagnostic mode:

```text
debug_artifacts = true
```

For benchmark runs, debug output must be disabled unless specifically measuring it.

---

# 8. DETERMINISTIC REMOVAL MUST BE VALIDATED SCIENTIFICALLY

The current equation is:

```text
original = (watermarked - alpha * watermark_color) / (1 - alpha)
```

Do NOT assume this is universally valid.

Verify:

1. What watermark color is actually used?
2. Is it pure white?
3. Is alpha spatially constant or varying?
4. Is the watermark antialiased?
5. Is JPEG compression affecting the pixels?
6. Does the same alpha map work across different resolutions?
7. Does it work across different backgrounds?
8. Does it work across different JPEG qualities?
9. Is the current `gemini_alpha.npy` actually a calibrated watermark alpha map or merely an estimate derived from a contaminated background?

Build a synthetic test:

```text
known_clean_background
+
known_watermark(alpha, color)
=
synthetic_watermarked
```

Then reverse it.

Measure:

- MAE
- RMSE
- max absolute error
- PSNR
- changed-pixel percentage

The recovered image should be compared with the original known-clean image.

Do not call the method "mathematically perfect" unless the test supports that claim.

---

# 9. RESOLUTION NORMALIZATION

The watermark detector must NOT assume one fixed pixel size.

If the watermark is detected at:

```text
1792 × 2400
```

it must still work at:

```text
1024 × 1365
2048 × 2731
1536 × 2048
etc.
```

Use normalized coordinates and scale-aware matching.

Do not hardcode:

```text
x = 1730
y = 2330
```

or a fixed 64×64 location.

---

# 10. BULK MODE MUST NOT SHARE A SINGLE MASK ACROSS IMAGES

Every image gets its own:

```text
image
→ detection
→ confidence
→ bbox
→ alpha/mask transform
→ removal
→ validation
```

Never:

```text
detect image #1
→ reuse same pixel coordinates for images #2–#150
```

Reference mode may provide a normalized reference, but each target must still be validated.

---

# 11. PERFORMANCE ARCHITECTURE

For the deterministic Gemini path:

```text
Input Queue
    ↓
Bounded Worker Pool
    ↓
Decode
    ↓
Detect
    ↓
Deterministic Remove
    ↓
Validate
    ↓
Encode
    ↓
Write
    ↓
Result Queue
```

Do NOT load all 150+ decoded images into RAM simultaneously.

Use bounded concurrency.

The queue should contain lightweight job metadata/path references, not giant decoded arrays.

---

# 12. CONCURRENCY MUST BE ADAPTIVE

Do NOT blindly use:

```text
max_workers = 16
```

Do NOT use every CPU thread automatically.

Image libraries may themselves use native thread pools. Oversubscription can make performance worse.

Determine:

- physical CPU cores
- logical CPU count
- available RAM
- image dimensions
- estimated per-image working memory

Then select a safe worker count.

Start conservatively.

Example policy:

```text
workers = min(
    configured_max,
    physical_cores,
    RAM_safe_workers,
    IO_safe_workers
)
```

Benchmark 1, 2, 4, and possibly 6 workers.

Choose the fastest stable configuration, not the highest CPU utilization.

---

# 13. MEMORY BUDGET

Do NOT define a fake hardcoded "maximum 150 images".

The correct maximum is based on:

```text
available RAM
+
image dimensions
+
number of simultaneous decoded images
+
temporary buffers
+
encoding buffers
+
application overhead
```

For each job estimate:

```text
raw_image_bytes = width × height × channels
```

Then include a safety multiplier for temporary arrays.

The system should expose:

```text
estimated_memory_per_job
available_memory
safe_concurrency
queued_count
active_count
```

---

# 14. QUEUE SIZE ≠ ACTIVE PROCESSING COUNT

A user may upload:

```text
500 images
```

The system may accept all 500 as queue metadata.

But only a bounded number should be actively decoded/processed.

Example:

```text
500 queued
4 active
496 waiting
```

This is correct.

Do NOT decode all 500 immediately.

---

# 15. MAXIMUM BULK SIZE

Do not invent an arbitrary maximum.

Implement a configurable policy:

```text
MAX_BULK_IMAGES
```

but default it based on the application's tested memory/throughput envelope.

The UI should display:

```text
500 images queued
4 processing
496 waiting
```

If the system has a true limit, explain why:

```text
Maximum batch size: 500
Reason: configured application safety limit
```

But do not pretend this is a hardware maximum.

---

# 16. BACKPRESSURE

When active memory exceeds the configured budget:

```text
pause intake
```

Do not continue decoding.

When memory becomes available:

```text
resume intake
```

This prevents a large batch from destroying the user's machine.

---

# 17. CANCELLATION

Bulk Mode must support:

```text
Cancel batch
```

Cancellation states:

```text
QUEUED
RUNNING
CANCELLING
CANCELLED
COMPLETED
PARTIAL
FAILED
```

A cancelled batch must:

- stop starting new jobs
- allow the current image to finish safely
- clean temporary state
- preserve already completed outputs
- report exactly what completed

---

# 18. RESUME / RECOVERY

If the backend crashes after:

```text
37 / 150 completed
```

do not restart all 150.

Persist per-image state:

```text
queued
processing
completed
failed
cancelled
```

A restart should be able to resume safely.

Output filenames must be deterministic and collision-safe.

---

# 19. IDEMPOTENCY

If output already exists and has a valid completion record:

```text
do not process again
```

unless the user explicitly chooses:

```text
Reprocess
```

This matters enormously for large batches.

---

# 20. GPU POLICY

The deterministic Gemini path should use:

```text
GPU = OFF
```

unless profiling proves otherwise.

LaMa:

```text
GPU = ON
```

only when an image requires general-purpose inpainting.

Never initialize CUDA merely because the application has a CUDA-capable GPU.

The UI hardware badge may say CUDA is available, but availability does not mean every job should use it.

---

# 21. GPU FALLBACK POLICY

For non-deterministic images:

```text
Gemini detector
    ↓
confidence high
    → deterministic CPU
confidence uncertain
    → review / optional vision fallback
confidence high for generic watermark
    → LaMa
```

Never silently route everything through LaMa.

Never silently route everything through an external AI service.

---

# 22. GPU MEMORY SAFETY

If LaMa is invoked:

- one bounded GPU job at a time initially
- reuse loaded model
- never load model per image
- avoid concurrent model copies
- measure peak VRAM
- handle CUDA OOM explicitly
- release/reuse resources correctly
- fallback to CPU only when policy allows

Do not "solve" GPU problems by randomly switching devices.

---

# 23. FILE I/O

Measure:

```text
read time
decode time
encode time
write time
```

Do not assume CPU processing is the bottleneck.

If encode/write dominates, optimize that path.

Do not repeatedly save intermediate JPEGs.

Do not save PNG debug copies during normal production processing.

---

# 24. OUTPUT QUALITY

For JPEG input/output:

Do not silently degrade quality.

Preserve:

- dimensions
- orientation
- metadata where appropriate
- color mode
- expected JPEG quality

If "Same as source" is selected, preserve the source format.

For PNG, do not convert to JPEG unless explicitly configured.

---

# 25. BENCHMARK MATRIX

Run:

### Single image

1 image

### Small batch

4 images

### Medium batch

25 images

### Large batch

100 images

### Stress batch

150 images

If the machine remains stable, optionally:

300 images

Do NOT require 500 images to be physically processed if the machine cannot safely sustain it.

Measure:

- total wall time
- throughput images/sec
- average ms/image
- P95 ms/image
- peak RAM
- peak VRAM
- CPU
- GPU
- disk
- failures

---

# 26. CONCURRENCY BENCHMARK

For the same test set:

```text
workers=1
workers=2
workers=4
workers=6
```

Do not test arbitrary huge worker counts.

Pick the configuration with the best:

```text
throughput
+
stability
+
RAM safety
+
image correctness
```

---

# 27. IMPORTANT: DO NOT CHASE 100% GPU/CPU UTILIZATION

The objective is NOT:

```text
GPU = 100%
CPU = 100%
```

The objective is:

```text
maximum stable throughput
+
correct output
+
bounded memory
+
low latency
```

A CPU at 40% with 4× throughput is better than CPU at 100% with a slower system.

---

# 28. FRONTEND / BACKEND CONTRACT

The UI must receive real progress from the backend.

For each batch:

```json
{
  "total": 150,
  "queued": 146,
  "processing": 4,
  "completed": 37,
  "failed": 1,
  "review": 2,
  "cancelled": 0,
  "percent": 24.67
}
```

Do not calculate fake progress from frontend timers.

---

# 29. PREVIEW / RESULT GENERATION

Do not generate expensive preview assets for every image while processing.

Bulk processing should prioritize:

```text
process
→ save result
→ update status
```

Preview generation can happen after completion or on demand.

---

# 30. CLEAN TEMPORARY FILES

Every batch gets an isolated temporary directory:

```text
temp/batches/<batch_id>/
```

At completion:

```text
keep only required outputs
```

At cancellation/failure:

```text
cleanup temporary artifacts
```

Never leave thousands of debug files behind.

---

# 31. SECURITY / PATH SAFETY

Validate uploaded filenames.

Never trust user-supplied paths.

Use generated internal IDs.

Prevent:

```text
../../
absolute path injection
unexpected output directories
```

---

# 32. TESTS

Create automated tests for:

### Detection

- actual watermark detected
- no-watermark image not falsely detected
- different resolutions
- different backgrounds

### Deterministic removal

- synthetic known-alpha test
- real sample images
- JPEG-compressed sample
- edge cases

### Batch

- 1 image
- 4 images
- 25 images
- cancellation
- failure
- retry
- resume
- duplicate output
- partial completion

### Memory

- bounded active jobs
- queue does not decode everything

### GPU

- deterministic path does not initialize CUDA unnecessarily
- LaMa path uses bounded GPU concurrency

---

# 33. NO SUCCESS CLAIM WITHOUT VISUAL PROOF

For the 4 previously failing images create:

```text
before
detected overlay
mask
after
```

Verify manually.

A green `COMPLETED` status is NOT proof.

The watermark must actually be gone.

---

# 34. PERFORMANCE ACCEPTANCE CRITERIA

Do not invent an absolute number before measuring.

Acceptance should be based on:

### Correctness

100% of confirmed Gemini test images pass watermark-removal validation.

### Stability

No crashes during:

- 4
- 25
- 100
- 150 image tests

### Memory

Memory remains bounded and does not grow linearly with queued image count.

### GPU

Deterministic Gemini batch does not consume meaningful GPU resources.

### Throughput

Choose the best stable worker count from benchmark results.

### Regression

Single Mode must remain correct.

---

# 35. WHY THE CURRENT 2–4 MINUTE RESULT IS NOT ACCEPTABLE

Do not immediately blame the deterministic algorithm.

If the mathematical removal itself is truly ~0.04 sec/image, then 4 images should not require minutes solely because of the removal kernel.

Therefore profile:

```text
startup
detector initialization
alpha loading
decode
processing
validation
encode
write
debug
queue
polling
UI preview
ZIP
worker lifecycle
```

Find the exact stage.

---

# 36. IMPORTANT ARCHITECTURAL RULE

Do NOT introduce Redis/Celery/RQ/Ray just because "queues are good".

First make the local bounded worker pipeline fast and correct.

For a desktop/local-first application, an in-process bounded queue may be sufficient.

Only introduce Redis/Celery/RQ/Ray if profiling proves that the current architecture needs process isolation, persistence, distributed workers, or recovery beyond the current implementation.

The queue abstraction should remain replaceable.

---

# 37. CURRENT DESKTOP-FIRST TARGET

The application runs locally on the user's PC.

Therefore optimize for:

```text
Local filesystem
Local CPU
Optional local NVIDIA GPU
Local memory
No mandatory cloud dependency
```

The application must continue to work without OmniRoute.

---

# 38. CHANGELOG DISCIPLINE

After every meaningful implementation phase append:

```text
## [2026-08-27] — <change>

### Changed
...

### Why
...

### Validation
...

### Performance
...

### Risks
...
```

Do not write marketing-style claims.

Write measurable facts.

Bad:

> "Bulk Mode is now extremely fast."

Good:

> "100-image benchmark: 31.4 s total, 3.18 images/s, peak RAM 2.4 GB, peak VRAM 0.0 GB."

---

# 39. FINAL DELIVERABLES

Before declaring this phase complete, the repository must contain:

```text
.gitignore
CHANGELOG.md
docs/BULK_PIPELINE_CHECKPOINT.md
docs/BULK_PERFORMANCE_REPORT.md
tests/
```

and the required implementation files.

Do not commit:

```text
debug/
processed_images/
temporary output
large test batches
IDE agent artifacts
venv
node_modules
cache files
```

unless explicitly required.

---

# 40. FINAL REPORT FORMAT

Return:

## Git Checkpoint

- branch:
- tag:
- commit:
- clean working tree: YES/NO

## Root Cause of Slowdown

Exactly which stage caused the 2–4 minute runtime.

## Before

- 4 images:
- total:
- GPU:
- RAM:
- CPU:

## After

- 4 images:
- total:
- images/sec:
- GPU:
- RAM:
- CPU:

## Benchmark

| Batch | Workers | Total | img/s | Peak RAM | Peak VRAM | Failures |
|---|---:|---:|---:|---:|---:|---:|
| 1 | | | | | | |
| 4 | | | | | | |
| 25 | | | | | | |
| 100 | | | | | | |
| 150 | | | | | | |

## Maximum Safe Queue

Report:

- tested maximum
- configured maximum
- safe active concurrency
- estimated memory/job
- reason

Do NOT claim an arbitrary hardware maximum.

## Correctness

- Gemini detection:
- deterministic removal:
- Single Mode regression:
- Bulk Mode:
- cancellation:
- resume:
- retry:

## GPU

Explain exactly when GPU is used and when it is not.

## Files Changed

List every changed file.

## Tests Run

List actual commands and actual results.

## Remaining Risks

List them honestly.

---

# FINAL COMMAND

Do this in order:

1. Git checkpoint.
2. `.gitignore`.
3. CHANGELOG.
4. Instrument timing.
5. Find the 2–4 minute bottleneck.
6. Fix bottleneck.
7. Add bounded worker queue.
8. Add memory/backpressure protection.
9. Validate deterministic removal mathematically.
10. Run 1/4/25/100/150 benchmarks.
11. Verify GPU behavior.
12. Verify Single Mode.
13. Verify Bulk Mode.
14. Verify cancellation/recovery.
15. Update CHANGELOG.
16. Produce final performance report.

DO NOT jump directly to a new architecture.

DO NOT declare success from a green UI status.

DO NOT claim 150 images can be processed in 1–3 seconds unless the benchmark actually measures full decode → processing → encode → write and proves it.

The goal is a production-grade local bulk pipeline, not a benchmark illusion.
