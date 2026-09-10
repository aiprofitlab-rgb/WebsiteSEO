#!/usr/bin/env python3
"""What every page under /en/tools/ shares.

Extracted from page_tool_efawtara.py when the second tool arrived, which is
exactly what the comment at the top of that block said should happen rather
than copying it. Both tools now import from here, so the privacy claim and the
tool header are one component and not two that drift.

Nothing page-specific belongs in this file. If only one tool needs it, it
lives in that tool's module.
"""

# The padlock, inline rather than an <img>: it is 300 bytes, it must not cost
# a request, and it is the icon on the one claim this whole tool set rests on.
LOCK_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 1a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 '
             '2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V11a2 2 0 0 0-2-2h-1V6a5 5 0 0 0-5-5zm0 2a3 3 0 0 1 3 '
             '3v3H9V6a3 3 0 0 1 3-3zm0 11a2 2 0 0 1 1 3.7V20h-2v-2.3A2 2 0 0 1 12 14z"/></svg>')

SHELL_CSS = """
/* =========================================================== tool shell */
/* Shared by every page under /en/tools/ - see tools/v4/tool_kit.py. */
.toolbar{
  display:flex;flex-wrap:wrap;gap:10px 22px;align-items:center;
  font-family:var(--mono);font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);margin:0 0 clamp(20px,3vw,30px);
}
.toolbar span{display:inline-flex;align-items:center;gap:8px}
.toolbar b{font-weight:500;color:var(--teal-950)}
.s-dark .toolbar,.s-teal .toolbar{color:rgba(241,239,232,.6)}
.s-dark .toolbar b,.s-teal .toolbar b{color:var(--cream)}

/* The privacy claim. It is a load-bearing sentence, so it is a component and
   not a paragraph someone can quietly soften. */
.local{
  display:flex;gap:14px;align-items:flex-start;
  border:1px solid var(--line);border-radius:14px;background:var(--white);
  padding:16px 18px;margin:clamp(22px,3vw,32px) 0 0;
}
.local svg{width:22px;height:22px;flex:none;fill:var(--teal);margin-top:2px}
.local p{margin:0;font-size:.94rem;line-height:1.6;color:var(--muted)}
.local b{color:var(--teal-950);font-weight:500}
.s-dark .local{background:rgba(241,239,232,.045);border-color:var(--line-dark)}
.s-dark .local p{color:rgba(241,239,232,.72)}
.s-dark .local b{color:var(--cream)}
.s-dark .local svg{fill:var(--amber-bright)}
"""
