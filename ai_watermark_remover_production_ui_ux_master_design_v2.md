# AI Watermark Remover --- Production UI/UX Master Design Specification

**Product:** Local-first AI Watermark Remover / Image Processing
Application\
**Target:** Desktop-first, production-grade, 2026-ready creative
software\
**Companion source of truth:**
`production_grade_software_master_checklist.md`\
**Purpose:** Define the visual system, information architecture,
interaction model, screen/state inventory, accessibility, performance
UX, and production UI acceptance criteria.

------------------------------------------------------------------------

## 0. Relationship to the Engineering Master Checklist

This document is the UI/UX companion to the production engineering
checklist. They must be implemented together.

The engineering checklist defines the product's production contract:
**Install → Start → Detect environment → Discover models → Load models →
Process real input → Produce real output → Save/download → Restart →
Work again.** It explicitly rejects fake success states, placeholder
controls, hard-coded paths, fragile developer-machine dependencies, and
incomplete recovery behavior.

This document defines the experience around that contract:

**Understand → Act → See system state → Verify result → Export →
Recover.**

A UI feature is not complete because it looks polished. It is complete
only when the real backend behavior, state, error path, export path, and
recovery path are represented correctly.

If a backend capability does not exist, the UI must not pretend it
exists.

------------------------------------------------------------------------

# 1. Product Design Direction

## 1.1 Product personality

The application should feel like professional creative software, not a
generic AI SaaS dashboard.

Desired qualities:

-   precise
-   fast
-   calm
-   technical
-   premium
-   trustworthy
-   image-first
-   locally controlled
-   efficient for repeated workflows

Avoid:

-   gaming/cyberpunk styling
-   excessive neon
-   excessive gradients
-   glassmorphism everywhere
-   giant dashboard cards
-   fake AI animations
-   decorative analytics with no product value
-   excessive rounded pills
-   cluttered settings

The interface should be visually sophisticated because of **hierarchy,
spacing, typography, composition, and interaction quality**, not because
every component glows.

## 1.2 Core design principles

Use these as hard rules:

### Purpose

Every surface has a clear job.

### Agency

Users can undo, cancel, retry, inspect, and recover.

### Familiarity

Use established patterns for file upload, image editing, sidebars, tabs,
previews, export, settings, and dialogs.

### Simplicity

Keep the primary workflow simple while exposing advanced controls
progressively.

### Hierarchy

Users should immediately know: 1. Where they are. 2. What object they
are working on. 3. What they can do. 4. What the system is doing. 5.
What happened. 6. What they should do next.

### Feedback

Every meaningful action receives visible feedback.

### Trust

Never claim completion until a real, validated result exists.

### Craft

Typography, spacing, icon alignment, focus states, hover states,
disabled states, copy, transitions, and error handling are all product
quality.

------------------------------------------------------------------------

# 2. Research-Informed Patterns

The specification is informed by current patterns from professional
creative software and mature design systems.

### Adobe Photoshop

Use the concept of a professional workspace composed of
application/navigation, tools, contextual options, panels,
document/canvas, and notifications. Contextual task actions should
appear near the current task where they reduce navigation.

### Topaz Photo

Treat export as a real workflow with filename, format, destination,
queue state, and output visibility. Do not hide where processed files
are going.

### PhotoRoom

Batch editing should be a dedicated high-throughput workspace with
images in a grid/list and controls that can apply to all or selected
items.

### Apple HIG

Use hierarchy, agency, familiarity, flexibility, simplicity, craft,
clear feedback, and recovery from mistakes.

### Microsoft Fluent

Use predictable hierarchy, concise labels, keyboard/focus support,
accessible contrast, and responsive navigation.

### shadcn/ui

Use a composable application sidebar with header, grouped navigation,
scrollable content, footer, collapse-to-icon behavior, and accessible
focus/tooltip behavior.

### Vercel Geist

Use restrained typography, systematic spacing, high-contrast surfaces,
subtle borders, and a small controlled color system.

### Stripe

Use reusable components, focus views for important workflows, settings
views, badges for state, menus for contextual actions, and consistent
component patterns.

### WCAG 2.2

Keyboard focus must remain visible and must not be hidden by application
chrome. Contrast and non-color status communication are mandatory.

------------------------------------------------------------------------

# 3. Global Visual System

## 3.1 Theme

Dark-first, with a complete light theme and system theme.

Dark mode: - near-black application background - slightly raised
charcoal surfaces - subtle 1px borders - high-contrast primary text -
muted secondary text - one strong brand/action accent

Light mode: - neutral background - white/near-white surfaces - dark
text - same geometry and spacing - same semantic status colors

Dark and light modes must be the same design system, not two separately
hacked themes.

## 3.2 Accent

Orange can remain the primary product accent because it is already
present in the current application.

Use accent for: - primary CTA - active navigation - selected tool -
progress emphasis - important focus state - selected controls

Do not make every icon, border, and heading orange.

## 3.3 Color roles

Define tokens for: - background - surface - elevated surface - border -
text - muted text - accent - success - warning - error - info - mask
overlay

Never use a color only because it looks good. Every color has a semantic
role.

## 3.4 Typography

Use one high-legibility modern sans-serif family.

Suggested hierarchy: - page title: 24--28px - section title: 16--18px -
body: 14px - secondary: 13px - caption: 12px

Keep the type scale small and systematic. Numeric information such as
image dimensions, file sizes, processing times, and confidence should
have consistent numeric styling.

## 3.5 Spacing

Use a tokenized scale such as:

`4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64`

Avoid arbitrary one-off spacing unless optical correction is genuinely
required.

## 3.6 Radius and elevation

Recommended starting point: - controls: 6px - cards/panels: 8--12px -
dialogs: 12--16px - large surfaces: 16--20px

Use subtle borders and restrained shadows. Avoid floating every element.

------------------------------------------------------------------------

# 4. Application Shell

Desktop layout:

``` text
┌────────────────────────────────────────────────────────────────────┐
│ App / Workspace Header                                             │
├───────────────┬────────────────────────────────────────────────────┤
│               │                                                    │
│ LEFT SIDEBAR  │                 MAIN WORKSPACE                     │
│               │                                                    │
│ navigation    │                                                    │
│ + contextual  │                                                    │
│ controls      │                                                    │
│               │                                                    │
└───────────────┴────────────────────────────────────────────────────┘
```

The main workspace must receive most of the screen. The image/canvas is
the dominant object in editor mode.

## 4.1 Sidebar

