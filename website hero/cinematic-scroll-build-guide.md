







<!-- Start of picture text -->
) a<br><!-- End of picture text -->



<!-- Start of picture text -->
ry i 2? = GF<br>e t@  f-<br>- ¢ yf a<br><!-- End of picture text -->



<!-- Start of picture text -->
a"a<br>x: CF /<br>es<br><!-- End of picture text -->

###### **PROMPT 06** 

_“remove any text on that position after "onchain influence built with real ones" — it will cover the video.”_ 

###### **MY MOVE** 

Trimmed the SCENES array to one opening line. The center caption now fades in early and clears out fast, leaving the rest of the scrub uncovered. Side overlays stay because they sit on the edges, away from the subject. 

###### **PROMPT 07** 

_“remove the slogan. tighter gap between logo and wordmark. like a header on the video. no background. slightly dark gradient from above lightening downward.”_ 

###### **MY MOVE** 

Moved logo + NABULINES into CinematicHero as a top-overlay header (white, 8px gap, tight horizontal lockup). Added a top-aligned dark-to-transparent gradient overlay (0.55 → 0 alpha across 28% of the stage) so the white header reads against the cream video. 

###### **PROMPT 08** 

#### _“remove the black background of the logo.”_ 

###### **MY MOVE** 

Pre-generated a true transparent PNG: load logo.png, map luminance → alpha (white logo strokes get full alpha, black background goes transparent), save as logo-transparent.png. Dropped the mix-blend-mode: screen hack — it couldn't beat the dark gradient backdrop. 

###### **PROMPT 09** 

#### _“the video is not loading on mobile.”_ 

###### **MY MOVE** 

Three fixes in one move: (a) replaced flaky <source media=...> with JS-based src selection at mount; (b) re-encoded mobile with _Constrained Baseline_ profile and GOP 5 (iOS hardware decoder loves baseline + dense-but-not-every-frame keyframes), dropped mobile from 17 MB to 6.3 MB; (c) added preload="auto" + a play/pause warm-up. 

###### **PROMPT 10** 

#### _“still nothing, on mobile it appears one sec then disappears.”_ 

###### **MY MOVE** 

Classic iOS Safari quirk — the <video> element blanks itself when you rapidly seek currentTime on a paused stream. The play/pause warm-up made it worse, not better. Final fix: on mobile (matchMedia max-width 768px) we ditch the scrub entirely and just autoplay + loop the video. Scroll still drives the orbitron overlays + caption + progress bar. Desktop scrub stays unchanged. 

NABULINES — cinematic scroll landing — build guide 

page 6 

## **03. Tips to build this yourself** 

Twelve lessons distilled from the journey. None of these are in tutorials. All of them came from something breaking first. 

# **01** 

##### **Crop the source before you optimize.** 

Portrait video with black letterbox bars baked in is the most common waste. Run ffmpeg ... -vf cropdetect on a 5-second window to detect the real content rectangle, then crop. Our source was 1080×1446 with only 1080×606 of actual content — 58% of the pixels were black. 

# **02** 

##### **+faststart is non-negotiable.** 

-movflags +faststart moves the moov atom to the front of the mp4. Without it, the browser must download the whole file before it can show frame one. With it, playback begins after just the first KB or two. Verify with python3 -c "with open('x.mp4','rb') as f: d=f.read(2_000_000); print(d.find(b'moov') < d.find(b'mdat'))" — must print True. 

# **Every-frame keyframes for sharp scrub. 03** 

Browsers render the nearest keyframe when you set currentTime. Default GOP is ~250 frames. For a scroll-scrub, encode with -g 1 -keyint_min 1 -sc_threshold 0 -x264-params keyint=1:min-keyint=1:scenecut=0. File grows ~3-5×, but every scroll position lands on a real frame. 

# **04** 

##### **Mobile = Constrained Baseline, not High.** 

iOS Safari's hardware decoder accelerates Baseline and Main reliably. High-profile + every-frame keyframes makes the decoder fall back to software, which on mobile is slow and bug-prone. Re-encode mobile with -profile:v baseline -level 3.1 -g 5 — much smaller, much more reliable, slightly softer scrub (which doesn't matter at phone resolution). 

# **05** 

