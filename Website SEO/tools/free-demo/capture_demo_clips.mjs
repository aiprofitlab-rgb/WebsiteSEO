// Records the six lead-preview demos for /en/free-demo/ as short muted clips, names and logos blurred
// in the page before any frame is taken (the same rule as the proof stills: "Not clients · names hidden").
//
//   node tools/free-demo/capture_demo_clips.mjs [vet perfume ...]   (no args = all, plus the phone dive clip)
//   PEEK=1 ...   writes a contact sheet of every 10th frame instead of encoding, for a quick look
//
// Each clip is driven on a paused clock (page.clock + one screenshot per 1/30 s), so the WebGL smoke and water,
// the scrubbed scroll heroes and the vet's idle blink come out the same on every run. Frames land in
// .tmp/free-demo/clips/<name>/ (gitignored). The encodes and the stills go to .tmp/free-demo/src/, where
// tools/free-demo/build_free_demo_assets.py picks them up, hashes them and points the page at them:
//   clip-<name>.mp4     1280x800, the hero laptop and the desktop wall
//   clip-<name>-m.mp4   768x480, the same clip for phones
//   clip-<name>.png     frame 0: the poster shown until the clip plays (and when it can't)
//   tile-<name>.png     the frame the peak's wall shows at rest
//   clip-vet-phone.mp4 / .png   390x844 @2x: the clip the phone version of the peak dives into
//
// The sites are the live Vercel deployments; nothing in their repos is touched. Re-check the blur by eye on the
// sheet after every recapture: a site redeploy can move a name into a new element.
import { chromium } from "../../node_modules/playwright-core/index.mjs";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// fileURLToPath, not URL.pathname: the repo path has spaces, which .pathname leaves as %20
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const FRAMES = path.join(ROOT, ".tmp/free-demo/clips");
const SRC = path.join(ROOT, ".tmp/free-demo/src");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FPS = 30, DUR = 3.0;
const PEEK = !!process.env.PEEK;
const T0 = new Date("2026-10-22T10:30:00+04:00").getTime(); // a Thursday morning in Muscat: every place reads "open"

// The business names, as the pages write them (Arabic diacritics are stripped before matching). \b only
// knows ASCII letters, so the short Arabic "سما" gets explicit Arabic-letter lookarounds instead.
const NAMES = /mansour|منصور|shahama|الشهامه|الشهامة|bustan|بستان|البدع|peekaboo|بيكابو|dukanah|دكانه|دكانة|\bsama\b|(?<![\u0621-\u064A])سما(?![\u0621-\u064A])/i;

const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const lerpPath = (pts, u) => {
  // a smooth pointer path through points, u in 0..1
  const n = pts.length - 1, x = Math.min(n - 1e-6, Math.max(0, u * n)), i = Math.floor(x), f = ease(x - i);
  return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f];
};

// blur: selectors blurred (px), hide: selectors made invisible. Any element whose own text names the
// business is blurred too (scan), so a chat pill or a nav item can't slip through.
const SITES = {
  // the eyes in the dark; nobody moves the pointer, so the cat slow-blinks by itself ~2.6 s after boot
  vet: {
    url: "https://dr-mansour-vet-clinic.vercel.app/", pre: 1.9, tile: 0,
    blur: [["a.brand", 9]],
  },
  // the coal glows and the smoke rises; a hand passes through it ("move your hand in the smoke")
  perfume: {
    url: "https://al-shahama-frankincense.vercel.app/", pre: 3.6, tile: 60,
    blur: [["a.brand", 9]],
    pointer: [[640, 470], [860, 300], [980, 200], [820, 140]],
  },
  // after the intro (its leaves fly into the logo disc, so it is never recorded), a hand strokes the water
  resthouse: {
    url: "https://bustan-al-bida-resort.vercel.app/", pre: 6.5, tile: 70,
    blur: [["#hdr .brand", 9], ["#heroLogo", 12], ["#fab", 7]],
    pointer: [[260, 640], [560, 600], [860, 650], [1080, 700]],
  },
  // the monkey rises behind the wall with his hands over his eyes. Stops before 400 px, where the
  // headline becomes "بيكابو!", the brand name.
  kidsalon: {
    url: "https://peekaboo-kids-salon.vercel.app/", pre: 2.4, tile: 89,
    blur: [["a.brand", 9]],
    scroll: [0, 330],
  },
  // the clay pot's lid lifts, the steam goes up, the dish shows. The headline names the café, so all of
  // it is blurred, as on the proof still.
  cafe: {
    url: "https://dukanah-cafe.vercel.app/", pre: 2.4, tile: 60,
    blur: [["a.brand", 9], ["#lidH", 16]],
    scroll: [0, 520],
  },
  // the butterfly opens its wings and lifts off the fingertip. The giant "sama" behind is the name: hidden.
  salon: {
    url: "https://sama-beauty-barka.vercel.app/", pre: 2.4, tile: 89,
    blur: [["a.brand", 9]], hide: [".hs-word"],
    scroll: [0, 800],
  },
};
// the peak's phone dive: the same vet hero, on a phone
const PHONE = { name: "vet-phone", site: "vet", viewport: { width: 390, height: 844 }, dpr: 2, mobile: true };