Target expanded width: approximately 240--280px.\
Collapsed width: approximately 56--72px.\
Make the width a design token.

Recommended navigation:

``` text
BRAND
AI Watermark Remover

WORKSPACE
  Editor
  Batch

LIBRARY
  History
  Exports

SYSTEM
  Models
  Settings
  Diagnostics
  About
```

The exact final labels may change, but the hierarchy should remain.

Sidebar must support: - expanded state - collapsed icon state -
tooltips - keyboard focus - clear active state - predictable scroll
behavior

Do not use icons alone without accessible names.

## 4.2 Header

Keep it compact:

``` text
Editor                                      ● Ready   CUDA • RTX 3050
```

During processing:

``` text
Editor                              ◌ Processing 4/9   CUDA • RTX 3050
```

The header should communicate state, not become another dashboard.

------------------------------------------------------------------------

# 5. Global State Vocabulary

Use one consistent vocabulary everywhere:

-   Ready
-   Loading
-   Preparing
-   Processing
-   Validating
-   Completed
-   Needs review
-   Cancelled
-   Failed
-   Offline
-   Model unavailable
-   GPU unavailable

Do not randomly alternate between "Done", "Finished", "Complete",
"Success", and "Ready".

------------------------------------------------------------------------

# 6. Single Editor

## 6.1 Core workflow

``` text
Load image
  ↓
Detect / scan
  ↓
Paint or select watermark
  ↓
Review mask
  ↓
Run removal
  ↓
Processing
  ↓
Validate result
  ↓
Compare
  ↓
Export
```

Do not force experienced users through a rigid wizard. The workflow
should be obvious without locking navigation.

## 6.2 Editor structure

Use a professional three-zone model when useful:

``` text
┌──────────────┬───────────────────────────┬──────────────────────┐
│ TOOLS /      │                           │ CONTEXT /            │
│ CONTROLS     │          CANVAS           │ RESULT / DETAILS     │
└──────────────┴───────────────────────────┴──────────────────────┘
```

The right contextual panel should collapse when unnecessary. Never
sacrifice canvas size merely to keep a panel visible.

## 6.3 Left context panel

### Source

``` text
SOURCE IMAGE
filename.jpg
1792 × 2400
2.4 MB

[Replace] [Start over]
```

### Tools

``` text
TOOLS
[Pan] [Paint] [Erase]

Brush size
──────●────── 24 px
```

### Detection

``` text
DETECTION
Sensitivity
──────●────── 160

Edge padding
────●──────── 12 px

☑ Skip low-confidence scans

[Scan candidate areas]
```

Primary action at the bottom:

`[ Run Neural Inpainting ]`

Make it sticky inside the control panel where appropriate.

------------------------------------------------------------------------

# 7. Paint and Erase

## Paint

Paint is the manual watermark-marking tool.

Requirements: - visible brush cursor - translucent mask overlay -
accurate canvas coordinate mapping - correct behavior under zoom/pan -
pointer down/drag/up support - immediate mask feedback - undo/redo -
optional mask-only view

The mask must be visible but should not completely hide the underlying
watermark.

## Erase

Erase means **remove pixels from the current mask**. It must not modify
the source image.

The eraser cursor must be a clearly visible circle representing brush
diameter, not an ambiguous generic cursor.

When no mask exists, show:

> Nothing to erase yet. Paint the area you want to remove first.

When erasing: - remove mask pixels immediately - never change source
pixels - support drag strokes - support undo/redo

------------------------------------------------------------------------

# 8. Canvas

The canvas is the most important object in the editor.

Controls:

``` text
[-] 100% [+] [Fit] [Fullscreen]
```

Recommended shortcuts: - `+` zoom in - `-` zoom out - `0` fit - `1`
100% - `Space` temporary pan - `B` paint - `E` erase - `P` pan - `Esc`
exit active mode

Canvas interactions must not be confused with browser page scrolling.

The image must remain correctly aligned when: - browser zoom changes -
window resizes - image aspect ratio changes - zoom changes - panels
open/close

------------------------------------------------------------------------

# 9. Contextual Actions

Use contextual action bars to keep common actions near the task.

After load:

``` text
Image loaded
[Scan candidates] [Paint] [Run removal]
```

After result:

``` text
Result ready
[Compare] [Download] [Export]
```

This follows professional creative-software patterns without cluttering
the main navigation.

------------------------------------------------------------------------

# 10. Processing and Validation

Never show a generic spinner with no useful state.

Preferred:

``` text
PROCESSING
Removing watermark...
Step 2 of 3

Preparing mask
████████░░ 72%

CUDA • RTX 3050
```

If ETA cannot be measured reliably, do not invent it.

Use actual backend phases where possible: - Preparing - Loading model -
Detecting - Inpainting - Encoding - Validating

## Result validation gate

The UI must not show "Completed" until: 1. output file exists 2. output
is readable 3. format/MIME is valid 4. dimensions are valid 5. result
URL is reachable 6. result preview loads

Then show:

`RESULT READY`

Otherwise:

``` text
RESULT UNAVAILABLE
The processed file could not be validated.
[Retry] [View diagnostics]
```

This directly aligns with the engineering checklist's no-fake-success
rule.

------------------------------------------------------------------------

# 11. Result and Comparison Workspace

Use:

``` text
[Original] [Split] [Slider] [Result]
```

### Original

Full source image.

### Result

Full processed image.

### Split

``` text
┌─────────────────────┬─────────────────────┐
│ ORIGINAL            │ RESULT              │
└─────────────────────┴─────────────────────┘
```

### Before/after slider

A visible draggable divider should compare aligned original/result
images.

Requirements: - clear handle - correct image alignment - smooth drag -
resize-safe - keyboard-accessible where practical

The result panel must never show a broken-image state as the final
success state.

------------------------------------------------------------------------

# 12. Export UX

Export is a first-class product workflow.

Single result:

`[ Download Result ]`

Advanced export:

``` text
EXPORT

Format
[Same as source ▾]

Quality
[100%]

Filename
[original_removed]

Location
[Choose folder]

[Export]
```

Supported: - Same as source - PNG - JPG/JPEG - WEBP

Changing an extension is not conversion. The backend must encode the
actual requested format.

After export:

``` text
Saved to:
D:\Pictures\AI Watermark Remover\processed\image.png

[Open folder]
```

------------------------------------------------------------------------

# 13. Batch Workspace

Batch is a separate high-throughput workflow, not a single-editor screen
with 100 rows.