##### **overflow-x: clip beats overflow-x: hidden.** 

overflow-x: hidden on html or body silently turns that element into a scroll container, which breaks position: sticky everywhere. Use overflow-x: clip — same horizontal clipping, no scroll container side-effect. Universally supported now. 

# **06** 

##### **Don't use <source media> inside <video>.** 

The media attribute is only spec'd for <source> children of <picture>. Inside <video> browsers ignore it and pick the first type-matching source. Resolve the source URL in JS at mount: matchMedia('(max-width: 768px)').matches ? mobileMp4 : desktopMp4. 

NABULINES — cinematic scroll landing — build guide 

page 7 

# **07** 

# **08** 



<!-- Start of picture text -->
09<br><!-- End of picture text -->

# **10** 

# **11** 

# **12** 

##### **IntersectionObserver gates the heavy bytes.** 

Don't ship 30 MB of video to every visitor — only those who scroll to it. rootMargin: '150% 0px 150% 0px' on an observer fires before the section enters the viewport, so the video has time to fetch before the user gets there. Pair with preload="metadata" until the observer fires, then upgrade to preload="auto". 

##### **iOS hates scrub-on-paused.** 

Setting video.currentTime rapidly on a paused <video> element blanks it out on iOS Safari. The only robust fix is to NOT scrub on mobile. Detect via matchMedia and substitute autoplay + loop. Use scroll progress to drive overlays instead of the video timeline. 

##### **Sample colors from the source, then hardcode them.** 

Dynamic-sampling the dominant color at runtime sounds nice but races with first paint and degrades to whatever your fallback is — black if you forget. Run ffmpeg ... -vf crop=20:20:cx:cy on the source, average the pixels with Pillow, and paste the hex into your component as a constant. 

##### **Generate a transparent logo, don't mix-blend-mode it.** 

Blending tricks (screen, multiply, difference) work only against specific backdrops. Once you have a dark gradient or photographic content underneath, blending fails. Pre-process the PNG: read pixels, set alpha = luminance, save as logo-transparent.png. Works on every backdrop forever. 

##### **Parent !important kills your fonts.** 

Global landing-page CSS like .landing-x * { font-family: ... !important } nukes any class-based font you apply inside. Beat it by writing font-family: var(--font-brand) ... !important in your scoped styled-jsx — the higher per-element specificity plus !important wins, every time. 

##### **Cache-bust with ?v=N after each re-encode.** 

When you re-encode the same filename, browsers serve the cached old crunchy version forever. Append ?v=N to your <video src> and poster, increment with every encoder run. Saved a lot of "hard-refresh" confusion during this build. 

NABULINES — cinematic scroll landing — build guide 

page 8 

## **04. The master Claude prompt** 

Use this if you want to recreate the same hero on another project. Paste it as a single prompt to Claude with your video file attached. 

```
Build a cinematic scroll-driven landing hero for my Next.js (app router) project at ~/PROJECT_P
ATH. The video is attached — assume it's portrait/3:4 with the action centered and possibly bla
ck bars baked in.
```

###### `1. CROP + COLOR SAMPLE` 

- `Detect black bars in the source via ffmpeg cropdetect. If bars are present, crop to the real content rectangle. Sample the corner color from a cropped still and use it as the page backdro p so the video is seamless with the page.` 

###### `2. DUAL ENCODE WITH +faststart` 

- `DESKTOP: native cropped resolution, High profile, CRF ~20, every-frame keyframes (-g 1) fo r crisp scrub.` 

- `MOBILE: 854x480, Constrained Baseline profile, GOP 5, CRF ~22 — iOS-friendly. Generate a p oster jpg too.` 

###### `3. CinematicHero.tsx` 

- `section is 3x viewport tall; inner stage is position:sticky top:0 height:100vh` 

- `on DESKTOP only: rAF loop lerps video.currentTime toward scroll position (lerp factor ~0.1 4)` 

- `on MOBILE (matchMedia max-width:768px): autoplay + loop the video, no currentTime touching . Still track scroll progress for overlays.` 

- `resolve the correct video src in JS, NOT via <source media=...> (it doesn't work inside <v ideo>)` 

- `IntersectionObserver gates the actual src injection with rootMargin 200%` 

- `poster paints immediately, preload upgrades from metadata to auto when observer fires` 

