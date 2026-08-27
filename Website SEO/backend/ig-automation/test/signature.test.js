/**
 * The only thing authenticating a public URL.
 */
const test = require("node:test");
const assert = require("node:assert");

const signature = require("../lib/signature");

const SECRET = "app-secret-0123456789";
const body = Buffer.from(JSON.stringify({ object: "instagram", entry: [{ id: "1" }] }), "utf8");

test("a payload signed with the app secret verifies", () => {
  assert.equal(signature.verify(body, signature.sign(body, SECRET), SECRET), true);
});

test("one changed byte fails", () => {
  const header = signature.sign(body, SECRET);
  const tampered = Buffer.from(JSON.stringify({ object: "instagram", entry: [{ id: "2" }] }), "utf8");
  assert.equal(signature.verify(tampered, header, SECRET), false);
});

test("a signature from a different secret fails", () => {
  assert.equal(signature.verify(body, signature.sign(body, "not-the-secret"), SECRET), false);
});

test("a missing or malformed header fails", () => {
  assert.equal(signature.verify(body, undefined, SECRET), false);
  assert.equal(signature.verify(body, "", SECRET), false);
  assert.equal(signature.verify(body, "sha1=abc", SECRET), false);
  assert.equal(signature.verify(body, "sha256=nothex", SECRET), false);
  assert.equal(signature.verify(body, "sha256=" + "a".repeat(63), SECRET), false, "63 hex chars is not a sha256");
});

test("an empty body cannot be signed into validity", () => {
  assert.equal(signature.verify(Buffer.alloc(0), signature.sign(Buffer.alloc(0), SECRET), SECRET), false);
});

test("no configured secret rejects everything — it fails closed, never open", () => {
  assert.equal(signature.verify(body, signature.sign(body, SECRET), ""), false);
  assert.equal(signature.verify(body, signature.sign(body, SECRET), undefined), false);
});

test("re-serialising the body changes the digest, which is why raw bytes are kept", () => {
  const header = signature.sign(body, SECRET);
  const reserialised = Buffer.from(JSON.stringify(JSON.parse(body.toString())).replace('"object"', ' "object"'), "utf8");
  assert.equal(signature.verify(reserialised, header, SECRET), false);
});

test("appsecret_proof is the HMAC of the token, and is empty when unconfigured", () => {
  const proof = signature.appsecretProof("TOKEN123", SECRET);
  assert.match(proof, /^[a-f0-9]{64}$/);
  assert.equal(signature.appsecretProof("TOKEN123", ""), "");
  assert.equal(signature.appsecretProof("", SECRET), "");
});

test("verify-token comparison is length-safe and does not throw", () => {
  assert.equal(signature.safeEqual("abc", "abc"), true);
  assert.equal(signature.safeEqual("abc", "abcd"), false);
  assert.equal(signature.safeEqual("", ""), true);
  assert.equal(signature.safeEqual(undefined, "abc"), false);
});
