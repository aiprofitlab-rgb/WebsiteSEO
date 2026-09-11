#!/usr/bin/env python3
"""Prove the QR subsystem in tools/v4/qr_js.py still works.

    python3 tools/verify_qr.py           # everything
    python3 tools/verify_qr.py --quick   # skip the browser pass

Four checks, in increasing order of what they cover:

  1. Every matrix, compared to segno module for module - all 40 versions at
     all 4 error-correction levels, with the payload filling the symbol
     exactly. Exact-fill because segno appends one spurious zero codeword
     whenever the bit stream is already byte-aligned after the terminator, so
     byte-equality is only meaningful where its quirk cannot fire. This check
     covers the block tables, the Reed-Solomon remainder, interleaving,
     alignment positions, format and version bits, the zigzag walk, AND mask
     selection.
  2. The reader, pointed at segno's own matrices for the same 160
     combinations. A shared bug between our writer and our reader would
     survive check 3 and die here.
  3. Round-trip: our encoder to our reader, over payload lengths and scripts
     the tool actually sees, including Arabic.
  4. The art itself: rendered in Chromium exactly as the page renders it, then
     decoded off the pixels with OpenCV. This is the only check that sees the
     rounded corners, the gold eyes, the centre plate and the palettes.

Dev-only dependencies. Anything missing is reported and skipped, not faked:
segno and opencv-python for 1, 2 and 4; node for 1-3; playwright for 4.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "v4"))
import qr_js  # noqa: E402

LEVELS = "lmqh"
ARABIC = ("مرحباً، أريد أن "
          "أسأل عن أسعاركم "
          "ومواعيد التسليم.")

HARNESS = """
%s
%s
module.exports = { QR: QR, ART: ART };
""" % (qr_js.CODEC_JS, qr_js.ART_JS)

BROWSER_PAGE = """<!doctype html><meta charset="utf-8"><body><canvas id="cv"></canvas>
<script>%s</script><script>%s</script>
<script>
window.RUN = function(cases, logo){
  var cv = document.getElementById("cv");
  return cases.map(function(t){
    var sym = ART.symbolFor(t.text);
    if (!sym) return {ok:false};
    var fit = ART.fit(cv, sym, t.pal, logo);
    ART.canvas(cv, sym, t.pal, fit.plate, logo, 10);
    return {ok:true, ver:sym.ver, ecl:sym.ecl, plate:fit.plate,
            headroom:fit.check.headroom,
            png:cv.toDataURL("image/png").split(",")[1]};
  });
};
</script></body>""" % (qr_js.CODEC_JS, qr_js.ART_JS)


def have(mod):
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


def node(script, cwd):
    r = subprocess.run(["node", "-e", script], cwd=cwd, capture_output=True, text=True,
                       env={**os.environ, "NODE_PATH": str(ROOT / "node_modules")})
    if r.returncode:
        print(r.stderr.strip()[:2000])
        raise SystemExit("node failed")
    return r.stdout


def main():
    quick = "--quick" in sys.argv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="verify-qr-"))
    (tmp / "qr.js").write_text(HARNESS, encoding="utf-8")
    fails = 0

    if not subprocess.run(["node", "-v"], capture_output=True).returncode == 0:
        print("!! node not found - checks 1 to 3 skipped")
        return 1

    caps = json.loads(node(
        "var q=require('./qr.js').QR;var o=[];"
        "for(var v=1;v<=40;v++)o.push([0,1,2,3].map(function(e){return q.capacityBytes(v,e);}));"
        "console.log(JSON.stringify(o));", tmp))

    # ---- 1 and 2: against segno -------------------------------------------
    if not have("segno"):
        print(".. segno not installed - checks 1 and 2 skipped")
    else:
        import random
        import segno
        import string
        random.seed(20260910)
        cases, refs = [], []
        for v in range(1, 41):
            for e in range(4):
                txt = "".join(random.choice(string.ascii_letters + string.digits)
                              for _ in range(caps[v - 1][e]))
                qr = segno.make(txt, error=LEVELS[e], mode="byte", encoding="utf-8",
                                boost_error=False, micro=False)
                cases.append({"text": txt, "ecl": e})
                refs.append((v, e, txt, [",".join(str(b) for b in row) for row in qr.matrix], qr))
        (tmp / "cases.json").write_text(json.dumps(cases))
        got = json.loads(node(
            "var q=require('./qr.js').QR,fs=require('fs');"
            "var c=JSON.parse(fs.readFileSync('cases.json','utf8'));"
            "console.log(JSON.stringify(c.map(function(p){"
            "var s=q.encode(p.text,p.ecl,null,null);"
            "return {ver:s.ver,mask:s.mask,rows:s.mods.map(function(r){return Array.prototype.join.call(r,',');})};"
            "})));", tmp))
        bad = 0
        for (v, e, txt, ref, qr), g in zip(refs, got):
            if g["ver"] != v or g["mask"] != qr.mask or g["rows"] != ref:
                bad += 1
                print("   FAIL v%d-%s (version %s/%s, mask %s/%s)"
                      % (v, LEVELS[e].upper(), g["ver"], v, g["mask"], qr.mask))
        fails += bad
        print("1. matrices identical to segno            %3d/160%s"
              % (160 - bad, "" if not bad else "   <-- FAILED"))

        # the reader, over segno's matrices
        payloads = [(r[3], r[0], r[1], r[4].mask, r[2]) for r in refs]
        (tmp / "read.json").write_text(json.dumps(
            [{"rows": p[0], "ver": p[1], "ecl": p[2], "mask": p[3]} for p in payloads]))
        out = json.loads(node(
            "var q=require('./qr.js').QR,fs=require('fs');"
            "var c=JSON.parse(fs.readFileSync('read.json','utf8'));"
            "console.log(JSON.stringify(c.map(function(d){"
            "var m=d.rows.map(function(r){return Uint8Array.from(r.split(',').map(Number));});"
            "var x=q.read(m,d.ver,d.ecl,d.mask);"
            "return x?Buffer.from(x.bytes).toString('utf8'):null;})));", tmp))
        bad = sum(1 for p, o in zip(payloads, out) if o != p[4])
        fails += bad
        print("2. reader reads segno's matrices          %3d/160%s"
              % (160 - bad, "" if not bad else "   <-- FAILED"))

    # ---- 3: round-trip ----------------------------------------------------
    trip = []
    for n in (1, 2, 17, 100, 400, 1200, 2600):
        for e in range(4):
            trip.append({"text": ("A" * n), "ecl": e})
            trip.append({"text": (ARABIC * (n // len(ARABIC) + 1))[:n], "ecl": e})
    (tmp / "trip.json").write_text(json.dumps(trip, ensure_ascii=False), encoding="utf-8")
    res = json.loads(node(
        "var q=require('./qr.js').QR,fs=require('fs');"
        "var c=JSON.parse(fs.readFileSync('trip.json','utf8'));"
        "console.log(JSON.stringify(c.map(function(p){"
        "var s=q.encode(p.text,p.ecl,null,null); if(!s) return 'OVER';"
        "var r=q.read(s.mods,s.ver,s.ecl,s.mask);"
        "return r?Buffer.from(r.bytes).toString('utf8'):null;})));", tmp))
    checked = [(t, r) for t, r in zip(trip, res) if r != "OVER"]
    bad = sum(1 for t, r in checked if r != t["text"])
    fails += bad
    print("3. round-trip, ASCII and Arabic           %3d/%-3d%s"
          % (len(checked) - bad, len(checked), "" if not bad else "   <-- FAILED"))

    # ---- 4: the art, in a browser, decoded by OpenCV ----------------------
    if quick:
        print("4. styled art in Chromium                 skipped (--quick)")
    elif not (have("cv2") and (ROOT / "node_modules" / "playwright").exists()):
        print(".. opencv-python or playwright missing - check 4 skipped")
    else:
        import base64
        import io
        import cv2
        import numpy as np
        from PIL import Image
        (tmp / "page.html").write_text(BROWSER_PAGE, encoding="utf-8")
        cases = []
        for msg in ("", "Hello, I would like to place an order.", ARABIC,
                    "See a/b + c (50%) & more!", ARABIC * 3):
            url = "https://wa.me/96899245250"
            if msg:
                import urllib.parse
                url += "?text=" + urllib.parse.quote(msg, safe="")
            for pal in ("cream", "dark", "mono"):
                cases.append({"text": url, "pal": pal})
        (tmp / "cases2.json").write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
        (tmp / "run.js").write_text("""
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const cases = JSON.parse(fs.readFileSync('cases2.json','utf8'));
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + process.cwd() + '/page.html');
  const out = await p.evaluate(([c,l]) => window.RUN(c,l), [cases, %s]);
  fs.writeFileSync('out2.json', JSON.stringify(out)); await b.close();
})();""" % json.dumps(qr_js.LOGO_PATH), encoding="utf-8")
        r = subprocess.run(["node", "run.js"], cwd=tmp, capture_output=True, text=True,
                           env={**os.environ, "NODE_PATH": str(ROOT / "node_modules")})
        if r.returncode:
            print(r.stderr.strip()[:1500])
            raise SystemExit("browser render failed")
        out = json.loads((tmp / "out2.json").read_text())
        det = cv2.QRCodeDetectorAruco()
        bad, worst = 0, 1.0
        for c, o in zip(cases, out):
            if not o["ok"]:
                bad += 1
                continue
            img = np.array(Image.open(io.BytesIO(base64.b64decode(o["png"]))).convert("L"))
            # the dark palette is an inverted symbol; OpenCV cannot read those,
            # so it is handed the flip. That limitation is why the page warns.
            if c["pal"] == "dark":
                img = 255 - img
            if det.detectAndDecode(img)[0] != c["text"]:
                bad += 1
                print("   FAIL %s v%d" % (c["pal"], o["ver"]))
            worst = min(worst, o["headroom"])
        fails += bad
        print("4. styled art rendered and decoded        %3d/%-3d   (lowest headroom kept %.0f%%)%s"
              % (len(cases) - bad, len(cases), worst * 100, "" if not bad else "   <-- FAILED"))

    print()
    print("ALL CHECKS PASSED" if not fails else "%d FAILURE(S)" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