NABULINES — cinematic scroll landing — build guide 

page 9 

`3. CinematicHero.tsx (continued)` 

- `center scene caption fades in/out at scroll milestone 0.05 only — anything else covers the subject` 

- `side b-roll overlays slide in from left/right at 8 milestones, orbitron font, dark ink on cream, with a thin 2px accent bar each` 

- `top header: white logo + wordmark with a dark-to-transparent gradient overlay on the top 2 8% for legibility` 

- `generate a true transparent PNG of the logo via Pillow (luminance -> alpha); do NOT use mi x-blend-mode` 

`4. GLOBALS.CSS` 

```
   html/body must use overflow-x:clip, not hidden. Hidden breaks position:sticky everywhere.
```

`5. FONT OVERRIDE` 

```
   If the parent landing has a global !important font override, beat it by writing font-family
with !important on each overlay class in scoped styled-jsx.
```

###### `6. CACHE-BUST` 

```
   Append ?v=N to every video and poster URL. Increment N with every encoder run.
```

```
CRITICAL PITFALLS — don't:
```

- `skip +faststart` 

- `use <source media=...> inside <video>` 

- `scrub on mobile (iOS Safari blanks the element)` 

- `use object-fit: contain with portrait source on landscape monitors` 

- `use mix-blend-mode against a dark gradient` 

- `forget the cache-bust query` 

```
Deliver: cropped + dual-encoded mp4s in public/landing-video/, transparent logo as public/logo-
transparent.png, and CinematicHero.tsx. Tell me when to hard-refresh.
```

NABULINES — cinematic scroll landing — build guide 

page 10 

## **05. Stack & files** 

### **Files touched** 

|**File**|**Role**|
|---|---|
|components/CinematicHero.tsx|The hero component — scrub + autoplay split, overlays, header|
|app/landing-x/page.tsx|Mounts <CinematicHero /> above the existing hero|
|app/globals.css|overflow-x: clip fix for sticky|
|public/landing-video/nabu-landing-desktop.mp4|1080×606, CRF 16, every-frame keyframe (~30 MB)|
|public/landing-video/nabu-landing-mobile.mp4|854×480, Baseline, GOP 5 (~6.3 MB)|
|public/landing-video/nabu-landing-poster.jpg|First-frame poster (~28 KB)|
|public/logo-transparent.png|White glyph on alpha — drop-in header logo|



### **FFmpeg one-liners that did all the work** 

```
# detect crop region of the real 16:9 content
ffmpeg -ss 5 -i SOURCE.mov -vframes 80 -vf cropdetect=24:2:0 -f null -
# sample the cream backdrop color
ffmpeg -y -ss 5 -i SOURCE.mov -vframes 1 -vf "crop=20:20:cx:cy" /tmp/c.png
# desktop encode — native res, near-lossless, every-frame keyframe, faststart
ffmpeg -y -i SOURCE.mov \
  -vf "crop=1080:606:0:420" \
  -c:v libx264 -preset slow -crf 16 -profile:v high -pix_fmt yuv420p \
  -g 1 -keyint_min 1 -sc_threshold 0 \
  -x264-params "keyint=1:min-keyint=1:scenecut=0" \
  -an -movflags +faststart \
  public/landing-video/nabu-landing-desktop.mp4
# mobile encode — Baseline + GOP 5 for iOS
ffmpeg -y -i SOURCE.mov \
  -vf "crop=1080:606:0:420,scale=854:480" \
  -c:v libx264 -preset slow -crf 22 -profile:v baseline -level 3.1 \
  -pix_fmt yuv420p -g 5 -keyint_min 1 -sc_threshold 0 \
  -x264-params "keyint=5:min-keyint=1:scenecut=0" \
  -an -movflags +faststart \
  public/landing-video/nabu-landing-mobile.mp4
```

###### `# poster` 

```
ffmpeg -y -ss 0 -i SOURCE.mov -vframes 1 -vf "crop=1080:606:0:420" \
  -q:v 2 public/landing-video/nabu-landing-poster.jpg
```

NABULINES — cinematic scroll landing — build guide 

page 11 



<!-- Start of picture text -->
2 ie (—<.o |<br>Wee<br><!-- End of picture text -->