Recommended layout:

``` text
┌───────────────┬───────────────────────────────────────────────────┐
│ BATCH         │ Queue                                             │
│ CONTROLS      │                                                   │
│               │ [Select all] [Select none]                       │
│ Add images    │                                                   │
│ Reference     │ □ image1.jpg  Completed  Preview  Download       │
│ Detection     │ □ image2.jpg  Processing                         │
│ Export        │ □ image3.jpg  Needs review  Preview              │
│ Performance   │                                                   │
│               │                                                   │
│ [Start batch] │                                                   │
└───────────────┴───────────────────────────────────────────────────┘
```

## 13.1 Queue row

Each item should show: - checkbox - thumbnail - filename - dimensions
where useful - status - confidence where useful - processing time -
error/review state - Preview - Download

Do not make important actions microscopic icon-only controls.

## 13.2 Batch summary

``` text
9 images

8 Completed
1 Needs review
0 Failed

12.8s avg
```

During processing:

``` text
Processing 4 / 9
██████████░░░░░ 44%

[Cancel batch]
```

## 13.3 Selection

Always expose: - Select all - Select none - selected count

When selected:

``` text
3 selected
[Download selected] [ZIP selected]
```

## 13.4 Batch export

``` text
EXPORT
Format [PNG ▾]
Filename [{original}_removed]
Destination [Choose folder]

[Download all] [ZIP all]
```

ZIP must contain real validated output images, not temporary files,
masks, HTML, JSON, or originals unless explicitly requested.

------------------------------------------------------------------------

# 14. Batch Preview

Preview must be a focused workspace/modal that does not destroy the
user's batch context.

``` text
PREVIEW 1 / 9

[Original] [Split] [Slider] [Result]

                         [Download this]

< previous                              next >

[thumbnail] [thumbnail] [thumbnail]
```

Use thumbnails for navigation. Load full-resolution images only for the
active preview.

------------------------------------------------------------------------

# 15. Batch Performance UX

For large batches:

``` text
Processing
24 / 100

Completed 22
Processing 2
Review 0
Failed 0

Average 1.8s/image
```

If the backend exposes reliable information:

``` text
Workers: 2
GPU memory: 3.1 / 4.0 GB
```

Never display fake progress or fake ETA.

For 100--500+ images, use virtualization/lazy loading and avoid keeping
hundreds of full-resolution images in browser memory.

------------------------------------------------------------------------

# 16. Reference Mode

Reference mode should be an advanced workflow for repeated watermark
placement.

``` text
REFERENCE MODE

1. Choose reference image
2. Mark watermark
3. Configure tolerance
4. Test on sample images
5. Apply to batch

[ Test reference ]
[ Apply to batch ]
```

Possible tolerances: - position - scale - rotation

Never promise perfect matching across geometrically different images.
Low-confidence matches must become `Needs review` instead of fake
success.

------------------------------------------------------------------------

# 17. Low-Confidence UX

Use:

``` text
NEEDS REVIEW

Watermark confidence: 0.41

The system could not confidently identify the watermark.

[Preview]
[Mark manually]
[Retry with reference]
[Skip]
```

Batch summary should explicitly separate: - Completed - Needs review -
Failed - Cancelled

------------------------------------------------------------------------

# 18. History

History is a real workspace, not a decorative list.

``` text
[thumbnail] image.jpg
Processed 12 minutes ago
PNG • 1792 × 2400 • 1.8 MB

[Open] [Download] [Delete]
```

Filters: - All - Completed - Needs review - Failed

Optional search by filename/date/format/batch.

Never expose raw internal filesystem paths in normal UI.

------------------------------------------------------------------------

# 19. Model Manager

The model manager must communicate real runtime state.

``` text
MODELS

LaMa Inpainting
Installed • v1.0.0
196 MB

Load: 1.2s
Inference: 12.9s
VRAM: 196 MB

[Details] [Verify] [Remove]
```

Missing:

``` text
Not installed
196 MB download
[Download model]
```

Downloading:

``` text
Downloading
████████░░ 78%
153 / 196 MB
```

Corrupt:

``` text
Model verification failed.
[Repair model]
```

Never show `Ready` unless the model is actually usable.

------------------------------------------------------------------------

# 20. Hardware / Runtime Surface

Keep hardware information visible but compact.

``` text
CUDA
RTX 3050
4 GB VRAM
Ready
```

Detailed view:

``` text
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
Backend: CUDA
VRAM: 4 GB
Fallback: CPU
```

If CUDA is unavailable:

``` text
CUDA unavailable
CPU fallback active
[View diagnostics]
```

------------------------------------------------------------------------

# 21. Settings Architecture

Group settings instead of creating a wall of toggles.

``` text
General
Processing
Models
Export
Appearance
AI Fallback
Performance
Privacy
Storage
Advanced
```

### General

-   language
-   startup behavior
-   confirmations
-   reset preferences

### Processing

-   sensitivity
-   edge padding
-   low-confidence behavior
-   default model
-   concurrency

### Export

-   default format
-   quality
-   filename pattern
-   output folder
-   overwrite behavior

### Appearance

-   Dark
-   Light
-   System
-   density where justified
-   reduced motion

### Storage

-   output directory
-   temporary directory
-   cache size
-   clear cache

------------------------------------------------------------------------

# 22. External AI / BYOK UX

External AI is optional fallback, not the core local workflow.

``` text
AI FALLBACK

Local processing
● Preferred

External fallback
○ Disabled

Provider
[OmniRoute ▾]

API key
Configured
[Replace] [Remove]

[Test connection]
```

Never expose actual keys in the UI.

Do not claim "100% local" when an external provider is enabled.

Use explicit language:

> Some images may be sent to the configured external provider when local
> processing requires fallback.

------------------------------------------------------------------------

# 23. Onboarding

Keep onboarding short.

### Step 1

``` text
Welcome to AI Watermark Remover
Remove watermarks locally with AI.
[Get started]
```

### Step 2

``` text
Checking your system...
✓ Runtime
✓ GPU detected
✓ CUDA available
✓ Model available
```

### Step 3

``` text
Recommended model
LaMa • 196 MB
[Install model]
```

### Step 4

``` text
You're ready.
[Open editor]
```

Allow skipping safe optional steps.

------------------------------------------------------------------------

# 24. About and Diagnostics

## About

Include: - product name - version - engine - model - hardware -
licenses - open-source components - documentation - source repository -
privacy statement - update check

## Diagnostics

