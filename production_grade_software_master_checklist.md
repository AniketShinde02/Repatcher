# Production-Grade Software Engineering & Release Master Checklist

**Project:** AI Watermark Remover / Local Image Processing Application\
**Document purpose:** A single A-to-Z production-readiness specification
covering engineering, runtime, AI models, packaging, Docker,
installation, upgrades, security, reliability, UX, observability,
testing, release, and end-user recovery.

> **Release rule:** A feature is not considered complete because the UI
> exists, an API returns `200`, or a build succeeds. A core feature is
> complete only when a real user can execute the complete workflow
> successfully and the result is verified.

------------------------------------------------------------------------

## 0. Non-Negotiable Definition of Done

The software must satisfy this chain:

**Install → Start → Detect environment → Discover models → Load models →
Process real input → Produce real output → Save/download → Restart →
Work again**

No fake success states.

No placeholder controls presented as functional.

No hard-coded developer-machine paths.

No dependency on the developer's global Python/Node installation.

No requirement for the user to manually repair PATH, CUDA, Python
packages, model folders, or ports.

Every failure must be diagnosable.

Every destructive or irreversible action must be explicit.

Every important user-visible operation must have a recoverable state.

------------------------------------------------------------------------

# 1. Product Architecture

## 1.1 Define the system boundaries

Document and enforce:

-   Frontend/UI
-   Backend/API
-   AI/model runtime
-   Image-processing layer
-   Batch/job engine
-   Model manager
-   Device manager
-   Filesystem/storage layer
-   Export layer
-   Configuration layer
-   Logging/diagnostics
-   Packaging/runtime launcher
-   Installer/updater
-   Docker runtime
-   Optional native desktop shell

Each layer must have a clear responsibility.

## 1.2 No accidental coupling

The UI must not:

-   know model filesystem internals
-   construct backend filesystem paths
-   assume CUDA exists
-   assume a specific username
-   assume a specific drive
-   assume localhost ports never change
-   directly manipulate model files
-   depend on temporary frontend state for persistent jobs

The backend must own authoritative processing state.

## 1.3 Configuration

Centralize:

-   application version
-   API host/port
-   frontend port
-   model directory
-   cache directory
-   staging directory
-   output directory
-   maximum upload size
-   supported formats
-   device preference
-   model preference
-   logging level
-   batch limits
-   concurrency limits

No scattered constants.

------------------------------------------------------------------------

# 2. Repository & Project Structure

Recommended structure:

``` text
project/
├─ web_ui/
├─ backend/
│  ├─ app/
│  ├─ core/
│  ├─ services/
│  ├─ models/
│  └─ tests/
├─ models/
│  └─ manifest/
├─ scripts/
├─ packaging/
│  ├─ docker/
│  ├─ desktop/
│  └─ installers/
├─ docs/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ e2e/
│  ├─ fixtures/
│  └─ performance/
├─ config/
├─ CHANGELOG.md
├─ README.md
├─ LICENSE
└─ .gitignore
```

Do not commit:

``` text
.venv/
venv/
node_modules/
.next/
dist/
build/
__pycache__/
*.pyc
runtime caches
temporary files
user outputs
private credentials
large generated artifacts
```

Model weights should be handled deliberately rather than accidentally
committed.

------------------------------------------------------------------------

# 3. Git & Version Control

Before release:

-   initialize Git if not already initialized
-   create a clean initial commit
-   define main/development branch strategy
-   use meaningful commits
-   tag releases
-   keep CHANGELOG updated
-   document breaking changes
-   add `.gitignore`
-   add `.gitattributes` if needed
-   use Git LFS or a model artifact registry if model files must be
    versioned
-   never commit secrets
-   never commit user images
-   never commit generated runtime caches

Release must be reproducible from a known commit/tag.

------------------------------------------------------------------------

# 4. Python Runtime Isolation

Use a project-owned Python environment during development/build.

Python `venv` creates an isolated environment with its own installed
packages and is intended to be disposable/recreated rather than copied
between machines. Do not treat a developer's `.venv` as a distributable
artifact.

Required:

-   pin supported Python versions
-   create `.venv`/`venv`
-   install dependencies only inside the environment
-   lock or pin dependencies
-   document installation
-   test from a clean environment
-   test with no globally installed project dependencies

Important:

**Do not ship a developer's venv as the universal cross-machine
runtime.**

For a packaged desktop application, bundle the runtime using an
appropriate application bundler or installer.

------------------------------------------------------------------------

# 5. Node Runtime

For the frontend:

-   pin Node major/minor as appropriate
-   use `package.json` engines where useful
-   commit the package-manager lockfile
-   use one package manager consistently
-   build from a clean environment
-   ensure production build has no development-only dependency
    requirement
-   never rely on a developer's globally installed Next.js CLI

Verify:

``` text
install
build
start
restart
```

------------------------------------------------------------------------

# 6. Dependency Management

Every dependency must have a reason.

Audit:

-   Python dependencies
-   Node dependencies
-   native libraries
-   CUDA dependencies
-   model dependencies
-   system packages
-   browser/runtime assumptions

For every dependency record:

-   package
-   version
-   purpose
-   license
-   whether runtime/build/test only
-   whether platform-specific
-   whether it requires GPU
-   whether it requires network access

Run vulnerability/dependency audits before release.

------------------------------------------------------------------------

# 7. AI Model Management

## 7.1 Model manifest

Create a machine-readable model manifest:

