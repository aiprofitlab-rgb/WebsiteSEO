#!/usr/bin/env python3
"""Score reels with a TRIBE v2 brain-response model on Replicate, into .tmp/brain/<date>/.

The model (prakhar-bhartiya/meta-tribev2-social-media-content-signal) predicts
how an average viewer's cortex responds to each moment of a clip, then folds
that into a 0-100 headline score, five sub-scores (reward, emotion, attention,
social relevance, novelty) and a ~2 Hz timeline. It is a test of whether brain
scores track how our reels actually did, before we build our own on a rented GPU.

Read this before trusting a number:
  - TRIBE v2 weights are CC BY-NC 4.0 (non-commercial). Fine for this test;
    never put the scores in a paid client deliverable.
  - It is someone else's community wrapper (~160 runs when this was written),
    so its scoring formula is theirs, not ours.
  - With fewer than ~8 reels a correlation is noise. The script says so.

Token: REPLICATE_API_TOKEN, read from ~/.config/aiprofitlab/replicate.env
(KEY=value lines), outside the repo on purpose, or from the environment, which
wins. It is never printed or written; every error message is scrubbed.

Cost: public Replicate models bill only the seconds the prediction runs, on an
L40S at $0.000975/s. One sample run took ~172 s (~$0.17); a 15 s clip should be
cheaper. Each row of results.csv carries its own cost from predict_time.

Usage:
    python3 tools/reel_brain_score.py a.mp4 b.mp4             # first 15 s of each
    python3 tools/reel_brain_score.py a.mp4 --seconds 60      # the model's max
    python3 tools/reel_brain_score.py *.mp4 --metrics m.csv   # + correlation
    python3 tools/reel_brain_score.py *.mp4 --dry-run         # trim only, no API, no cost

--metrics is a CSV with a `file` column (the clip's file name) and any numeric
columns you have from Instagram Insights, e.g. views, avg_watch_s, shares.
--dry-run writes metrics_template.csv with those columns empty, ready to fill.

Output (.tmp/brain/<YYYY-MM-DD>/):
    clips/<name>.mp4        the trimmed upload (short side 720 px, silent track added if none)
    raw/<name>.json         full model output, timeline included
    results.csv             one row per clip: scores, predict time, cost
    correlation.txt         Spearman rank correlation of each score with each metric
"""

import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_FILE = pathlib.Path.home() / ".config" / "aiprofitlab" / "replicate.env"
API = "https://api.replicate.com/v1"
MODEL = "prakhar-bhartiya/meta-tribev2-social-media-content-signal"
L40S_PER_SECOND = 0.000975
MAX_SECONDS = 60          # the model rejects longer clips
METRIC_COLUMNS = ["views", "reach", "avg_watch_s", "likes", "comments", "shares", "saved"]

# Prefer the pinokio build (newer, has every codec); fall back to whatever is on PATH.
FFMPEG = next((p for p in ("/Users/nahid/pinokio/bin/miniconda/bin/ffmpeg", shutil.which("ffmpeg"))
               if p and os.path.exists(p)), None)
FFPROBE = next((p for p in ("/Users/nahid/pinokio/bin/miniconda/bin/ffprobe", shutil.which("ffprobe"))
                if p and os.path.exists(p)), None)


# --------------------------------------------------------------------------- token