Show: - app version/build - frontend/backend status - Python/runtime
status - GPU/CUDA status - RAM/VRAM - model state - storage/free disk -
worker status - safe logs

Actions:
`[Copy diagnostics] [Open logs] [Run health check] [Clear temporary cache]`

Never expose API secrets or raw sensitive configuration.

------------------------------------------------------------------------

# 25. Empty, Loading, Error, and Recovery States

Every important screen needs all meaningful states.

## Empty editor

``` text
Your workspace is empty
Drop an image here to start.
[Choose image]
PNG, JPG, WEBP
```

## Empty batch

``` text
No images in the queue
[Add images]
```

## Empty history

``` text
No processed images yet
Your completed results will appear here.
```

## Model missing

``` text
No models installed
[Install model]
```

## Error

Always explain: 1. what happened 2. why it matters 3. what the user can
do

Bad: `Error 500`

Good:
`The inpainting model ran out of GPU memory. Retry using CPU fallback or reduce processing load.`

------------------------------------------------------------------------

# 26. Destructive Actions

Use explicit confirmation for: - delete history - remove model - clear
cache - cancel active batch when work may be lost

Example:

``` text
Remove model?
This deletes the local model files. Processed images are not affected.
[Cancel] [Remove model]
```

------------------------------------------------------------------------

# 27. Undo / Recovery

Where technically supported: - undo mask stroke - redo mask stroke -
reset mask - retry processing - restart failed batch item - retry failed
batch - cancel batch

Recommended shortcuts: - Ctrl/Cmd + Z - Ctrl/Cmd + Shift + Z

------------------------------------------------------------------------

# 28. Keyboard and Command Palette

Recommended shortcuts:

``` text
Ctrl/Cmd + O       Open image
Ctrl/Cmd + S       Export
Ctrl/Cmd + Z       Undo
Ctrl/Cmd + Shift+Z Redo
Space              Temporary pan
B                  Paint
E                  Erase
P                  Pan
+                  Zoom in
-                  Zoom out
0                  Fit
1                  100%
Esc                Close/cancel
Ctrl/Cmd + ,       Settings
Ctrl/Cmd + K       Command palette
```

Command palette:

``` text
Search commands...
Open image
Start batch
Run inpainting
Export result
Download selected
Open settings
Manage models
Clear mask
Reset workspace
Toggle theme
Show shortcuts
```

As the product grows, this becomes a major productivity feature for
power users.

------------------------------------------------------------------------

# 29. Accessibility

Minimum production requirements:

-   keyboard navigation
-   visible focus
-   semantic buttons
-   accessible labels
-   tooltips for unfamiliar icon-only controls
-   sufficient contrast
-   status not communicated by color alone
-   logical focus order
-   modal focus trapping
-   Escape closes temporary surfaces
-   reduced-motion support
-   screen-reader labels

When opening a dialog/preview/drawer, move focus into it and return
focus to the initiating control on close.

Focus must never be hidden behind sticky bars or overlays.

------------------------------------------------------------------------

# 30. Icons

Use one icon family consistently, such as Lucide if already used.

Rules: - consistent stroke weight - consistent optical size - consistent
padding - no random mixed icon libraries - icon-only buttons require
accessible labels and tooltips - destructive actions use semantic
warning/error icons - never use emoji as functional UI icons

------------------------------------------------------------------------

# 31. Motion

Motion should explain state, not decorate the interface.

Good: - sidebar collapse - dialog opening - preview transitions -
progress changes - result transitions - hover/focus feedback

Avoid: - permanent animated backgrounds - pulsing everywhere -
parallax - animated cards with no purpose

Honor `prefers-reduced-motion`.

------------------------------------------------------------------------

# 32. Responsive / Window Behavior

Desktop is the primary target.

At wide desktop widths: - full sidebar - canvas - optional context panel

At smaller desktop/tablet widths: - collapsible sidebar - contextual
panel becomes drawer - canvas remains primary

At narrow widths: - sidebar becomes overlay - secondary actions move
into menus - batch rows can become cards

Test at: - 1280×720 - 1366×768 - 1440×900 - 1920×1080 - 2560×1440 - 125%
Windows scaling - 150% Windows scaling

The application must survive browser zoom and window resizing without
clipping or overlapping controls.

------------------------------------------------------------------------

# 33. Drag and Drop

Support: - one image - multiple images - folder drop where supported

Idle: `Drop images to add them`

Drag-over: `Release to add 12 images`

Validate files before processing.

------------------------------------------------------------------------

# 34. File Validation UX

For unsupported input:

``` text
Unsupported file
logo.psd cannot be processed.
Supported: PNG, JPG, JPEG, WEBP
[Choose another image]
```

For oversized input:

``` text
Image is too large
Maximum supported size: 50 MB
[Choose another image]
```

If automatic optimization exists, clearly explain its effect.

------------------------------------------------------------------------

# 35. Storage and Output UX

Users must always know where files are saved.

Settings:

``` text
OUTPUT
Folder
D:\Pictures\AI Watermark Remover
[Change folder]

Temporary files ...
Cache ...
[Clear cache]
```

After export:

``` text
Saved to:
D:\Pictures\AI Watermark Remover\processed\image.png
[Open folder]
```

Never silently hide output locations.

------------------------------------------------------------------------

# 36. Filename Rules

Default:

`{original_name}_removed.{format}`

Examples: - `photo.jpg → photo_removed.jpg` -
`photo.jpg → photo_removed.png`

Never produce: - `photo.jpg.txt` - `photo.png.html` - extension/format
mismatches

The actual binary encoding must match the displayed format.

------------------------------------------------------------------------

# 37. Privacy UX

Local-first messaging:

``` text
LOCAL-FIRST
Your images are processed on this device by default.
No image is uploaded unless you explicitly enable an external AI provider.
```

If external fallback is enabled, update the message dynamically.

Never make a local-processing claim that becomes false when external
fallback is active.

------------------------------------------------------------------------

# 38. Analytics UX

Default analytics should be privacy-first and local where possible.

Useful aggregate metrics: - images processed - average processing time -
batch usage - export formats - errors

Do not collect image content, filenames, or personal data merely because
the UI can display metrics.

------------------------------------------------------------------------

# 39. Component Architecture

Build a reusable design system rather than one-off page markup.

Core components:

``` text
AppShell
Sidebar
Header
PageHeader
Panel
Section
Button
IconButton
Tooltip
Tabs
Badge
StatusBadge
Progress
Slider
Checkbox
Switch
Select
Input
Dialog
Drawer
Toast
Dropdown
ContextMenu
EmptyState
LoadingState
ErrorState
ImageDropzone
ImageCanvas
MaskOverlay
Preview
BeforeAfterSlider
Queue
QueueItem
ExportPanel
ModelCard
Metric
```

Every component should have consistent variants and states.

------------------------------------------------------------------------

# 40. Design Tokens

Centralize tokens such as:

``` text
--color-bg
--color-surface
--color-surface-raised
--color-border
--color-text
--color-text-muted
--color-accent
--color-success
--color-warning
--color-error

--space-1 ... --space-10
--radius-sm --radius-md --radius-lg
--font-xs --font-sm --font-md --font-lg --font-xl
```

Theme changes must happen through tokens, not scattered CSS overrides.

------------------------------------------------------------------------

# 41. State Matrix

Every major feature must consider:

``` text
EMPTY
LOADING
READY
ACTIVE
PROCESSING
SUCCESS
WARNING
ERROR
CANCELLED
RECOVERABLE
```

Batch additionally needs: - partial completion - needs review - per-item
failure - export preparation - ZIP ready

The screen count is therefore not just pages. It is:

**Screens + states + modals + drawers + backend states + errors +
recovery.**

------------------------------------------------------------------------

# 42. Production UI Screen Inventory

## Core editor

1.  Editor --- empty
2.  Editor --- image loaded
3.  Editor --- paint
4.  Editor --- erase
5.  Editor --- mask ready
6.  Editor --- processing
7.  Editor --- validating
8.  Editor --- result
9.  Editor --- comparison
10. Editor --- export

## Batch

11. Batch --- empty
12. Batch --- files loaded
13. Batch --- processing
14. Batch --- partially complete
15. Batch --- completed
16. Batch --- needs review
17. Batch --- failed
18. Batch --- preview
19. Batch --- export
20. Batch --- ZIP creation

## System

21. Models
22. Model download
23. Model verification
24. Model error
25. Settings
26. Appearance
27. AI providers
28. Storage
29. Diagnostics
30. History
31. About
32. First-run onboarding

## Global surfaces

33. Command palette
34. Keyboard shortcuts
35. Confirmation dialog
36. Error dialog
37. Export dialog
38. Preview modal
39. Toast/notification
40. Update dialog

Each relevant screen also requires
empty/loading/success/warning/error/disabled/recovery states.

------------------------------------------------------------------------

# 43. Engineering Alignment Matrix

  Engineering system   UI surface/state
  -------------------- ------------------------------------------
  Model manager        Models + download + verify + repair
  Device manager       Hardware status
  Batch engine         Batch queue + progress
  Async jobs           Live processing state
  Result validation    Validating + result-ready state
  Export layer         Export + download + ZIP
  Output storage       Storage settings + saved-to confirmation
  Cancellation         Cancelled state + recovery
  AI fallback          Provider settings + fallback status
  Diagnostics          Diagnostics workspace
  Logging              Safe log viewer
  Error handling       Error/recovery UI
  Performance          Honest progress + metrics
  History              History workspace
  Packaging            First-run/setup experience
  Security             Safe error and configuration messaging

If engineering adds a backend state, the UI must represent it.

If UI adds a control, there must be real backend behavior behind it.

------------------------------------------------------------------------

# 44. Visual QA Gate

Every screen must be checked for:

-   consistent spacing
-   consistent typography
-   consistent icon sizing
-   consistent borders
-   consistent radii
-   consistent color roles
-   no accidental gradients
-   no random shadows
-   no clipped text
-   no overlapping controls
-   no hidden primary action

Test at multiple desktop sizes and Windows scaling levels.

------------------------------------------------------------------------

# 45. Interaction QA Gate

Every interactive component should have the appropriate:

-   idle
-   hover
-   focus
-   active
-   selected
-   disabled
-   loading
-   success
-   warning
-   error

Inputs additionally need: - empty - filled - focused - invalid -
disabled

------------------------------------------------------------------------

# 46. Do Not Design Only the Happy Path

For every screen ask:

-   What if there is no data?
-   What if loading takes 60 seconds?
-   What if processing fails?
-   What if the user cancels?
-   What if the file is corrupt?
-   What if the model is missing?
-   What if the GPU is unavailable?
-   What if VRAM is insufficient?
-   What if disk is full?
-   What if the output folder disappears?
-   What if the browser/app loses connection?
-   What if one batch item fails?
-   What if every batch item fails?
-   What if 500 images are loaded?
-   What if a model download is interrupted?
-   What if the application restarts during a batch?

These are UI design requirements because they change what the user sees
and what the user can do next.

------------------------------------------------------------------------

# 47. Forbidden Anti-Patterns

Do not build:

-   giant dashboard cards for simple information
-   neon everywhere
-   excessive glassmorphism
-   fake AI animations
-   fake progress
-   fake ETA
-   fake confidence
-   fake completion
-   mystery icons
-   icon-only actions without labels/tooltips
-   tiny unreadable text
-   full-screen spinners for ordinary local operations
-   decorative analytics with no product value
-   settings scattered across unrelated screens
-   raw filesystem paths in normal UI
-   buttons that do nothing
-   mock data presented as real processing
-   downloaded HTML/JSON/text disguised as images
-   extension-only format conversion

------------------------------------------------------------------------

# 48. Implementation Order

Do not implement every screen simultaneously.

## Phase A --- Design foundation

1.  tokens
2.  typography
3.  colors
4.  spacing
5.  icons
6.  buttons
7.  inputs
8.  panels
9.  sidebar
10. header
11. dialogs
12. toast system
13. status system

## Phase B --- Core editor

1.  upload
2.  canvas
3.  pan
4.  paint
5.  erase
6.  mask
7.  zoom
8.  process
9.  processing state
10. result
11. comparison
12. export

## Phase C --- Batch

1.  multi-upload
2.  queue
3.  selection
4.  progress
5.  preview
6.  per-item download
7.  selected/all download
8.  ZIP
9.  review
10. reference mode
11. cancellation

## Phase D --- System

1.  model manager
2.  hardware
3.  settings
4.  storage
5.  diagnostics
6.  history
7.  about
8.  onboarding

## Phase E --- Polish

1.  keyboard shortcuts
2.  command palette
3.  motion
4.  accessibility
5.  responsive behavior
6.  visual QA
7.  performance QA

------------------------------------------------------------------------