``` text
model_id
display_name
version
filename
expected_size
checksum
framework
minimum_runtime
supported_devices
license
source
download_url
optional/required
```

Never infer model identity solely from a filename.

## 7.2 Model discovery

At startup:

1.  locate application data directory
2.  locate model directory
3.  read manifest
4.  check model existence
5.  check size
6.  verify checksum when available
7.  verify loadability
8.  determine compatible device
9.  report exact state

States:

``` text
NOT_INSTALLED
DISCOVERING
VERIFYING
AVAILABLE
LOADING
READY
INCOMPATIBLE
CORRUPTED
ERROR
```

## 7.3 Existing model handling

If a user already has the model:

-   discover it
-   validate it
-   reuse it
-   do not redownload it unnecessarily
-   do not overwrite it without explicit approval
-   do not duplicate multi-GB weights unnecessarily

If the model is incompatible or corrupted:

-   explain why
-   provide repair/re-download
-   preserve a backup when appropriate

## 7.4 Model download

If a model is missing:

-   show model name
-   show size
-   show progress
-   show download speed
-   show ETA where reliable
-   support retry
-   validate checksum after download
-   use temporary `.partial` file
-   atomically rename only after successful validation
-   recover safely after interrupted download

Never report "Installed" before verification succeeds.

------------------------------------------------------------------------

# 8. Packaging Strategy

There are two different concepts:

### Development environment

Uses:

-   Python venv
-   Node environment
-   source code
-   development dependencies

### End-user application

Uses:

-   packaged runtime
-   application files
-   required native dependencies
-   model manager
-   user-data directories
-   installer/launcher
-   optional Docker runtime

Do not confuse these.

------------------------------------------------------------------------

# 9. Desktop Packaging

For a native desktop distribution, prefer a predictable
**one-folder/installer architecture** over forcing every large model
into a single executable.

A Python bundler such as PyInstaller can bundle Python, dependencies and
application files into a distributable folder. Its documentation
explicitly supports adding data files and binaries through spec files.
It is not a cross-compiler: builds should be produced/tested on the
target OS.

Recommended conceptual layout:

``` text
AIWatermarkRemover/
├─ AIWatermarkRemover.exe
├─ runtime/
├─ backend/
├─ frontend/
├─ models/
├─ resources/
└─ licenses/
```

Large mutable models should preferably live in a user-data/model
directory rather than inside an immutable executable payload.

------------------------------------------------------------------------

# 10. First-Run Experience

A fresh user must be able to:

1.  install
2.  launch
3.  see setup/initialization status
4.  detect hardware
5.  detect existing models
6.  download missing required models
7.  verify model integrity
8.  initialize runtime
9.  open the application

No terminal commands should be required for normal users.

If a dependency cannot be bundled, the application must explicitly
identify it and provide a controlled setup path.

------------------------------------------------------------------------

# 11. Portable User Data Layout

Use OS-appropriate user-data locations.

Conceptually:

``` text
user-data/
├─ models/
├─ cache/
├─ outputs/
├─ temp/
├─ logs/
├─ config/
├─ jobs/
└─ state/
```

Never store user data beside source code by accident.

Never use:

``` text
C:\Users\DeveloperName\...
D:\Starter Kit\...
```

as runtime defaults.

------------------------------------------------------------------------

# 12. Installation Conflict Prevention

The installer/runtime must survive users who already have:

-   Python
-   CUDA
-   PyTorch
-   Node
-   Git
-   another version of the software
-   another model version
-   another application using the same ports
-   different environment variables
-   different GPU drivers

Rules:

-   do not overwrite unrelated system packages
-   do not mutate global Python packages
-   do not silently change system PATH
-   do not overwrite user models
-   use application-owned runtime paths
-   detect port conflicts
-   detect incompatible drivers
-   provide actionable recovery

------------------------------------------------------------------------

# 13. GPU / CPU Runtime

Detect actual hardware.

Do not hard-code:

``` text
NVIDIA GeForce RTX 3050
```

Instead detect:

-   vendor
-   device name
-   VRAM
-   driver capability
-   CUDA availability
-   framework CUDA availability

Decision:

``` text
GPU available + compatible
→ GPU

GPU unavailable
→ CPU

GPU detected but runtime initialization fails
→ controlled CPU fallback
```

Show the real active device.

Do not claim CUDA acceleration when inference is actually running on
CPU.

------------------------------------------------------------------------

# 14. GPU Memory Management

Track:

-   VRAM allocation
-   peak VRAM
-   model memory
-   per-image memory
-   batch memory
-   failures due to OOM

For OOM:

1.  catch the failure
2.  release temporary tensors
3.  clear safe caches
4.  retry using a safer strategy where appropriate
5.  fall back to CPU if configured
6.  report the actual reason

Do not blindly retry forever.

------------------------------------------------------------------------

# 15. Core Image Pipeline

Canonical flow:

``` text
Input
↓
Validate
↓
Decode
↓
Orient
↓
Normalize
↓
Detect / Manual Mask
↓
Validate Mask
↓
Model Inference
↓
Post-process
↓
Restore Original Dimensions
↓
Encode
↓
Persist Output
↓
Return Output Metadata
```

Every stage must be testable independently.

------------------------------------------------------------------------

# 16. Single Editor

Required:

-   image upload
-   drag/drop
-   file validation
-   pan
-   zoom
-   fit
-   reset
-   Paint
-   Erase Mask
-   brush size
-   visible cursor
-   clear mask
-   automatic detection
-   candidate review
-   processing
-   progress
-   cancellation where supported
-   actual result
-   before/after
-   comparison slider
-   download
-   export format
-   error recovery

------------------------------------------------------------------------

# 17. Paint Tool

Verify:

-   mouse
-   pointer events
-   drag
-   click
-   fast movement
-   slow movement
-   zoom 50%
-   zoom 100%
-   zoom 200%
-   pan
-   browser resize
-   image edge
-   large brush
-   tiny brush

Mask coordinates must always map to original image coordinates.

------------------------------------------------------------------------

# 18. Erase Tool

Define the semantics clearly.

**Erase = erase the mask**, not destroy pixels in the original image.

Paint:

``` text
mask += stroke
```

Erase:

``` text
mask -= stroke
```

The source image remains unchanged until processing.

If actual object removal is offered, call it:

**Object Remove / Inpaint**

Workflow:

``` text
select object
↓
generate mask
↓
inpaint
↓
show reconstructed image
```

The UI must never confuse mask editing with destructive source-image
editing.

------------------------------------------------------------------------

# 19. Automatic Detection

Must:

-   inspect actual input
-   generate real candidate regions
-   provide confidence
-   create real masks
-   display candidates
-   allow review
-   respect sensitivity
-   respect edge padding

Confidence policy:

``` text
HIGH
→ process automatically if enabled

MEDIUM
→ review

LOW
→ skip or require explicit approval
```

Never report success with an empty mask.

------------------------------------------------------------------------

# 20. Inpainting Engine

The production pipeline must call the actual working model engine.

Verify:

-   image reaches backend
-   mask reaches backend
-   dimensions match
-   model loads
-   device is correct
-   inference occurs
-   output is generated
-   output is decoded
-   output is returned
-   output is not identical to the input when a valid removal was
    requested

Compare against the known-working Gradio/IOPaint implementation if one
exists.

If the old implementation is reliable, reuse its proven model invocation
path rather than maintaining a broken parallel implementation.

------------------------------------------------------------------------

# 21. Result Verification

After processing:

-   display actual result
-   preserve dimensions
-   preserve aspect ratio
-   avoid accidental crop
-   avoid accidental resize
-   verify file exists
-   verify file decodes
-   verify file size \> 0

UI must not show "Completed" until the output actually exists and passes
validation.

------------------------------------------------------------------------

# 22. Before/After UX

Provide:

### Side-by-side

``` text
ORIGINAL | PROCESSED
```

### Slider

``` text
ORIGINAL ← slider → PROCESSED
```

Both must operate on the actual source/result pair.

------------------------------------------------------------------------

# 23. Export System

Single:

-   Same as source
-   PNG
-   JPEG
-   WEBP

Batch:

-   Same as source
-   PNG
-   JPEG
-   WEBP
-   Individual files
-   ZIP

Use deterministic names:

``` text
originalname_processed.ext
```

or an equivalent documented convention.

Never silently overwrite the original.

------------------------------------------------------------------------

# 24. Browser Save Behaviour

A browser application cannot assume unrestricted filesystem access.

Therefore:

### Web mode

Use browser download/save behaviour.

### Native desktop mode

Use a native save-folder picker.

The storage abstraction should support both.

Do not build fake "save path" controls that do nothing.

------------------------------------------------------------------------

# 25. Batch Engine

Batch architecture:

``` text
CREATE JOB
↓
VALIDATE ALL INPUTS
↓
QUEUE
↓
LOAD MODEL ONCE
↓
PROCESS IMAGE 1
↓
PROCESS IMAGE 2
↓
...
↓
PROCESS IMAGE N
↓
WRITE OUTPUTS
↓
GENERATE SUMMARY
```

Do not load the model once per image.

------------------------------------------------------------------------

# 26. Batch States

Each item:

``` text
QUEUED
VALIDATING
DETECTING
REVIEW_REQUIRED
PROCESSING
SAVING
COMPLETED
SKIPPED
FAILED
CANCELLED
```

Job:

``` text
CREATED
QUEUED
RUNNING
CANCELLING
COMPLETED
PARTIAL
FAILED
CANCELLED
```

------------------------------------------------------------------------

# 27. Batch Performance

Benchmark:

``` text
1 image
2 images
5 images
10 images
25 images
50 images
```

Record:

-   model load
-   detection
-   inference
-   encoding
-   disk I/O
-   total
-   average/image
-   peak RAM
-   peak VRAM

Investigate:

-   model reload
-   duplicate preprocessing
-   repeated disk copies
-   repeated initialization
-   CPU/GPU transfers
-   CUDA synchronization
-   frontend polling
-   encoding overhead

Do not blindly add GPU parallelism.

------------------------------------------------------------------------

# 28. Batch Failure Isolation

One bad image must not kill the entire batch.

Test:

``` text
valid
valid
corrupt
valid
unsupported
valid
```

Expected:

``` text
COMPLETED
COMPLETED
FAILED
COMPLETED
SKIPPED
COMPLETED
```

Final batch summary must be accurate.

------------------------------------------------------------------------

# 29. Batch Cancellation

Implement cancellation.

Requirements:

-   stop starting new work
-   safely finish or interrupt current work when supported
-   cancel queued items
-   clean temporary files
-   persist final status
-   allow UI reconnection

------------------------------------------------------------------------

# 30. Retry Failed

Provide:

**Retry Failed**

