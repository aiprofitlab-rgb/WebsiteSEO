# Cinematic Hero — Asset Prompt Pack

**Sequence:** a humanoid robot becomes a human assistant and starts working.
**Used by:** `public_html/en/index-cinematic.html` (scroll-scrubbed image sequence).
**Brand:** AI Profit Lab Brand Playbook v2 — cream `#F1EFE8`, teal `#0F6E56`, amber `#BA7517`.

---

## Guardrail — read before generating

The figure that emerges is **the AI assistant, not the founder and not a client.**

- Never give the figure a name, a job title, a quote, or a testimonial.
- Never place it in a context implying it is a real employee or a real customer.
- Keep the face three-quarter / soft-focus from scene 05 onward. It is a depiction of the product, not a portrait of a person.

The Playbook's imagery rule is *"real founder photography and real client/product photography — never generic stock."* This sequence sits inside that rule only because it illustrates the system itself. The founder photo and the working demo tools directly below the hero remain the trust layer.

---

## Pipeline

```
7 keyframe images  →  6 Kling clips (start+end frame)  →  assemble ~28s mp4
                   →  tools/build_cinematic_frames.py --from-video
                   →  public_html/assets/cinematic/{desktop,mobile}/*.webp
```

Frame count and compression are handled by the script. The video export only has to be clean, not optimised.

---

# A. Image prompts — 7 keyframes

Generate with **Nano Banana (Gemini)** or **ChatGPT / gpt-image-1**. 16:9.

## Global style string — prepend to every prompt

