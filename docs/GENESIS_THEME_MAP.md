# Genesis Theme Map — Visual Source of Truth

**Reference Path**: `D:\Download\genesis-nextjs`
**Date Created**: 2026-08-13
**Author**: Antigravity AI for Aniket

---

## 🎨 1. Core Visual Tokens & Design System

| Token | Genesis Reference Value | Tailwind / CSS Mapping |
|---|---|---|
| **Background Color** | Pitch Black (`#000000` / `#020617`) | `bg-black` or `bg-slate-950` |
| **Primary Text** | Pure White (`#FFFFFF`) | `text-white` / `text-slate-50` |
| **Muted Text** | Slate / Gray (`#94A3B8` / `#CBD5E1`) | `text-slate-400` / `text-slate-300` |
| **Primary Accent** | Genesis Orange (`#F26A06`) | `text-[#F26A06]`, `bg-[#F26A06]`, `from-[#F26A06]` |
| **Secondary Accent** | Genesis Magenta (`#D10A8A`) | `bg-[#D10A8A]`, `to-[#D10A8A]` |
| **Tertiary Accent** | Electric Indigo (`#2E08CF`) | `bg-[#2E08CF]` |
| **Glass Surface** | Semi-transparent White/Slate | `bg-white/10 border border-white/20 backdrop-blur-xl` |
| **Glass Card** | Dark Translucent | `bg-slate-900/60 border border-slate-800/80 backdrop-blur-md` |
| **Font Family** | Poppins / Sans-Serif | `font-sans` (`var(--font-sans)`) |
| **Button Shape** | Rounded Full Pill | `rounded-full px-6 py-2.5 font-medium` |

---

## 🌌 2. Ambient Background Glow Orbs (Signature Genesis Effect)

The signature Genesis visual atmosphere is created by three fixed, blurred glow orbs behind the UI:

```jsx
<div className="fixed inset-0 overflow-hidden -z-20 pointer-events-none">
    <div className="absolute rounded-full top-80 left-2/5 -translate-x-1/2 size-130 bg-[#D10A8A] blur-[100px] opacity-40" />
    <div className="absolute rounded-full top-80 right-0 -translate-x-1/2 size-130 bg-[#2E08CF] blur-[100px] opacity-40" />
    <div className="absolute rounded-full top-0 left-1/2 -translate-x-1/2 size-130 bg-[#F26A06] blur-[100px] opacity-50" />
</div>
```

---

## 🧩 3. Component Architecture & UI Mapping

### Header / Navbar
- Single sticky header at `top-0 z-50`
- Glassmorphism backdrop: `bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80`
- Brand Logo with Genesis Orange gradient orb: `from-[#F26A06] to-[#D10A8A]`
- Pill navigation switch with active item highlighted in Genesis Orange (`bg-[#F26A06] text-white shadow-lg shadow-orange-500/20`)

### Interactive Cards & Watermark Panels
- Rounded corners (`rounded-2xl`)
- Subtly glowing border (`border border-white/10 hover:border-orange-500/30 transition-all`)
- Dark glass container fill (`bg-slate-900/50 backdrop-blur-md`)

### Buttons & Actions
- Primary CTA: Genesis Orange gradient (`bg-gradient-to-r from-[#F26A06] to-[#D10A8A] hover:opacity-95 shadow-lg shadow-orange-500/25`)
- Secondary CTA: Glass pill (`bg-white/10 border border-white/20 text-white hover:bg-white/20`)

---

## 🔒 Protection Rule
All UI components in `web_ui/components` and `web_ui/sections` must strictly adhere to this color palette and glassmorphic styling to maintain visual identity consistency.