Only failed items retry.

Completed items are not reprocessed unless explicitly requested.

------------------------------------------------------------------------

# 31. ZIP Export

ZIP must contain only successful outputs.

Never include:

-   masks
-   source files unless explicitly selected
-   temporary files
-   logs
-   models
-   cache
-   application binaries

Validate the resulting ZIP.

------------------------------------------------------------------------

# 32. File Validation

Accept only explicitly supported image formats.

Test:

-   JPG/JPEG
-   PNG
-   WEBP
-   BMP
-   TIFF if supported

Test filenames containing:

-   spaces
-   Unicode
-   parentheses
-   multiple dots
-   uppercase extensions
-   very long names

Reject dangerous/unwanted formats.

Backend validation is authoritative.

------------------------------------------------------------------------

# 33. Image Edge Cases

Test:

-   tiny image
-   large image
-   portrait
-   landscape
-   square
-   very wide
-   very tall
-   transparent PNG
-   EXIF orientation
-   corrupted image
-   zero-byte file
-   oversized file
-   unusual color modes
-   unsupported bit depth

------------------------------------------------------------------------

# 34. Mask Edge Cases

Test:

-   empty mask
-   one-pixel mask
-   full-image mask
-   edge-touching mask
-   multiple disconnected regions
-   tiny mask
-   huge mask
-   manual mask
-   automatic mask

Reject invalid masks before inference.

------------------------------------------------------------------------

# 35. Quality Regression

For every result verify:

``` text
width unchanged
height unchanged
aspect ratio unchanged
```

Also verify:

-   no unexpected crop
-   no unexpected resize
-   alpha behaviour is documented
-   unmasked pixels remain unchanged where the algorithm guarantees it
-   output decodes correctly

Maintain regression fixtures.

------------------------------------------------------------------------

# 36. Settings

Every visible setting must actually work.

Audit:

-   model
-   device
-   sensitivity
-   edge padding
-   brush size
-   export format
-   output policy
-   cache cleanup
-   theme
-   batch settings

If a setting does not work, remove/disable it rather than pretending.

------------------------------------------------------------------------

# 37. Theme

Test:

-   dark
-   light
-   browser refresh
-   every page
-   dialogs
-   errors
-   progress states
-   disabled states
-   hover states
-   focus states

No unreadable text or invisible controls.

------------------------------------------------------------------------

# 38. Accessibility

At minimum:

-   keyboard navigation
-   visible focus
-   usable button labels
-   tooltips where icons are ambiguous
-   sufficient contrast
-   no essential information conveyed only by color
-   useful error messages
-   reasonable screen-reader labels for controls

------------------------------------------------------------------------

# 39. Error Handling

Handle:

``` text
400
404
409
413
429
500
502
503
timeout
connection lost
model missing
model corrupted
GPU unavailable
GPU OOM
CPU fallback
invalid image
invalid mask
output failure
disk full
permission denied
port conflict
```

User-facing errors must be actionable.

Raw stack traces belong in diagnostics, not normal UI.

------------------------------------------------------------------------

# 40. Disk & Filesystem Safety

Handle:

-   disk full
-   permission denied
-   read-only folder
-   locked file
-   missing folder
-   deleted model
-   interrupted write
-   partial output

Write outputs atomically where practical:

``` text
temporary output
↓
validate
↓
rename
```

Never leave corrupted final files with a "completed" state.

------------------------------------------------------------------------

# 41. Temporary Files

Separate:

``` text
models/
cache/
temp/
outputs/
logs/
```

Cleanup must:

-   remove stale temporary data
-   never remove models
-   never remove user outputs
-   never remove active jobs
-   handle crashes safely

------------------------------------------------------------------------

# 42. Crash Recovery

If the application crashes during processing:

-   no corrupted final output should be marked complete
-   temporary files can be cleaned on next startup
-   completed outputs remain valid
-   model files remain valid
-   active jobs become recoverable/failed according to policy

------------------------------------------------------------------------

# 43. Logging

Use structured logs.

Every processing job should have:

``` text
timestamp
job_id
image_id
operation
model
model_version
device
input_dimensions
mask_dimensions
duration
output
status
error
```

Never log:

-   passwords
-   tokens
-   API keys
-   unnecessary personal data
-   raw image content

------------------------------------------------------------------------

# 44. Diagnostics

Provide a diagnostics screen/report containing:

-   app version
-   OS
-   architecture
-   Python/runtime version
-   backend status
-   frontend status
-   model status
-   model version
-   device
-   GPU
-   VRAM
-   CPU
-   RAM
-   storage availability
-   configuration summary
-   recent errors

Allow copying diagnostics.

------------------------------------------------------------------------

# 45. Health Checks

Backend:

``` text
GET /health
```

Readiness:

``` text
GET /ready
```

Model/runtime status:

``` text
GET /status
```

Health must distinguish:

``` text
process alive
```

from:

``` text
application ready to process images
```

------------------------------------------------------------------------

# 46. API Design

Document every endpoint.

For each:

-   method
-   path
-   request
-   response
-   validation
-   errors
-   timeout
-   authentication if applicable
-   idempotency behaviour
-   rate limits if applicable

Do not expose internal filesystem paths unnecessarily.

------------------------------------------------------------------------

# 47. Security

Treat uploaded images as untrusted input.

Validate:

-   file type
-   extension
-   MIME
-   decoded content
-   size
-   dimensions

Prevent:

-   path traversal
-   arbitrary file writes
-   command injection
-   unsafe subprocess invocation
-   malicious filenames
-   uncontrolled resource consumption

Never trust the client.

Backend revalidates everything.

------------------------------------------------------------------------

# 48. Dependency & Supply-Chain Security

Before release:

-   scan dependencies
-   pin critical versions
-   verify model checksums
-   verify downloaded artifacts
-   document licenses
-   track third-party notices
-   remove unused dependencies
-   review native binaries

Do not blindly load untrusted serialized model artifacts. PyTorch
documentation warns that some packaging/serialization mechanisms based
on pickle can execute code when loading untrusted/tampered data.

------------------------------------------------------------------------

# 49. Secrets

Never hard-code:

-   API keys
-   passwords
-   signing keys
-   private tokens

Use environment/configuration/secret stores appropriately.

For Docker Compose, distinguish ordinary configuration from secrets and
avoid passing sensitive values casually through environment variables.

------------------------------------------------------------------------

# 50. Docker Architecture

Docker is the final reproducible runtime, not a substitute for testing.

Recommended conceptual setup:

``` text
docker/
├─ backend.Dockerfile
├─ frontend.Dockerfile
├─ compose.yaml
└─ compose.production.yaml
```

Possible services:

``` text
frontend
backend
worker
```

Only create separate services when there is a real operational reason.

------------------------------------------------------------------------

# 51. Docker Image Rules

Production images should:

-   use pinned base images
-   use multi-stage builds where useful
-   run as non-root where feasible
-   contain only required runtime dependencies
-   exclude source development artifacts where unnecessary
-   exclude user outputs
-   exclude mutable caches
-   exclude secrets
-   define health checks
-   define resource expectations
-   log predictably

------------------------------------------------------------------------

# 52. Docker Model Strategy

Do not automatically bake huge mutable model weights into every image
unless that is deliberately required.

Choose one documented strategy:

### Strategy A --- Image-bundled model

Pros: - offline startup - deterministic model

Cons: - huge image - every model update rebuilds image

### Strategy B --- Persistent model volume

Pros: - model survives container recreation - smaller image - model can
be managed separately

Cons: - first-run initialization required

### Strategy C --- Installer-managed model cache

Useful for desktop distributions.

For this product, prefer a versioned model manager + persistent model
storage unless offline all-in-one distribution is a hard requirement.

------------------------------------------------------------------------

# 53. Docker Volumes

Persistent data should be separated:

``` text
models
outputs
config
logs
```

Do not store important user data only inside ephemeral containers.

------------------------------------------------------------------------

# 54. Docker Health

Compose should support:

-   health checks
-   restart policies where appropriate
-   production configuration
-   persistent volumes
-   controlled environment configuration

Development and production Compose configuration should not be
identical.

------------------------------------------------------------------------

# 55. Docker GPU

If GPU acceleration is supported in Docker:

-   verify NVIDIA Container Toolkit/runtime compatibility
-   verify GPU visibility inside container
-   verify framework sees CUDA
-   verify model loads
-   verify actual inference uses GPU

CPU mode must remain independently testable.

------------------------------------------------------------------------

# 56. Port Management

Do not assume:

``` text
3000
3003
7860
```

are always free.

At startup:

-   detect conflicts
-   provide clear error
-   allow configured ports
-   propagate actual backend URL to frontend
-   avoid hard-coded localhost dependencies

------------------------------------------------------------------------

# 57. Launcher

The end-user launcher should:

1.  validate installation
2.  validate runtime
3.  validate models
4.  detect hardware
5.  start backend
6.  wait for readiness
7.  start frontend/native shell
8.  open the UI
9.  monitor child processes
10. shut down cleanly

If backend fails:

-   frontend must show useful diagnostics
-   launcher must not report successful startup

------------------------------------------------------------------------

# 58. First-Run Model Setup

The ideal flow:

``` text
Install
↓
Launch
↓
Detect existing models
↓
Verify
↓
Missing model?
    ↓ YES
Download
↓
Verify checksum
↓
Load
↓
Warm-up
↓
Ready
```

If the user already has the correct model:

``` text
Detect
↓
Verify
↓
Reuse
```

No unnecessary download.

------------------------------------------------------------------------

# 59. Offline Mode

Define what works offline.

At minimum:

-   existing model
-   local image processing
-   local export
-   local batch

Network should not be required after all required local assets are
installed unless a feature explicitly depends on it.

------------------------------------------------------------------------

# 60. Update System

Document:

-   app updates
-   model updates
-   dependency updates
-   migration rules
-   rollback
-   failed update recovery

Never overwrite a working installation without a recovery strategy.

Model update:

``` text
download new
↓
verify
↓
load-test
↓
mark active
↓
retain old until safe
```

------------------------------------------------------------------------

# 61. Backward Compatibility

Test:

-   old configuration
-   old model cache
-   old output files
-   older job state where applicable

Version configuration schemas.

Do not silently interpret incompatible configuration.

------------------------------------------------------------------------

# 62. Testing Pyramid

## Unit

Test:

-   path resolver
-   coordinate mapping
-   masks
-   model discovery
-   device detection
-   file validation
-   output naming
-   configuration
-   export

## Integration

Test:

-   API → model
-   API → filesystem
-   batch → model
-   model → output
-   GPU/CPU selection

## E2E

Test real browser workflows.

## Packaging

Test the actual installed artifact.

------------------------------------------------------------------------

