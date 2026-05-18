# Antigravity Agent Configuration & Optimization Tasks

## System Guardrails (CRITICAL)
- **Zero Visual Changes:** Do not modify the website's user interface (UI), design layout, or typography. 
- **Color Palette Integrity:** Stay strictly loyal to the existing website color codes. Do not alter, override, or replace any color definitions in the CSS, Tailwind configuration, or components.
- **Logo Preservation:** Do not modify, recreate, or replace the website logo. It must remain completely untouched in its original state and size.
- **Scope Restriction:** Your authorization is strictly limited to backend performance, server configurations, caching headers, script loading optimization, and asset delivery pipelines.

## Core Objective
Optimize the performance of `aiprofitlab.io` to address the 1.2s Time to First Byte (TTFB) and 1.7s Largest Contentful Paint (LCP) flagged in the GTmetrix report, while keeping the frontend visuals 100% identical.

## Task Backlog

### Task 1: Reduce Initial Server Response Time (High Priority)
- **Problem:** The root document takes 840ms to respond, causing a sluggish TTFB.
- **Action:** Audit the hosting environment, server configuration, or framework setup (e.g., Next.js/Vercel). Identify backend rendering bottlenecks. If applicable, ensure pages meant to be Statically Generated (SSG) are not accidentally relying on Server-Side Rendering (SSR) for every request. Aim to drop backend processing below 300ms.

### Task 2: Implement Efficient Cache Policies (Medium Priority)
- **Problem:** Static assets lack optimal long-term cache strategies.
- **Action:** Apply aggressive caching headers (`Cache-Control: public, max-age=31536000, immutable`) to all static assets, specifically targeting Tailwind CSS files, Google Fonts (Cairo / gstatic), and the background image (`hero-bg.webp`).
- **Action:** Preload critical font assets to eliminate any render-blocking resource chains.

### Task 3: Optimize JavaScript Execution (Low Priority)
- **Problem:** JavaScript execution blocks the main thread for 133ms.
- **Action:** Inspect script integrations (e.g., Google Tag Manager or custom scripts). Ensure non-critical third-party JS uses `defer` or `async` attributes so they do not block page rendering.

## Operational Workflow
1. Analyze the current infrastructure, hosting platform, and repository setup.
2. Present a precise technical plan for the server/caching adjustments before execution.
3. Apply optimizations step-by-step, verifying network headers and server response times after each deployment.