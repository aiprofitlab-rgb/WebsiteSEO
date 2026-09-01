/**
 * Files the admin panel uploads, and the public URL a follower clicks.
 *
 * WHY A LINK AND NOT AN ATTACHMENT. Meta allows exactly one private reply per
 * comment, ever. A real attachment would have to be its own message, which
 * would mean either the text or the file — never both — and no follow-up is
 * possible. So an uploaded PDF becomes a URL that rides along inside the one
 * message we are allowed to send. It is also the only form that works for every
 * file type: Instagram's send API does not accept arbitrary documents the way
 * Messenger's does.
 *
 * The store is deliberately dumb: bytes in a directory, metadata encoded in the
 * filename. No database table, because the interesting failure here is not a
 * lost row — it is a directory that does not survive a redeploy, and the fix
 * for that is the path, not the schema. Uploads live beside the SQLite file and
 * the token, under /var/lib/ig-automation, which DEPLOY.md's rsync excludes.
 *
 * URLs are unguessable (16 random bytes) and never enumerable, because "the
 * lead magnet is private until someone comments" is not something a directory
 * listing should be able to break.
 */

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const DEFAULT_DIR = path.join(__dirname, "..", "uploads");
const MAX_BYTES = Math.round(Number(process.env.IG_UPLOAD_MAX_MB || 25) * 1024 * 1024);

/**
 * What may be uploaded, and what it is served as.
 *
 * An allowlist, not a blocklist, and the reason is the hostname. These files are
 * served from hooks.aiprofitlab.io — a subdomain of the brand. An .html or .svg
 * upload there is a same-origin script that anyone can be linked to, wearing the
 * company's domain. There is no campaign that needs one, so neither is on this
 * list; "inline" below is only ever a passive type.
 */