def load_token():
    if os.environ.get("REPLICATE_API_TOKEN"):
        return os.environ["REPLICATE_API_TOKEN"]
    if TOKEN_FILE.exists():
        for line in TOKEN_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("REPLICATE_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


# --------------------------------------------------------------------------- http

class Replicate:
    """Minimal Replicate client. Raises RuntimeError with a scrubbed message."""

    def __init__(self, token):
        self.token = token

    def _scrub(self, text):
        return str(text).replace(self.token, "<token>") if self.token else str(text)

    def _call(self, method, url, body=None, headers=None):
        headers = {"Authorization": f"Bearer {self.token}", **(headers or {})}
        for attempt in range(4):
            req = urllib.request.Request(url, data=body, method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                text = e.read().decode(errors="replace")
                # 429 = throttled, 5xx = Replicate hiccup: wait and retry.
                if (e.code == 429 or e.code >= 500) and attempt < 3:
                    time.sleep(10 * (attempt + 1))
                    continue
                raise RuntimeError(self._scrub(f"{method} {url} -> HTTP {e.code}: {text[:400]}"))
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < 3:
                    time.sleep(5)
                    continue
                raise RuntimeError(self._scrub(f"{method} {url} -> {e}"))

    def get(self, path):
        return self._call("GET", path if path.startswith("http") else f"{API}{path}")

    def post_json(self, path, payload):
        return self._call("POST", f"{API}{path}", json.dumps(payload).encode(),
                          {"Content-Type": "application/json"})

    def upload(self, path):
        """POST /files as multipart; returns the URL a prediction input can point at."""
        boundary = uuid.uuid4().hex
        head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"content\"; "
                f"filename=\"{path.name}\"\r\nContent-Type: video/mp4\r\n\r\n").encode()
        body = head + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        r = self._call("POST", f"{API}/files", body,
                       {"Content-Type": f"multipart/form-data; boundary={boundary}"})
        return r["urls"]["get"]


# --------------------------------------------------------------------------- clips

def probe(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    kinds = {s.get("codec_type") for s in info.get("streams", [])}
    return float(info["format"]["duration"]), "audio" in kinds


def trim(src, dst, seconds):
    """First `seconds` of src, short side 720 px, H.264/AAC. Adds a silent track if
    the clip has none, so the audio encoder always gets input (our old reels were
    posted silent, with music added in the Instagram app)."""
    duration, has_audio = probe(src)
    length = min(seconds, duration, MAX_SECONDS)
    scale = "scale='if(gt(iw,ih),-2,720)':'if(gt(iw,ih),720,-2)'"
    cmd = [FFMPEG, "-y", "-v", "error", "-t", f"{length:.2f}", "-i", str(src)]
    if not has_audio:
        cmd += ["-f", "lavfi", "-t", f"{length:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0",
            "-vf", scale, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)
    return length, has_audio


# --------------------------------------------------------------------------- scoring

def score(rep, version, clip, timeout_s):
    url = rep.upload(clip)
    pred = rep.post_json("/predictions", {"version": version, "input": {"video": url}})
    started = time.time()
    while pred.get("status") not in ("succeeded", "failed", "canceled"):
        if time.time() - started > timeout_s:
            rep._call("POST", pred["urls"]["cancel"])
            raise RuntimeError(f"timed out after {timeout_s}s (cancelled; a cold boot can take minutes)")
        time.sleep(5)
        pred = rep.get(pred["urls"]["get"])
    if pred["status"] != "succeeded":
        raise RuntimeError(f"prediction {pred['status']}: {str(pred.get('error'))[:300]}")
    return pred


# --------------------------------------------------------------------------- correlation

def ranks(values):
    """Average ranks, so ties share a rank (Spearman's convention)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    r = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = sum((a - mx) ** 2 for a in rx) ** 0.5
    sy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (sx * sy) if sx and sy else float("nan")


def correlate(rows, metrics_path):
    with open(metrics_path, newline="") as f:
        metrics = {pathlib.Path(m["file"]).stem: m for m in csv.DictReader(f)}
    score_cols = [c for c in rows[0] if c == "headline_score" or c.startswith("sub_")]
    lines = []
    metric_cols = [c for c in next(iter(metrics.values())) if c != "file"] if metrics else []
    for mc in metric_cols:
        pairs = []
        for row in rows:
            m = metrics.get(row["clip"])
            try:
                pairs.append((row, float(m[mc])))
            except (TypeError, ValueError, KeyError):
                continue
        if len(pairs) < 3:
            continue
        lines.append(f"\n{mc}  (n={len(pairs)}{', too few to mean anything' if len(pairs) < 8 else ''})")
        for sc in score_cols:
            rho = spearman([float(r[sc]) for r, _ in pairs], [v for _, v in pairs])
            lines.append(f"  {sc:<28} rho = {rho:+.2f}")
    return "\n".join(lines) or "No metric column had 3+ numeric values matching the clips."


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("videos", nargs="+", type=pathlib.Path)
    ap.add_argument("--seconds", type=float, default=15, help=f"score the first N seconds (max {MAX_SECONDS})")
    ap.add_argument("--metrics", type=pathlib.Path, help="CSV of real Instagram numbers per clip")
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait per prediction")
    ap.add_argument("--dry-run", action="store_true", help="trim and plan only; no API calls, no cost")
    args = ap.parse_args()

    if not (FFMPEG and FFPROBE):
        sys.exit("ffmpeg/ffprobe not found.")
    missing = [str(v) for v in args.videos if not v.is_file()]
    if missing:
        sys.exit("Not found: " + ", ".join(missing))
    stems = [v.stem for v in args.videos]
    if len(set(stems)) != len(stems):
        sys.exit("Two clips share a file name; rename one so results don't overwrite each other.")

    out = ROOT / ".tmp" / "brain" / dt.date.today().isoformat()
    (out / "clips").mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir(parents=True, exist_ok=True)

    clips = []
    for v in args.videos:
        dst = out / "clips" / f"{v.stem}.mp4"
        length, had_audio = trim(v, dst, args.seconds)
        clips.append((v, dst, length, had_audio))
        print(f"  {v.name}: {length:.1f}s{'' if had_audio else ' (no audio, silent track added)'}"
              f", {dst.stat().st_size / 1e6:.1f} MB")

    if args.dry_run:
        tpl = out / "metrics_template.csv"
        with open(tpl, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["file"] + METRIC_COLUMNS)
            for v, *_ in clips:
                w.writerow([v.name] + [""] * len(METRIC_COLUMNS))
        print(f"\nDry run: {len(clips)} clips trimmed into {out / 'clips'}.")
        print(f"Fill in {tpl} from Instagram Insights, then rerun without --dry-run.")
        print(f"Rough cost: {len(clips)} x ~$0.05-0.20 = ${0.05 * len(clips):.2f}-${0.20 * len(clips):.2f}")
        return

    token = load_token()
    if not token:
        sys.exit(f"No REPLICATE_API_TOKEN. Put REPLICATE_API_TOKEN=... in {TOKEN_FILE}.")
    rep = Replicate(token)
    version = rep.get(f"/models/{MODEL}")["latest_version"]["id"]

    rows, spent = [], 0.0
    for v, clip, length, had_audio in clips:
        print(f"Scoring {v.name} ...", flush=True)
        try:
            pred = score(rep, version, clip, args.timeout)
        except RuntimeError as e:
            print(f"  failed: {e}")
            continue
        o = pred["output"]
        (out / "raw" / f"{v.stem}.json").write_text(json.dumps(
            {"source": str(v), "seconds_scored": length, "prediction_id": pred["id"],
             "metrics": pred.get("metrics"), "output": o}, indent=2))
        predict_s = (pred.get("metrics") or {}).get("predict_time") or 0
        cost = predict_s * L40S_PER_SECOND
        spent += cost
        row = {"clip": v.stem, "seconds_scored": round(length, 1), "had_audio": had_audio,
               "headline_score": o["headline_score"]}
        row.update({f"sub_{k}": val for k, val in sorted(o["sub_scores"].items())})
        row.update({"predict_s": round(predict_s, 1), "cost_usd": round(cost, 4),
                    "scoring_version": o.get("scoring_version")})
        rows.append(row)
        subs = ", ".join(f"{k} {val}" for k, val in sorted(o["sub_scores"].items()))
        print(f"  {o['headline_score']}/100  ({subs})  {predict_s:.0f}s, ${cost:.3f}")

    if not rows:
        sys.exit("Nothing scored.")
    with open(out / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)}/{len(clips)} scored, ~${spent:.2f} total. Results: {out / 'results.csv'}")

    if args.metrics:
        report = correlate(rows, args.metrics)
        (out / "correlation.txt").write_text(report + "\n")
        print(report)


if __name__ == "__main__":
    main()