# 49. Production Definition of UI Done

A screen is NOT done because it: - looks good - builds - contains a
button - shows mock data - has an animation

It is done only when:

1.  real backend state exists
2.  real data appears
3.  empty state works
4.  loading state works
5.  success state works
6.  failure state works
7.  recovery works
8.  keyboard navigation works
9.  focus is visible
10. dark theme works
11. light theme works
12. resize works
13. refresh/restart behavior is safe
14. no fake success exists
15. the complete real workflow has been manually tested

------------------------------------------------------------------------

# 50. Final Product Experience

## Single image

``` text
OPEN APP
  ↓
Environment/model check
  ↓
Editor
  ↓
Drop image
  ↓
Canvas
  ↓
Mark watermark
  ↓
Run removal
  ↓
Real progress
  ↓
Real result validation
  ↓
Before / After
  ↓
Export
  ↓
File opens correctly
```

## Batch

``` text
DROP 100 IMAGES
  ↓
Queue appears immediately
  ↓
Choose detection/reference strategy
  ↓
Start batch
  ↓
Live progress
  ↓
Completed / Review / Failed
  ↓
Preview any result
  ↓
Download individual
  ↓
Download selected/all
  ↓
ZIP completed
  ↓
Extract ZIP
  ↓
Every image opens correctly
```

------------------------------------------------------------------------

# 51. Final Design Rule

The product must not become a collection of attractive screens.

It must become a coherent professional tool:

> **Minimal at the surface, powerful underneath, explicit about state,
> fast for experts, understandable for first-time users, accessible, and
> honest about what the system actually did.**

The visual benchmark is professional creative software, not a generic AI
dashboard.

The engineering benchmark remains the companion production checklist.

The UI benchmark is:

> **Understand → Act → See what is happening → Verify → Export →
> Recover.**

Both documents must pass before release.

------------------------------------------------------------------------

# 52. Research References

-   Apple Human Interface Guidelines --- Design Principles:
    https://developer.apple.com/design/human-interface-guidelines/design-principles/
-   Apple Human Interface Guidelines:
    https://developer.apple.com/design/human-interface-guidelines/
-   Adobe Photoshop Workspace Overview:
    https://helpx.adobe.com/photoshop/desktop/get-started/learn-the-basics/workspace-overview.html
-   Adobe Photoshop Contextual Task Bar:
    https://helpx.adobe.com/photoshop/desktop/get-started/learn-the-basics/boost-workflows-with-the-contextual-task-bar.html
-   Topaz Photo Export:
    https://docs.topazlabs.com/topaz-photo/functions/export
-   PhotoRoom Batch Editor:
    https://help.photoroom.com/en/articles/14181758-quick-guide-to-the-batch-editor-ui-web-app
-   Microsoft Fluent 2 Accessibility:
    https://fluent2.microsoft.design/accessibility
-   Microsoft Fluent 2 Navigation:
    https://fluent2.microsoft.design/components/web/react/core/nav/usage
-   shadcn/ui Sidebar:
    https://ui.shadcn.com/docs/components/base/sidebar
-   shadcn/ui Blocks: https://ui.shadcn.com/blocks
-   Vercel Geist: https://vercel.com/geist/introduction
-   Vercel Geist Typography: https://vercel.com/geist/typography
-   Vercel Geist Colors: https://vercel.com/geist/colors
-   Stripe App Design: https://docs.stripe.com/stripe-apps/design
-   Stripe UI Components: https://docs.stripe.com/stripe-apps/components
-   Stripe Styling: https://docs.stripe.com/stripe-apps/style
-   W3C WCAG 2.2:
    https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
-   W3C Focus Visible:
    https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
-   W3C Focus Appearance:
    https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html

------------------------------------------------------------------------

# 53. Companion Engineering Source of Truth

Use this document together with:

`production_grade_software_master_checklist.md`

The engineering checklist explicitly requires real model
discovery/reuse, recoverable model downloads, graceful GPU/CPU fallback,
isolated runtime dependencies, predictable output storage, validated
downloads, batch ZIP export, clean-machine testing, Docker verification,
packaging verification, upgrade safety, and evidence-based release
acceptance.

The UI must represent those states honestly and completely.

**No visual polish can compensate for a broken processing pipeline. No
backend feature is production-complete if the user cannot understand or
control it.**

# UI/UX MASTER V2 --- Research-Validated Implementation Addendum

This addendum upgrades the existing UI/UX specification using current
2026-era patterns from professional creative software, desktop HIGs,
mature design systems, batch media editors, and accessibility standards.

It does **not** replace the companion engineering checklist. It makes
the visual/interaction contract stricter.

## A. Design Benchmark: Professional Creative Workspace

The product should follow the mental model:

**Navigation → Tools → Canvas → Context → Result → Export**

Do not turn the application into a conventional SaaS dashboard.

The canvas must receive the largest visual area in Editor mode.

The sidebar should contain navigation and task controls, while
contextual controls should appear near the active task.

The interface should support: - persistent workspace state; -
collapsible navigation; - compact toolbar; - contextual actions; -
keyboard acceleration; - precise pointer interactions; - fullscreen
canvas; - predictable recovery.

## B. Navigation Architecture

Use a persistent left sidebar for desktop.

Recommended hierarchy:

``` text
AI Watermark Remover

WORKSPACE
  Editor
  Batch

LIBRARY
  History
  Exports

SYSTEM
  Models
  Settings
  Diagnostics
  About
```

The sidebar must: - collapse to icon mode; - preserve state; - expose
tooltips; - have visible active state; - remain keyboard accessible; -
support scrolling when content exceeds viewport; - never hide critical
status only because it is collapsed.

Do not create five different navigation systems for five screens.

## C. Editor Layout Rule

Editor priority:

``` text
Canvas > Active tool controls > Result/context > Secondary settings
```

Never:

``` text
Cards > Dashboard metrics > Decorative content > Canvas
```

Use a three-zone workspace only when it improves the current task:

``` text
┌──────────────┬──────────────────────────┬──────────────────────┐
│ Tools        │ Canvas                   │ Context / Result     │
│ Controls     │                          │                      │
└──────────────┴──────────────────────────┴──────────────────────┘
```

The right panel should be collapsible.

The canvas should expand when secondary panels disappear.

## D. Toolbar Rules

The top toolbar should contain only high-frequency actions:

-   undo;
-   redo;
-   fit;
-   zoom;
-   compare;
-   fullscreen;
-   export where appropriate.