const TYPES = {
  pdf: { mime: "application/pdf", inline: true },
  png: { mime: "image/png", inline: true },
  jpg: { mime: "image/jpeg", inline: true },
  jpeg: { mime: "image/jpeg", inline: true },
  webp: { mime: "image/webp", inline: true },
  gif: { mime: "image/gif", inline: true },
  mp4: { mime: "video/mp4", inline: true },
  mov: { mime: "video/quicktime", inline: true },
  mp3: { mime: "audio/mpeg", inline: true },
  m4a: { mime: "audio/mp4", inline: true },
  txt: { mime: "text/plain; charset=utf-8", inline: false },
  csv: { mime: "text/csv; charset=utf-8", inline: false },
  zip: { mime: "application/zip", inline: false },
  doc: { mime: "application/msword", inline: false },
  docx: { mime: "application/vnd.openxmlformats-officedocument.wordprocessingml.document", inline: false },
  xls: { mime: "application/vnd.ms-excel", inline: false },
  xlsx: { mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", inline: false },
  ppt: { mime: "application/vnd.ms-powerpoint", inline: false },
  pptx: { mime: "application/vnd.openxmlformats-officedocument.presentationml.presentation", inline: false },
};

const dir = () => process.env.IG_UPLOAD_DIR || DEFAULT_DIR;

/** Where a follower's browser will land. Must be the public origin, not localhost. */
const publicBase = () => String(process.env.IG_PUBLIC_BASE || "https://hooks.aiprofitlab.io").replace(/\/+$/, "");

const extOf = (name) => String(name || "").toLowerCase().split(".").pop() || "";

/**
 * A filename safe to put on disk and into a URL path.
 * Unicode is dropped rather than percent-encoded: the name is cosmetic (it is
 * what the follower sees in their downloads folder) and an ASCII one cannot
 * surprise any of the four things that will handle it.
 */
function safeName(name) {
  const base = path.basename(String(name || "file"));
  const cleaned = base
    .replace(/[^\w.\- ]+/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^[.\-]+/, "")
    .slice(0, 80);
  return cleaned || "file";
}

/** On-disk name carries the id and the display name: <id>__<name>. */
const encodeName = (id, name) => `${id}__${name}`;
function decodeName(diskName) {
  const at = diskName.indexOf("__");
  if (at < 0) return null;
  const id = diskName.slice(0, at);
  const name = diskName.slice(at + 2);
  if (!/^[a-f0-9]{32}$/.test(id) || !name) return null;
  return { id, name };
}

function describe(diskName) {
  const parsed = decodeName(diskName);
  if (!parsed) return null;
  const type = TYPES[extOf(parsed.name)];
  let size = 0;
  let at = null;
  try {
    const st = fs.statSync(path.join(dir(), diskName));
    size = st.size;
    at = new Date(st.mtimeMs).toISOString();
  } catch {
    return null;
  }
  return {
    id: parsed.id,
    name: parsed.name,
    ext: extOf(parsed.name),
    mime: (type && type.mime) || "application/octet-stream",
    size,
    uploadedAt: at,
    url: urlFor(parsed.id, parsed.name),
  };
}

/** Newest first. */
function list() {
  let names;
  try {
    names = fs.readdirSync(dir());
  } catch {
    return [];
  }
  return names
    .map(describe)
    .filter(Boolean)
    .sort((a, b) => String(b.uploadedAt).localeCompare(String(a.uploadedAt)));
}

function find(id) {
  if (!/^[a-f0-9]{32}$/.test(String(id || ""))) return null;
  let names;
  try {
    names = fs.readdirSync(dir());
  } catch {
    return null;
  }
  const hit = names.find((n) => n.startsWith(`${id}__`));
  return hit ? { ...describe(hit), path: path.join(dir(), hit) } : null;
}

/**
 * The URL that goes in the DM.
 *
 * Takes the display name as a second argument only so list() does not have to
 * re-scan the directory for something it already knows. Callers with just an id
 * (the rules engine, resolving rule.dm.fileId) leave it out and get a lookup.
 * A missing file resolves to "" rather than a dead link — the DM then carries
 * whatever text and link the rule also has, instead of a 404 on the brand's
 * own domain.
 */
function urlFor(id, name) {
  if (!id) return "";
  const display = name || (find(id) || {}).name;
  if (!display) return "";
  return `${publicBase()}/f/${id}/${encodeURIComponent(display)}`;
}

class UploadRejected extends Error {
  constructor(message) {
    super(message);
    this.name = "UploadRejected";
  }
}

/**
 * @param {Buffer} buffer raw bytes as posted
 * @param {string} filename original name, used for the extension and the display name
 */
function save(buffer, filename) {
  if (!Buffer.isBuffer(buffer) || !buffer.length) throw new UploadRejected("empty upload");
  if (buffer.length > MAX_BYTES) {
    throw new UploadRejected(`file is ${(buffer.length / 1024 / 1024).toFixed(1)} MB — the limit is ${Math.round(MAX_BYTES / 1024 / 1024)} MB`);
  }

  const name = safeName(filename);
  const ext = extOf(name);
  if (!TYPES[ext]) {
    throw new UploadRejected(`.${ext || "?"} files are not allowed — allowed: ${Object.keys(TYPES).join(", ")}`);
  }

  const id = crypto.randomBytes(16).toString("hex");
  fs.mkdirSync(dir(), { recursive: true });
  const target = path.join(dir(), encodeName(id, name));
  const tmp = `${target}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, buffer, { mode: 0o640 });
  fs.renameSync(tmp, target);

  console.log(JSON.stringify({ event: "file_uploaded", id, name, bytes: buffer.length }));
  return describe(encodeName(id, name));
}

function remove(id) {
  const hit = find(id);
  if (!hit) return false;
  fs.unlinkSync(hit.path);
  console.log(JSON.stringify({ event: "file_deleted", id, name: hit.name }));
  return true;
}

/** Which rules point at this file. Deleting one out from under a live rule is worth a warning. */
function usedBy(id, config) {
  return ((config && config.rules) || []).filter((r) => r.dm && r.dm.fileId === id).map((r) => r.id);
}

module.exports = { dir, publicBase, list, find, save, remove, urlFor, usedBy, safeName, describe, TYPES, MAX_BYTES, UploadRejected };