# 63. Real-World E2E Matrix

Run:

### Single manual

``` text
upload
→ paint
→ erase
→ process
→ result
→ compare
→ download
```

### Single automatic

``` text
upload
→ detect
→ review
→ process
→ result
→ download
```

### Batch

``` text
5 images
→ process
→ verify each
→ export
→ ZIP
```

### Failure

``` text
valid
corrupt
valid
unsupported
valid
```

Expected batch continuation.

### Restart

``` text
process
→ close
→ reopen
→ process again
```

### Existing model

``` text
pre-populated model
→ launch
→ detect
→ verify
→ no unnecessary download
```

### No GPU

``` text
disable/unavailable GPU
→ CPU
→ process
```

### GPU

``` text
GPU available
→ CUDA
→ process
```

### Low disk

``` text
simulate low storage
→ graceful error
```

------------------------------------------------------------------------

# 64. Performance Tests

Measure:

-   startup time
-   model discovery time
-   model load time
-   first inference
-   warm inference
-   batch average
-   peak RAM
-   peak VRAM
-   output encoding
-   export
-   ZIP creation

Separate:

``` text
cold start
```

from:

``` text
warm start
```

------------------------------------------------------------------------

# 65. Regression Test Dataset

Maintain a small deterministic dataset containing:

-   simple watermark
-   text watermark
-   corner watermark
-   center watermark
-   patterned watermark
-   multiple watermarks
-   transparent watermark
-   difficult background
-   small watermark
-   large watermark
-   portrait
-   landscape
-   PNG
-   JPEG
-   WEBP

Store expected properties, not copyrighted/user-sensitive assets
unnecessarily.

------------------------------------------------------------------------

# 66. Quality Metrics

For regression:

-   output exists
-   dimensions equal
-   format correct
-   mask applied
-   watermark region changed
-   unrelated region preserved where expected
-   no black/blank output
-   no severe artifacts
-   output opens successfully

Where meaningful, track image-quality metrics and human visual review.

------------------------------------------------------------------------

# 67. UI State Machine

Every async operation should have explicit states.

Example:

``` text
IDLE
→ LOADING
→ READY
→ PROCESSING
→ SUCCESS
→ ERROR
```

Never derive critical application state only from button text.

Disable conflicting operations while processing.

Prevent double-submit.

------------------------------------------------------------------------

# 68. Concurrency

Protect against:

-   double-click processing
-   two batch jobs competing for one GPU
-   model unloading during inference
-   concurrent model downloads
-   duplicate job submission
-   output filename collisions

Use locks/queues where appropriate.

------------------------------------------------------------------------

# 69. Browser Refresh

Refreshing the browser must not:

-   kill backend jobs
-   corrupt outputs
-   reset persistent model state
-   create duplicate jobs

The frontend should recover the latest job state when possible.

------------------------------------------------------------------------

# 70. Long-Running Jobs

For batch:

-   backend owns job
-   frontend polls/subscribes
-   progress is persisted
-   job ID is stable
-   reconnect is supported
-   final state remains queryable

Do not keep critical job state only in React state.

------------------------------------------------------------------------

# 71. UX Completion Rules

Every action needs:

-   visible feedback
-   disabled state when unavailable
-   success state
-   failure state
-   retry path where appropriate

No:

``` text
click
→ nothing happens
```

No invisible processing.

------------------------------------------------------------------------

# 72. Empty States

Design/test:

-   no image
-   no mask
-   no candidate
-   no batch
-   no model
-   no output
-   no history
-   no errors

Every empty state must explain the next action.

------------------------------------------------------------------------

# 73. Loading States

Show:

-   what is loading
-   progress if measurable
-   indeterminate state if not measurable
-   cancel if safe
-   error if timeout/failure

Never fake progress.

------------------------------------------------------------------------

# 74. About / Credits / Licenses

Include:

-   application version
-   processing engine
-   model
-   framework
-   licenses
-   third-party acknowledgements
-   source links
-   local-first/privacy statement only if technically true

Do not claim "local-only" if any feature uploads data.

------------------------------------------------------------------------

# 75. Privacy

Document:

-   whether images leave the machine
-   whether telemetry exists
-   what logs contain
-   where outputs are stored
-   model download behaviour
-   update behaviour

If local-first:

verify it technically.

------------------------------------------------------------------------

# 76. Documentation

Required:

``` text
README.md
INSTALLATION.md
USER_GUIDE.md
ARCHITECTURE.md
MODEL_GUIDE.md
TROUBLESHOOTING.md
SECURITY.md
PRIVACY.md
CHANGELOG.md
RELEASE.md
```

Also maintain:

``` text
docs/PHASE_8_MASTER_CHECKLIST.md
docs/PHASE_8_FUNCTIONAL_COMPLETION_REPORT.md
```

------------------------------------------------------------------------

# 77. Troubleshooting Guide

Document fixes for:

-   backend not starting
-   frontend not starting
-   port conflict
-   model missing
-   model corrupted
-   CUDA unavailable
-   CPU fallback
-   GPU OOM
-   slow batch
-   permission denied
-   disk full
-   image unsupported
-   output missing
-   Docker not starting
-   container unhealthy
-   browser cannot connect
-   stale process
-   incomplete download

------------------------------------------------------------------------

# 78. Release Build

Before release:

``` text
clean repository
↓
clean dependency install
↓
tests
↓
lint
↓
type checks
↓
production build
↓
package
↓
install on clean machine
↓
run E2E
↓
verify outputs
↓
verify uninstall
↓
verify reinstall
```

Never release directly from the developer environment.

------------------------------------------------------------------------

# 79. Clean-Machine Test

Use a machine/environment that has:

-   no project Python packages
-   no project Node packages
-   no project model cache
-   no developer source paths
-   no developer environment variables

Install only the released artifact.

The application must work.

------------------------------------------------------------------------

# 80. Upgrade Test

Test:

``` text
Version N
→ install N+1
→ preserve models
→ preserve user outputs
→ migrate config
→ launch
→ process image
```

------------------------------------------------------------------------

# 81. Uninstall Test

Uninstall must clearly define whether it removes:

-   application binaries
-   models
-   cache
-   user outputs
-   configuration
-   logs

Never silently delete valuable user outputs.

------------------------------------------------------------------------

# 82. Security Release Checklist

Before shipping:

-   [ ] no secrets in repository
-   [ ] no developer paths
-   [ ] no unsafe subprocess input
-   [ ] upload validation
-   [ ] path traversal prevention
-   [ ] resource limits
-   [ ] dependency audit
-   [ ] model checksum validation
-   [ ] safe model loading
-   [ ] logs sanitized
-   [ ] debug mode disabled
-   [ ] production errors sanitized
-   [ ] container permissions reviewed

------------------------------------------------------------------------

# 83. Production Observability

Track, where appropriate:

-   startup success/failure
-   model load failure
-   inference failure
-   batch failure
-   device fallback
-   export failure
-   disk errors
-   crash reports if enabled

Do not collect personal/image content unnecessarily.

------------------------------------------------------------------------

# 84. Release Artifacts

A release should produce:

``` text
Windows installer
Windows portable build if desired
Docker image
Docker Compose deployment
checksums
release notes
documentation
license notices
```

If supporting macOS/Linux:

build and test those artifacts independently.

------------------------------------------------------------------------

# 85. Reproducibility

Record:

-   Git commit/tag
-   frontend lockfile
-   Python dependency lock/pins
-   base image digest where practical
-   model versions
-   model checksums
-   build timestamp
-   build environment
-   package version

A release must be identifiable.

------------------------------------------------------------------------

# 86. Supply-Chain Reproducibility

For every model:

``` text
model ID
version
source
checksum
license
```

For every release:

``` text
application version
Git commit
dependency versions
model versions
container image digest
```

------------------------------------------------------------------------

# 87. Final Production Acceptance Matrix

Mark each:

``` text
[ ] VERIFIED
[ ] IMPLEMENTED / NOT VERIFIED
[ ] BROKEN
[ ] NOT APPLICABLE
```

### Runtime

-   [ ] clean install
-   [ ] clean start
-   [ ] clean restart
-   [ ] clean shutdown
-   [ ] no developer dependencies

### Models

-   [ ] discovery
-   [ ] validation
-   [ ] reuse
-   [ ] download
-   [ ] checksum
-   [ ] load
-   [ ] GPU
-   [ ] CPU
-   [ ] fallback

### Single

-   [ ] upload
-   [ ] paint
-   [ ] erase mask
-   [ ] pan
-   [ ] zoom
-   [ ] detection
-   [ ] mask
-   [ ] inference
-   [ ] actual result
-   [ ] comparison
-   [ ] slider
-   [ ] export
-   [ ] download

### Batch

-   [ ] multi-upload
-   [ ] queue
-   [ ] background execution
-   [ ] model reuse
-   [ ] progress
-   [ ] cancellation
-   [ ] retry
-   [ ] failure isolation
-   [ ] statistics
-   [ ] individual export
-   [ ] ZIP
-   [ ] format selection

### Packaging

-   [ ] desktop installer
-   [ ] portable build if applicable
-   [ ] Docker
-   [ ] Compose
-   [ ] GPU container
-   [ ] CPU container
-   [ ] health check
-   [ ] persistent volumes
-   [ ] clean machine test

### Reliability

-   [ ] crash recovery
-   [ ] disk-full handling
-   [ ] permission handling
-   [ ] invalid image handling
-   [ ] corrupt model handling
-   [ ] port conflict
-   [ ] network failure where applicable

### Security

-   [ ] upload validation
-   [ ] path safety
-   [ ] dependency audit
-   [ ] model integrity
-   [ ] secrets audit
-   [ ] safe serialization/model loading
-   [ ] sanitized logs

### Documentation

-   [ ] README
-   [ ] install guide
-   [ ] user guide
-   [ ] architecture
-   [ ] model guide
-   [ ] troubleshooting
-   [ ] security
-   [ ] privacy
-   [ ] changelog
-   [ ] release notes

------------------------------------------------------------------------

# 88. Final Release Gate

The application is **NOT production-ready** if any of these fail:

1.  Single manual processing
2.  Single automatic processing
3.  Batch processing
4.  Actual output generation
5.  Download/export
6.  Model discovery/loading
7.  GPU execution where supported
8.  CPU fallback
9.  Clean installation
10. Clean restart
11. Error recovery
12. Security validation
13. Clean-machine test
14. Packaging test

------------------------------------------------------------------------

# 89. Final Engineering Rule

Do not add more features while a core workflow is broken.

Priority order:

``` text
Correctness
↓
Reliability
↓
Data safety
↓
Performance
↓
Packaging
↓
UX polish
↓
New features
```