Do not put every command in the toolbar.

Secondary actions belong in menus or contextual panels.

## E. Sidebar vs Toolbar vs Panel

Use:

### Sidebar

For: - navigation; - persistent workspace controls; - grouped settings.

### Toolbar

For: - frequent actions; - current document actions; - view controls.

### Context panel

For: - tool-specific options; - current selection; - current result; -
export configuration.

### Dialog

For: - destructive actions; - important confirmations; - focused
workflows.

### Drawer

For: - secondary configuration on constrained screens.

This separation prevents the interface from becoming a pile of controls.

## F. Visual Language

Use restrained surfaces:

``` text
Background
Surface
Raised surface
Border
Text
Muted text
Accent
Semantic status colors
```

Use borders and spacing to establish hierarchy before using shadows.

Do not create a card around every label.

Do not use gradients as the primary hierarchy mechanism.

Do not use transparency merely because the product is "AI".

## G. Typography

Typography must create hierarchy before color does.

Use: - one primary family; - limited weights; - consistent line
heights; - consistent numeric styling; - sentence case labels; - short
action labels.

Prefer:

`Run removal`

over:

`Start AI Powered Watermark Removal Process`

Prefer:

`Download result`

over:

`Download Your Amazing Processed Image`

## H. Information Density

Professional users should be able to scan the screen quickly.

Use: - aligned values; - compact metadata; - clear section headers; -
predictable spacing; - dense but readable queue rows.

Avoid: - huge whitespace blocks; - giant cards; - decorative
statistics; - oversized headings.

## I. State Design Is Part of the Visual Design

Every major surface needs a complete state matrix.

For example, Editor:

``` text
EMPTY
IMPORTING
READY
MASKING
MASK READY
PROCESSING
VALIDATING
RESULT READY
NEEDS REVIEW
FAILED
```

Batch:

``` text
EMPTY
QUEUED
RUNNING
PARTIAL
NEEDS REVIEW
COMPLETED
FAILED
CANCELLED
```

Model:

``` text
NOT INSTALLED
DOWNLOADING
VERIFYING
READY
LOADING
CORRUPTED
INCOMPATIBLE
ERROR
```

A production design must show all of these states.

## J. Mask Interaction

Paint and Erase are not cosmetic tools.

Paint: - adds to mask.

Erase: - subtracts from mask.

The source image must remain unchanged until actual inpainting.

The cursor must visibly represent brush diameter.

When the cursor is over a bright image, the cursor must still be
visible.

Use a high-contrast outline and/or dual-tone cursor treatment.

Do not use a faint white circle that disappears into white backgrounds.

## K. Result Experience

The result is the product's proof.

After processing, the user should immediately see:

``` text
RESULT READY

[Original] [Split] [Slider] [Result]

[Download result]
[Export]
```

Do not force the user to navigate elsewhere to discover the result.

The Result surface must never show a broken image while the job is
marked Completed.

## L. Before/After Comparison

Provide three comparison mechanisms:

1.  Side-by-side;
2.  Split view;
3.  Before/after slider.

All three must use the exact same original/result pair.

The slider must: - preserve alignment; - remain stable during resize; -
have a visible handle; - not trigger page scrolling accidentally; - work
at different zoom levels.

## M. Batch Design

Batch is a high-throughput production surface.

Recommended visual hierarchy:

``` text
Batch title
↓
Batch summary
↓
Primary batch controls
↓
Queue
↓
Export actions
```

Queue rows should prioritize:

``` text
thumbnail
filename
status
confidence
processing time
preview
download
```

Selection actions:

``` text
Select all
Select none
Selected count
Download selected
ZIP selected
```

Global actions:

``` text
Download all
ZIP all
Retry failed
Cancel batch
```

Do not make users open each row to perform obvious batch actions.

## N. Batch Preview

The preview should be a focused workspace, not a completely separate
page.

Use:

``` text
PREVIEW 4 / 100

[Original] [Split] [Slider] [Result]

< Previous                         Next >

[Download this]
```

Use thumbnail navigation.

Only load full-resolution assets for the active image.

This is important for 100--500+ image batches.

## O. Export UX

Export is a core workflow.

Single:

``` text
Download result
```

Advanced:

``` text
Format
Quality
Filename
Destination
Export
```

Batch:

``` text
Download selected
Download all
ZIP selected
ZIP all
```

Never create an export UI that only changes the file extension.

The actual encoded MIME must match the chosen format.

## P. Output Location

The UI must always answer:

> Where did my image go?

Desktop/native:

``` text
Saved to:
Pictures / AI Watermark Remover / Outputs

[Open folder]
```

Browser:

Use real browser download behavior.

Never show a fake folder picker in web mode.

Never claim an output was saved if the output file was not actually
persisted.

## Q. Model Manager Design

Model UI should look like a real runtime manager, not a download card.

Example:

``` text
LaMa Inpainting

READY
196 MB
v1.0.0

Load      1.2s
Inference 12.9s
VRAM      196 MB

[Details]
[Verify]
[Repair]
```

The UI must distinguish:

-   installed;
-   verified;
-   loaded;
-   ready;
-   currently loading.

Do not collapse these into one green "Installed" badge.

## R. Runtime Status

Runtime information should be compact but trustworthy.

``` text
CUDA • RTX 3050 • Ready
```

If CPU:

``` text
CPU • Fallback • Ready
```

If GPU initialization failed:

``` text
GPU unavailable • CPU fallback
```

The UI must use detected values, never hard-coded hardware labels.

## S. Settings Information Architecture

Settings should be grouped by user intent:

``` text
General
Processing
Models
Export
Appearance
AI fallback
Performance
Privacy
Storage
Advanced
```

Do not create one enormous scrolling settings page with unrelated
toggles.

Use progressive disclosure for advanced options.

## T. Light/Dark/System Theme

Theme is a system, not a recolor.

All components must have:

-   dark tokens;
-   light tokens;
-   semantic status colors;
-   focus states;
-   disabled states;
-   hover states.

Do not patch light mode with one-off overrides.

Do not hard-code colors inside individual components.

## U. Accessibility Acceptance

Baseline: WCAG 2.2 AA.

Required: - keyboard operation; - visible focus; - sufficient
contrast; - accessible names; - logical focus order; - non-color status
communication; - reduced motion; - usable controls at 125% and 150%
Windows scaling.

For critical focus indicators, use a strong visible treatment rather
than relying on a barely visible browser outline.

## V. Responsive Desktop Rules