> minimal futuristic editorial photography, a clean seamless warm cream off-white background (#F1EFE8) filling the entire frame edge to edge, no floor, no wall, no horizon line, no table — pure floating cream void, soft directional daylight from the upper left, gentle warm shadows, restrained palette of cream and warm off-white with deep teal (#0F6E56) accents and a single amber (#BA7517) light source, absolutely no blue or cyan tones, no neon, no circuit-board patterns, no glowing eyes, no sci-fi clutter, shallow depth of field, ultra detailed, 8k, calm and expensive, generous negative space with clear empty space above the subject reserved for a logo, 16:9 aspect ratio.

## Consistency rule — this is what decides whether it works

Generate scene 01 first. **From scene 02 onward, upload the previous scene as a reference image** and open the prompt with:

> USING THE UPLOADED REFERENCE IMAGE — keep the EXACT same figure: same proportions, same height, same shell material and colour, same amber chest dot position, same camera distance and eye level, same cream background, same lighting direction. Do not change the body shape or the framing. ONLY change what is described below.

Consistency of the figure across seven frames is the single hardest part of this build. Do not skip the reference chaining.

---

### 01 · STANDBY

> a single humanoid robot standing centered in the cream void, matte pearl-white ceramic shell with soft rounded panels and fine visible seams, smooth blank visor instead of a face with no eyes and no mouth, head slightly bowed in a powered-down rest pose, arms relaxed at its sides, a single small amber light dot glowing at the centre of its chest — the only warm light in the entire frame, faint teal reflection along the panel edges, fine dust suspended in the soft light, deep negative space above the head, the robot is the only subject, hero product shot.

### 02 · WAKE

> the same robot in the same pose, but the amber chest dot has brightened and now casts a soft warm pool of light onto its chest and forearms, thin teal light is tracing along the seams of the shell like current finding a path, the head has lifted to face the camera directly, the visor catches a faint teal sheen, shoulders settling as if a held breath has just been released, dust motes drifting through the warm light, still calm and still, nothing violent.

### 03 · FRACTURE

> the same robot facing the camera, its ceramic shell panels are separating and lifting away from the body along the seams, floating outward a short distance and hanging suspended in mid-air, the panel edges dissolving into fine amber particles and thin teal light filaments that drift upward, beneath the lifted panels there is warm light rather than machinery, the silhouette of the figure stays intact and recognisable throughout, slow and graceful, no explosion, no debris, no violence, the figure holds its centre.

### 04 · THRESHOLD

> the same figure at the exact midpoint of transformation, the left side of the body still matte pearl-white ceramic shell, the right side already warm human — real skin, a simple soft off-white cotton shirt with natural fabric folds, the boundary between the two is not a hard line but a drifting band of amber particles and teal light filaments reorganising themselves, the amber chest dot has migrated and now reads as warm light at the centre of the human chest, the face still partly obscured by the last of the dissolving visor, poised and unhurried.

### 05 · THE ASSISTANT

> a real human figure standing in the cream void where the robot was, same height, same stance, same camera distance — a calm, capable professional assistant in a simple soft off-white cotton shirt with sleeves rolled once, warm natural skin, relaxed shoulders, hands loose at the sides, head turned slightly away from the camera in a three-quarter view so the face is soft and not the focus of the frame, gentle amber rim light along one shoulder, the last few amber particles still dissolving in the air around the figure, quiet competence, editorial portrait lighting, not a stock-photo smile.

### 06 · THE DESK

> the same human figure now turning and settling into a simple seat at a minimal desk that is materialising out of the cream void beneath a soft warm glow — the desk is a plain pale surface with no legs visible and no room around it, still a floating cream void, a slim phone and a single thin screen are resolving into existence on the desk surface, the figure's hands are reaching toward them, warm amber light from the screen beginning to catch the face and forearms in three-quarter view, teal accent light along the desk edge, calm and deliberate, no clutter, no keyboard, no coffee cup, no plants.

### 07 · AT WORK

> the same human figure seated at the same minimal floating desk, now working — one hand on the phone, eyes on the thin screen in three-quarter view, the screen glowing softly with abstract teal and amber interface shapes and no readable text, small soft-edged cards of light floating in the air above the desk suggesting messages being answered and figures updating, warm amber light on the face and hands, a faint teal glow along the desk edge, dust motes drifting through the warm light, the pose is relaxed and unhurried — someone who has this handled, generous clear space above for a logo.

---

## Avoid list — append to any prompt that drifts

> no blue or cyan lighting, no neon, no cyberpunk, no circuit boards, no glowing eyes, no exposed wires or metal endoskeleton, no crowded background, no office set, no lens flare, no text or letters anywhere in the image, no stock-photo smiling, no logos.

---

# B. Motion prompts — Kling 3.0, 6 clips

**Settings for every clip:** Start Frame = scene N · End Frame = scene N+1 · Duration 5s · Motion Strength 3/10 (raise to 5/10 for clip 03 only) · camera locked static, no pan, no zoom.

If a clip morphs the body shape or drifts the framing, regenerate. Expect 3–5 attempts on clips 03 and 04 — those are the transformation beats and the most likely to distort.

### Clip 01 · Standby → Wake (scenes 1→2)

> the amber dot at the robot's chest slowly brightens and begins to pulse gently like a slow heartbeat, thin teal light traces along the shell seams spreading outward from the chest, the bowed head lifts smoothly to face the camera, the shoulders settle slightly, dust motes drift slowly through the warm light, camera locked static with no pan or zoom, slow cinematic ease-out as the head reaches its final position, calm and quiet, sharp focus throughout, 16:9.

### Clip 02 · Wake → Fracture (scenes 2→3)

> the ceramic shell panels begin to separate along the seams and lift gently away from the body, floating outward and settling suspended in mid-air, panel edges dissolving into fine amber particles that drift slowly upward, thin teal light filaments trail behind each floating panel, warm light spills from beneath the lifted panels, the figure's silhouette stays fully intact and centred throughout with no morphing of the body shape, camera locked static, slow motion, graceful not violent, no explosion, sharp focus throughout, 16:9.

### Clip 03 · Fracture → Threshold (scenes 3→4) — *Motion Strength 5/10*

> the suspended panels dissolve completely into drifting amber particles, the particle cloud sweeps across the body from right to left reorganising as it travels, warm human skin and soft cotton fabric resolving in its wake on the right side of the body while the left side remains ceramic shell, the boundary between machine and human is a soft drifting band of amber particles and teal filaments, never a hard edge, the amber chest light migrates smoothly to the centre of the human chest, the figure holds its exact position and proportions throughout with no morphing of height or stance, camera locked static, slow-motion magical realism, sharp focus throughout, 16:9.

### Clip 04 · Threshold → The Assistant (scenes 4→5)

> the transformation completes as the particle band sweeps off the left edge of the body, the remaining ceramic shell resolves into warm skin and soft off-white cotton shirt, the last of the visor dissolves revealing a calm human face turned three-quarters away from the camera, the final amber particles drift upward and fade out of frame, the shoulders relax and settle, a gentle amber rim light settles along one shoulder, the figure holds the same height, same stance, and same camera distance as the start frame, camera locked static, slow ease-out into stillness, quiet and unhurried, sharp focus throughout, 16:9.

### Clip 05 · The Assistant → The Desk (scenes 5→6)

> the human figure turns smoothly toward the desk and settles into a seated position, a minimal pale desk surface materialises beneath a soft warm glow rising from below, a slim phone and a single thin screen resolve into existence on the desk surface fading in from the cream void, the figure's hands reach toward them unhurried, warm amber light from the screen begins to catch the face and forearms, a teal accent light traces along the desk edge, the background stays a pure empty cream void with no room and no walls appearing, camera locked static, slow deliberate motion, sharp focus throughout, 16:9.

### Clip 06 · The Desk → At Work (scenes 6→7)

> the seated figure begins working, one hand settling onto the phone and eyes moving to the screen, the screen fills with softly glowing abstract teal and amber interface shapes with no readable text, small soft-edged cards of light fade in one by one and float gently in the air above the desk suggesting messages being answered, warm amber light steadies on the face and hands, dust motes drift slowly through the light, the figure's posture stays relaxed and unhurried throughout, the loop settles into a calm steady rhythm at the end, camera locked static, slow-motion editorial, sharp focus throughout, 16:9.

---

# C. Assembly & handoff

**CapCut or Premiere:**

- 6 clips in order, no gaps, no overlap
- 0.3s Cross Dissolve between each pair
- Export: 1920×1080 · 30fps · H.264 (MP4) · muted · ~28s total

**Then:**

```bash
python3 tools/build_cinematic_frames.py --from-video /path/to/assembled.mp4
python3 tools/build_cinematic_frames.py --report
```

That writes 90 desktop frames, 45 mobile frames and a poster into `public_html/assets/cinematic/`, replacing the placeholders. No page code changes are needed — the swap is pure assets.

---

# D. Overlay copy locked to the sequence

The page overlays are timed to these scenes. Copy is fixed in the page; listed here so image generation keeps the matching areas of frame clear.

| Scroll | Overlay | Keep clear |
|---|---|---|
| 0 → 0.14 | "Never lose a buyer to silence again." | centre of frame |
| 0.16 | 9:47 PM. A buyer asks if you deliver to Sohar. | right third |
| 0.28 | Your office closed four hours ago. | left third |
| 0.40 | Something answers anyway. | right third |
| 0.52 | It knows your stock. It knows your delivery times. | left third |
| 0.64 | It books the order and logs the lead. | right third |
| 0.76 | You read about it in the morning. | left third |
| 0.88 → 1.0 | "Every success starts with insight." + CTA | lower centre |

Keep the figure **centred** and the **upper third empty** in every scene — the wordmark sits top-left and the side beats need the outer thirds.