async function prepare(page, site) {
  await page.evaluate(({ blur, hide, names }) => {
    const re = new RegExp(names, "i");
    const st = document.createElement("style");
    st.textContent = "*:focus,*:focus-visible{outline:none!important} html{scroll-behavior:auto!important} input{caret-color:transparent}"
      + blur.map(([s, px]) => `${s}{filter:blur(${px}px)!important}`).join("")
      + hide.map((s) => `${s}{visibility:hidden!important}`).join("")
      + ".__apl-blur{filter:blur(7px)!important}";
    document.head.appendChild(st);
    const strip = (s) => s.replace(/[ً-ٰٟ]/g, "");
    for (const e of document.querySelectorAll("body *")) {
      const own = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("");
      const alt = (e.getAttribute("alt") || "") + " " + (e.getAttribute("aria-label") || "");
      if (re.test(strip(own)) || (e.tagName === "IMG" && (re.test(strip(alt)) || /logo/i.test(e.getAttribute("src") || "")))) e.classList.add("__apl-blur");
    }
    document.querySelectorAll("img[loading=lazy]").forEach((i) => (i.loading = "eager"));
    // CSS animations and transitions don't follow the paused clock: step them by hand
    window.__stepCss = (ms) => {
      for (const a of document.getAnimations()) {
        if (!(a instanceof CSSAnimation || a instanceof CSSTransition)) continue;
        if (!a.__held) { a.pause(); a.__held = 1; }
        a.currentTime = (a.currentTime || 0) + ms;
      }
    };
  }, { blur: site.blur || [], hide: site.hide || [], names: NAMES.source });
}

const step = async (page, ms) => { await page.clock.runFor(ms); await page.evaluate((ms) => __stepCss(ms), ms); };

async function record(browser, name, site, opts = {}) {
  const vp = opts.viewport || { width: 1280, height: 800 };
  const ctx = await browser.newContext({
    viewport: vp, deviceScaleFactor: opts.dpr || 1, isMobile: !!opts.mobile, hasTouch: !!opts.mobile, timezoneId: "Asia/Muscat",
  });
  await ctx.addInitScript(() => {
    window.open = () => ({});
    let s = 20261026; Math.random = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("  page error:", name, e.message));
  await page.clock.install({ time: T0 });
  await page.clock.pauseAt(T0 + 500);
  await page.goto(site.url, { waitUntil: "load", timeout: 90000 }).catch((e) => console.log("  goto:", e.message));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1500);            // real time for images and the WebGL plates to decode
  await prepare(page, site);
  for (let t = 0; t < site.pre * 1000; t += 50) await step(page, 50);
  await page.waitForTimeout(400);

  const dir = path.join(FRAMES, name);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  const N = Math.round(DUR * FPS);
  for (let f = 0; f < N; f++) {
    const u = f / (N - 1);
    if (site.scroll && !opts.mobile) await page.evaluate((y) => scrollTo(0, y), Math.round(site.scroll[0] + (site.scroll[1] - site.scroll[0]) * ease(u)));
    if (site.pointer && !opts.mobile) { const [x, y] = lerpPath(site.pointer, u); await page.mouse.move(x, y, { steps: 2 }); }
    await step(page, 1000 / FPS);
    if (!PEEK || f % 10 === 0) await page.screenshot({ path: path.join(dir, `f${String(f).padStart(3, "0")}.jpg`), type: "jpeg", quality: 92 });
  }
  await ctx.close();
  return dir;
}

function ffmpeg(args) { execFileSync("ffmpeg", ["-hide_banner", "-loglevel", "error", "-y", "-nostdin", ...args], { stdio: "inherit" }); }

function encode(name, dir, tile, phone) {
  fs.mkdirSync(SRC, { recursive: true });
  const inp = ["-framerate", String(FPS), "-i", path.join(dir, "f%03d.jpg")];
  const x264 = (crf) => ["-c:v", "libx264", "-preset", "slow", "-crf", String(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an"];
  if (phone) {
    ffmpeg([...inp, "-vf", "scale=540:-2:flags=lanczos", ...x264(28), path.join(SRC, `clip-${name}.mp4`)]);
  } else {
    ffmpeg([...inp, "-vf", "scale=1280:800:flags=lanczos", ...x264(27), path.join(SRC, `clip-${name}.mp4`)]);
    ffmpeg([...inp, "-vf", "scale=768:480:flags=lanczos", ...x264(28), path.join(SRC, `clip-${name}-m.mp4`)]);
    ffmpeg(["-i", path.join(dir, `f${String(tile).padStart(3, "0")}.jpg`), path.join(SRC, `tile-${name}.png`)]);
  }
  ffmpeg(["-i", path.join(dir, "f000.jpg"), path.join(SRC, `clip-${name}.png`)]);
  for (const f of fs.readdirSync(SRC).filter((f) => f.startsWith(`clip-${name}`) && f.endsWith(".mp4")))
    console.log(`  ${f.padEnd(26)} ${Math.round(fs.statSync(path.join(SRC, f)).size / 1024)} KB`);
}

function sheet(name, dir) {
  // every 10th frame in one image, to check the blur and the motion by eye
  const out = path.join(FRAMES, `${name}-sheet.jpg`);
  ffmpeg(["-pattern_type", "glob", "-i", path.join(dir, "f*0.jpg"), "-vf", "scale=480:-2,tile=3x3:padding=6", "-frames:v", "1", out]);
  console.log("  sheet", path.relative(ROOT, out));
}

const want = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--use-angle=metal"] });
for (const [name, site] of Object.entries(SITES)) {
  if (want.length && !want.includes(name)) continue;
  console.log(name);
  const dir = await record(browser, name, site);
  sheet(name, dir);
  if (!PEEK) encode(name, dir, site.tile, false);
}
if (!want.length || want.includes(PHONE.name)) {
  console.log(PHONE.name);
  const dir = await record(browser, PHONE.name, SITES[PHONE.site], PHONE);
  sheet(PHONE.name, dir);
  if (!PEEK) encode(PHONE.name, dir, 0, true);
}
await browser.close();