Test:

``` text
1280×720
1366×768
1440×900
1920×1080
2560×1440
125% Windows scaling
150% Windows scaling
```

Also test browser zoom.

At reduced width:

1.  collapse sidebar;
2.  hide secondary panels;
3.  move advanced settings into drawers;
4.  preserve the canvas;
5.  preserve the primary action.

Never make the canvas so small that image editing becomes impractical.

## W. Interaction Quality

Every interaction should have:

``` text
Intent
Immediate feedback
Stable state
Recovery path
```

Example:

Click Run removal:

``` text
Run removal
↓
Preparing
↓
Processing
↓
Validating
↓
Result ready
```

Failure:

``` text
Processing failed
↓
Explain reason
↓
Retry / fallback / diagnostics
```

## X. Error Design

Do not expose raw exceptions to normal users.

Instead:

``` text
RESULT COULD NOT BE LOADED

The processed image exists, but the application
could not retrieve it.

[Retry]
[View diagnostics]
```

Technical details belong in Diagnostics.

## Y. Performance-Aware UI

The interface should expose measured performance only.

Useful:

``` text
Processing 24 / 100
Average 1.8s/image
Workers 2
GPU memory 3.1 / 4.0 GB
```

Only show a metric if the backend actually measures it.

Never fake: - ETA; - GPU utilization; - progress; - speed; - completion.

## Z. Large-Batch Memory Rules

For 100--500+ images:

-   virtualize rows;
-   lazy-load thumbnails;
-   unload inactive full-resolution previews;
-   avoid storing unnecessary image blobs in React state;
-   release object URLs;
-   use pagination/windowing where appropriate;
-   preserve backend job state independently of the browser.

The UI must remain responsive even while the worker is processing.

## AA. Design System Enforcement

Create one source of truth for:

``` text
colors
spacing
typography
radii
shadows
z-index
motion
component variants
breakpoints
sidebar widths
canvas chrome
status colors
```

No page should invent its own design language.

## AB. No Hard-Coded Product Assumptions

Do not hard-code:

``` text
RTX 3050
4 GB
D:\Starter Kit
localhost:3000
one model
one provider
one export format
one batch size
one browser width
```

Runtime values must come from configuration/state.

UI capabilities must come from actual backend capabilities.

## AC. Reusable Screen Composition

Build screens from shared primitives.

Example:

``` text
AppShell
 ├── Sidebar
 ├── Header
 └── Workspace

Editor
 ├── SourcePanel
 ├── CanvasWorkspace
 └── ContextPanel

Batch
 ├── BatchControls
 ├── Queue
 ├── BatchSummary
 └── ExportBar

Preview
 ├── ComparisonToolbar
 ├── ComparisonCanvas
 └── ThumbnailStrip
```

This prevents the application from becoming a collection of unrelated
pages.

## AD. Visual QA

Before approving a screen:

-   inspect at every target resolution;
-   inspect at 125% scaling;
-   inspect at 150% scaling;
-   inspect light mode;
-   inspect dark mode;
-   inspect empty state;
-   inspect loading;
-   inspect success;
-   inspect error;
-   inspect disabled;
-   inspect keyboard focus;
-   inspect long filenames;
-   inspect large numbers;
-   inspect large image dimensions;
-   inspect batch with 100+ rows.

## AE. Final UI Gate

Do not declare UI/UX complete until all of these are true:

``` text
[ ] Canvas is dominant
[ ] Sidebar is consistent
[ ] Toolbar is compact
[ ] Editor is understandable in seconds
[ ] Paint works visibly
[ ] Erase cursor is visible
[ ] Mask states are clear
[ ] Processing state is truthful
[ ] Result state is truthful
[ ] Original/Result comparison works
[ ] Slider works
[ ] Single export is obvious
[ ] Batch export is obvious
[ ] ZIP actions are obvious
[ ] Batch preview works
[ ] History works
[ ] Model state is truthful
[ ] Runtime state is truthful
[ ] AI fallback state is explicit
[ ] Output location is understandable
[ ] Light mode works
[ ] Dark mode works
[ ] System theme works
[ ] Keyboard navigation works
[ ] Focus is visible
[ ] Responsive desktop layouts work
[ ] Large batches remain usable
[ ] No screen depends on hard-coded runtime values
[ ] No fake data is used for functional UI
```

## AF. Research References

These references were reviewed for this specification:

-   Apple HIG --- Sidebars\
    https://developer.apple.com/design/human-interface-guidelines/sidebars/

-   Apple HIG --- Toolbars\
    https://developer.apple.com/design/human-interface-guidelines/toolbars/

-   Apple HIG --- Designing for macOS\
    https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/

-   Microsoft Fluent 2 Accessibility\
    https://fluent2.microsoft.design/accessibility

-   Microsoft Fluent 2 Navigation\
    https://fluent2.microsoft.design/components/web/react/core/nav/usage

-   shadcn/ui Sidebar\
    https://ui.shadcn.com/docs/components/base/sidebar

-   Vercel Geist Colors\
    https://vercel.com/geist/colors

-   Stripe App Design\
    https://docs.stripe.com/stripe-apps/design

-   Stripe UI Components\
    https://docs.stripe.com/stripe-apps/components

-   Figma UI Design Principles\
    https://www.figma.com/resource-library/ui-design-principles/

-   Figma Design Systems\
    https://www.figma.com/blog/design-systems-102-how-to-build-your-design-system/

-   Figma Typography Systems\
    https://www.figma.com/best-practices/typography-systems-in-figma/

-   W3C WCAG 2.2 --- Focus Visible\
    https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html

-   W3C WCAG 2.2 --- Focus Appearance\
    https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html

-   PhotoRoom Batch Editor\
    https://help.photoroom.com/en/articles/14181758-quick-guide-to-the-batch-editor-ui-web-app

-   PhotoRoom Batch\
    https://help.photoroom.com/en/articles/11784338-what-is-the-batch-feature

-   Cloudinary Media Editor\
    https://cloudinary.com/documentation/media_editor

-   Cloudinary Studio\
    https://cloudinary.com/documentation/dam_editing_and_transformations

------------------------------------------------------------------------

# FINAL RULE

Do not treat this as inspiration.

Treat it as the UI/UX acceptance contract.

Do not copy another product.

Study the patterns, then implement a coherent original design language
for AI Watermark Remover.

The result should feel like a serious 2026 creative application:

**clean + dense + precise + fast + trustworthy + image-first +
production-grade.**