A beautiful UI around a broken inference engine is still a broken
product.

------------------------------------------------------------------------

# 90. Release Sign-Off

Before declaring the product complete, the team must produce:

``` text
PHASE_8_MASTER_CHECKLIST.md
PHASE_8_FUNCTIONAL_COMPLETION_REPORT.md
CHANGELOG.md
RELEASE_NOTES.md
```

The completion report must include actual evidence:

-   commands executed
-   tests passed
-   E2E workflows passed
-   package installed on a clean machine
-   model discovery result
-   GPU result
-   CPU result
-   batch benchmark
-   export verification
-   Docker verification
-   known limitations

Do not use statements such as:

> "Implemented."

Use:

> "Implemented and verified with X test on Y environment; result Z."

------------------------------------------------------------------------

# 91. Recommended Final Delivery Architecture

For the final product, aim for:

``` text
                         ┌───────────────────┐
                         │   Desktop Shell   │
                         │  (optional Tauri) │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │    Web UI         │
                         │     Next.js       │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   Backend/API     │
                         │     FastAPI       │
                         └─────────┬─────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
          ┌───────▼──────┐ ┌──────▼───────┐ ┌─────▼──────┐
          │ Model Manager│ │ Device Mgr   │ │ Batch Job  │
          └───────┬──────┘ └──────┬───────┘ └─────┬──────┘
                  │                │               │
                  └────────────────┼───────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Image Processing  │
                         │ / Inpainting      │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Models / Runtime  │
                         │ CUDA or CPU       │
                         └───────────────────┘
```

Packaging layer:

``` text
Desktop Installer
       │
       ├── packaged runtime
       ├── frontend
       ├── backend
       ├── native dependencies
       └── model manager
               │
               └── user model store
```

Docker layer:

``` text
Docker Image
    │
    ├── frontend
    ├── backend
    ├── worker/runtime
    └── required runtime libraries
          │
          ├── model volume
          ├── output volume
          ├── config volume
          └── log volume
```

------------------------------------------------------------------------

# 92. Important Packaging Principle

Do not make the mistake of thinking:

> "Docker + venv + model files = automatically production-ready."

They solve different problems.

-   **venv** isolates Python development/runtime dependencies.
-   **Docker** isolates and reproduces a containerized runtime.
-   **desktop bundling/installer** gives normal users an installable
    application.
-   **model manager** handles large AI artifacts.
-   **persistent user-data storage** protects models/config/outputs.
-   **CI/CD** verifies that the released artifact actually works.

A production product may use all of them without making them
interchangeable.

------------------------------------------------------------------------

# 93. Final "Nothing Left" Audit

Before release, ask these questions:

### Can a completely new user install it without opening CMD?

### Can a user with Python already installed use it without dependency conflicts?

### Can a user with CUDA already installed use it without the application depending on their Python environment?

### Can a CPU-only machine run it?

### Can a supported NVIDIA machine run it?

### If the model already exists, does the application detect and reuse it?

### If the model is missing, does the application download and verify it?

### If download is interrupted, can it recover?

### If the model is corrupted, can it repair it?

### If the GPU runs out of VRAM, does the application fail gracefully?

### If one batch image is corrupt, do the remaining images continue?

### If the browser refreshes, does the batch survive?

### If the application crashes, are outputs safe?

### If the disk becomes full, does the user receive a useful error?

### Can every completed result actually be downloaded?

### Can batch results be exported individually and as ZIP?

### Does the output directory behave predictably?

### Does the application work on a clean machine?

### Does Docker work from a clean checkout?

### Does the packaged desktop application work without developer tooling?

### Can the application be upgraded without destroying models or outputs?

### Can the application be uninstalled without unexpectedly destroying user data?

### Can another developer reproduce the release?

### Can the team prove every core feature with evidence?

If any answer is **No**, the product is not finished.

------------------------------------------------------------------------

# 94. Sources / Standards Used for This Checklist

This document incorporates current official documentation and
established production practices, including:

-   Python `venv` documentation --- isolated Python environments,
    disposable/recreatable environments, and platform-specific
    environment creation.
-   Docker documentation --- production Compose configuration,
    environment handling, health/restart considerations, and
    containerized Python applications.
-   PyInstaller documentation --- Python application bundling,
    one-folder/one-file modes, data/binary inclusion, spec files,
    runtime paths, and platform-specific builds.
-   PyTorch documentation --- model packaging/serialization security
    considerations.

Official references:

-   Python venv: https://docs.python.org/3/library/venv.html
-   Docker Compose production:
    https://docs.docker.com/compose/how-tos/production/
-   Docker Compose environment variables:
    https://docs.docker.com/compose/how-tos/environment-variables/best-practices/
-   Docker Python guide: https://docs.docker.com/guides/python/
-   PyInstaller manual: https://pyinstaller.org/en/stable/
-   PyInstaller spec files:
    https://pyinstaller.org/en/stable/spec-files.html
-   PyInstaller runtime information:
    https://pyinstaller.org/en/stable/runtime-information.html
-   PyTorch package documentation:
    https://docs.pytorch.org/docs/main/package.html

------------------------------------------------------------------------

## Final Rule

**Do not stop at "the software runs on my machine."**

The release target is:

> **A clean machine can install it, start it, obtain/verify the required
> runtime and models, process real images on supported hardware, recover
> from expected failures, export real results, restart safely, and
> reproduce the same behaviour from the released artifact.**

That is the production-grade bar.
