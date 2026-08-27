# Antigravity Agent Configuration

## Stack
Static HTML under `public_html/`, built by Python scripts in `tools/`, styled with Tailwind CSS v4 CLI, deployed to Apache shared hosting over FTP. There is no Next.js, no Vercel, and no server-side rendering — caching and headers are controlled by `public_html/.htaccess`.

## System Guardrails (CRITICAL)
- **Zero Visual Changes:** Do not modify the website's user interface (UI), design layout, or typography.
- **Color Palette Integrity:** Stay strictly loyal to the existing website color codes. Do not alter, override, or replace any color definitions in the CSS, Tailwind configuration, or components.
- **Logo Preservation:** Do not modify, recreate, or replace the website logo. It must remain completely untouched in its original state and size.
- **Scope Restriction:** Your authorization is strictly limited to backend performance, server configurations, caching headers, script loading optimization, and asset delivery pipelines.

## Operational Workflow
1. Analyze the current infrastructure, hosting platform, and repository setup.
2. Present a precise technical plan for the server/caching adjustments before execution.
3. Apply optimizations step-by-step, verifying network headers and server response times after each deployment.
