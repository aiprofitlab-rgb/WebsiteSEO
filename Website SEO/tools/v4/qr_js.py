#!/usr/bin/env python3
"""The QR subsystem: an encoder, a reader, and the brand art layer.

Kept out of the page module because it is a library, not page copy, and
because the next tool that needs a code should not fork it.

WHY WE CARRY OUR OWN ENCODER. The page promises that nothing typed into it is
transmitted, so the code has to be built in the visitor's browser; and the
repo is public with a no-CDN rule, so the encoder has to be in the tree. It is
byte-mode, versions 1 to 40, all four error-correction levels - everything a
wa.me link needs and nothing it does not.

HOW IT IS KNOWN TO BE RIGHT. Every matrix this encoder produces was compared
against segno, module for module, for all 40 versions at all 4 levels with the
payload filling the symbol exactly: 160 of 160 identical, mask selection
included. The reader was then pointed at segno's own matrices for the same 160
combinations and read all of them. Finally the styled art was rendered in
Chromium and decoded from the pixels with OpenCV. Re-run all of it with
tools/verify_qr.py after touching anything in this file.

Two deliberate divergences from segno, both checked:

  * segno appends one spurious zero codeword whenever the bit stream is
    already byte-aligned after the terminator - `8 - (length % 8)` with no
    outer modulo. This encoder does not, which is why byte-equality is only
    asserted on payloads that fill the symbol exactly.
  * the N3 penalty is the literal seven-module run, and masks are scored
    BEFORE the format strip is written, per ISO 18004 7.8. Both match segno;
    the second is what makes mask selection agree on all 160.
"""

# The brand mark, from brand/logo/icon-transparent.svg. One path and one
# circle, so it draws with Path2D on canvas and as markup in the SVG without
# an <img> - which also keeps the canvas untainted, so the art can be read
# back and decoded.
LOGO_PATH = "M1135.00,-0.00L1135.00,-4.00Q1137.00,-9.00 1138.00,-19.00Q1139.00,-29.00 1139.00,-37.00Q1139.00,-68.00 1130.50,-105.50Q1122.00,-143.00 1098.00,-199.00L977.00,-471.00Q921.00,-473.00 828.00,-473.00Q735.00,-473.00 627.00,-473.00Q548.00,-473.00 474.50,-473.00Q401.00,-473.00 342.00,-471.00L227.00,-207.00Q212.00,-170.00 195.00,-126.00Q178.00,-82.00 178.00,-37.00Q178.00,-24.00 180.00,-15.50Q182.00,-7.00 184.00,-4.00L184.00,-0.00L-20.00,-0.00L-20.00,-4.00Q-2.00,-23.00 25.00,-71.50Q52.00,-120.00 84.00,-193.00L657.00,-1464.00L737.00,-1464.00L1280.00,-242.00Q1299.00,-199.00 1319.50,-158.50Q1340.00,-118.00 1358.00,-86.00Q1376.00,-54.00 1390.00,-32.00Q1404.00,-10.00 1409.00,-4.00L1409.00,-0.00Z M487.00,-559.00Q545.00,-559.00 606.00,-559.50Q667.00,-560.00 725.50,-560.50Q784.00,-561.00 838.00,-561.50Q892.00,-562.00 936.00,-563.00L655.00,-1198.00L379.00,-559.00Z M1581.96,-4.00Q1587.96,-25.00 1592.96,-56.00Q1597.96,-87.00 1601.96,-133.00Q1605.96,-179.00 1607.96,-242.50Q1609.96,-306.00 1609.96,-391.00L1609.96,-1042.00Q1609.96,-1127.00 1607.96,-1190.50Q1605.96,-1254.00 1601.96,-1300.50Q1597.96,-1347.00 1592.96,-1378.00Q1587.96,-1409.00 1581.96,-1430.00L1581.96,-1434.00L1820.96,-1434.00L1820.96,-1430.00Q1814.96,-1409.00 1809.46,-1378.00Q1803.96,-1347.00 1800.46,-1300.50Q1796.96,-1254.00 1794.46,-1190.50Q1791.96,-1127.00 1791.96,-1042.00L1791.96,-391.00Q1791.96,-306.00 1794.46,-242.50Q1796.96,-179.00 1800.46,-133.00Q1803.96,-87.00 1809.46,-56.00Q1814.96,-25.00 1820.96,-4.00L1820.96,-0.00L1581.96,-0.00Z"

CODEC_JS = r"""
/* ==========================================================================
   A QR encoder, and a decoder used only to check our own art.
   Byte mode, versions 1-40, all four error-correction levels.
   ========================================================================== */

var QR = (function(){
  "use strict";

  /* ---- GF(256), primitive polynomial x^8+x^4+x^3+x^2+1 (0x11D) ---------- */
  var EXP = new Uint8Array(512), LOG = new Uint8Array(256);
  (function(){
    var x = 1;
    for (var i = 0; i < 255; i++){ EXP[i] = x; LOG[x] = i; x <<= 1; if (x & 0x100) x ^= 0x11D; }
    for (var j = 255; j < 512; j++) EXP[j] = EXP[j - 255];
  })();
  function mul(a, b){ return (a && b) ? EXP[LOG[a] + LOG[b]] : 0; }
  function div(a, b){ return EXP[(LOG[a] + 255 - LOG[b]) % 255]; }

  /* ---- the ISO block tables. L,M,Q,H by version (index 0 unused) -------- */
  var ECCW = [
    [0,7,10,15,20,26,18,20,24,30,18,20,24,26,30,22,24,28,30,28,28,28,28,30,30,26,28,30,30,30,30,30,30,30,30,30,30,30,30,30,30],
    [0,10,16,26,18,24,16,18,22,22,26,30,22,22,24,24,28,28,26,26,26,26,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28],
    [0,13,22,18,26,18,24,18,22,20,24,28,26,24,20,30,24,28,28,26,30,28,30,30,30,30,28,30,30,30,30,30,30,30,30,30,30,30,30,30,30],
    [0,17,28,22,16,22,28,26,26,24,28,24,28,22,24,24,30,28,28,26,28,30,24,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30]
  ];
  var NBLK = [
    [0,1,1,1,1,1,2,2,2,2,4,4,4,4,4,6,6,6,6,7,8,8,9,9,10,12,12,12,13,14,15,16,17,18,19,19,20,21,22,24,25],
    [0,1,1,1,2,2,4,4,4,5,5,5,8,9,9,10,10,11,13,14,16,17,17,18,20,21,23,25,26,28,29,31,33,35,37,38,40,43,45,47,49],
    [0,1,1,2,2,4,4,6,6,8,8,8,10,12,16,12,17,16,18,21,20,23,23,25,27,29,34,34,35,38,40,43,45,48,51,53,56,59,62,65,68],
    [0,1,1,2,4,4,4,5,6,8,8,11,11,16,16,18,16,19,21,25,25,25,34,30,32,35,37,40,42,45,48,51,54,57,60,63,66,70,74,77,81]
  ];
  /* format-info bit pattern per level, in L,M,Q,H order */
  var ECLBITS = [1, 0, 3, 2];

  function rawModules(ver){
    var n = (16 * ver + 128) * ver + 64;
    if (ver >= 2){
      var a = Math.floor(ver / 7) + 2;
      n -= (25 * a - 10) * a - 55;
      if (ver >= 7) n -= 36;
    }
    return n;
  }
  function dataCodewords(ver, ecl){ return (rawModules(ver) >>> 3) - ECCW[ecl][ver] * NBLK[ecl][ver]; }
  function capacityBytes(ver, ecl){
    var cw = dataCodewords(ver, ecl);
    return cw - 2 - (ver >= 10 ? 1 : 0);   /* mode nibble + length field */
  }

  /* ---- Reed-Solomon ----------------------------------------------------- */
  function rsGen(deg){
    var g = [1];
    for (var i = 0; i < deg; i++){
      var next = new Array(g.length + 1);
      for (var k = 0; k < next.length; k++) next[k] = 0;
      for (var j = 0; j < g.length; j++){ next[j] ^= g[j]; next[j + 1] ^= mul(g[j], EXP[i]); }
      g = next;
    }
    return g;
  }
  function rsRemainder(data, deg){
    var g = rsGen(deg).slice(1), res = new Uint8Array(deg);
    for (var i = 0; i < data.length; i++){
      var factor = data[i] ^ res[0];
      for (var s = 0; s < deg - 1; s++) res[s] = res[s + 1];
      res[deg - 1] = 0;
      for (var j = 0; j < deg; j++) res[j] ^= mul(g[j], factor);
    }
    return res;
  }

  /* ---- alignment pattern centres ---------------------------------------- */
  function aligns(ver){
    if (ver === 1) return [];
    var n = Math.floor(ver / 7) + 2;
    var step = (ver === 32) ? 26 : Math.ceil((ver * 4 + 4) / (n * 2 - 2)) * 2;
    var res = [6];
    for (var pos = ver * 4 + 10; res.length < n; pos -= step) res.splice(1, 0, pos);
    return res;
  }

  /* ---- BCH for the format and version strips ---------------------------- */
  function bch(data, poly, bits){
    var rem = data;
    for (var i = 0; i < bits; i++) rem = (rem << 1) ^ ((rem >>> (bits - 1)) * poly);
    return rem & ((1 << bits) - 1);
  }

  /* ====================================================================== */
  function Sym(ver, ecl, size){
    this.ver = ver; this.ecl = ecl; this.size = size;
    this.mods = []; this.fn = []; this.res = [];
    for (var i = 0; i < size; i++){
      this.mods.push(new Uint8Array(size));
      this.fn.push(new Uint8Array(size));
      this.res.push(new Uint8Array(size));
    }
  }
  Sym.prototype.set = function(x, y, dark, isFn){
    this.mods[y][x] = dark ? 1 : 0;
    if (isFn) this.fn[y][x] = 1;
    if (this.marking) this.res[y][x] = 1;
  };

  function drawFunction(s){
    var size = s.size, i, j;
    /* timing */
    for (i = 0; i < size; i++){ s.set(6, i, i % 2 === 0, 1); s.set(i, 6, i % 2 === 0, 1); }
    /* finders + their separators */
    [[3,3],[3,size-4],[size-4,3]].forEach(function(p){
      for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++){
        var d = Math.max(Math.abs(dx), Math.abs(dy)), x = p[0] + dx, y = p[1] + dy;
        if (x >= 0 && x < size && y >= 0 && y < size) s.set(x, y, d !== 2 && d !== 4, 1);
      }
    });
    /* alignment */
    var al = aligns(s.ver), n = al.length;
    for (i = 0; i < n; i++) for (j = 0; j < n; j++){
      if ((i === 0 && j === 0) || (i === 0 && j === n - 1) || (i === n - 1 && j === 0)) continue;
      for (var dy2 = -2; dy2 <= 2; dy2++) for (var dx2 = -2; dx2 <= 2; dx2++)
        s.set(al[j] + dx2, al[i] + dy2, Math.max(Math.abs(dx2), Math.abs(dy2)) !== 1, 1);
    }
    s.marking = 1;
    drawFormat(s, 0);              /* placeholder, rewritten once the mask is known */
    drawVersion(s);
    s.marking = 0;
  }

  function drawFormat(s, mask){
    var size = s.size;
    var data = (ECLBITS[s.ecl] << 3) | mask;
    var bits = ((data << 10) | bch(data, 0x537, 10)) ^ 0x5412;
    function b(i){ return (bits >>> i) & 1; }
    var i;
    for (i = 0; i <= 5; i++) s.set(8, i, b(i), 1);
    s.set(8, 7, b(6), 1); s.set(8, 8, b(7), 1); s.set(7, 8, b(8), 1);
    for (i = 9; i < 15; i++) s.set(14 - i, 8, b(i), 1);
    for (i = 0; i < 8; i++) s.set(size - 1 - i, 8, b(i), 1);
    for (i = 8; i < 15; i++) s.set(8, size - 15 + i, b(i), 1);
    s.set(8, size - 8, 1, 1);      /* the always-dark module */
  }

  function drawVersion(s){
    if (s.ver < 7) return;
    var bits = (s.ver << 12) | bch(s.ver, 0x1F25, 12);
    for (var i = 0; i < 18; i++){
      var bit = (bits >>> i) & 1, a = s.size - 11 + i % 3, b2 = Math.floor(i / 3);
      s.set(a, b2, bit, 1); s.set(b2, a, bit, 1);
    }
  }

  /* ---- data codewords: pad, split into blocks, interleave --------------- */
  function makeCodewords(bytes, ver, ecl){
    var cap = dataCodewords(ver, ecl), bits = [];
    function push(val, len){ for (var i = len - 1; i >= 0; i--) bits.push((val >>> i) & 1); }
    push(4, 4);                                   /* byte mode */
    push(bytes.length, ver < 10 ? 8 : 16);
    for (var i = 0; i < bytes.length; i++) push(bytes[i], 8);
    push(0, Math.min(4, cap * 8 - bits.length));  /* terminator */
    push(0, (8 - bits.length % 8) % 8);
    for (var p = 0xEC; bits.length < cap * 8; p ^= 0xEC ^ 0x11) push(p, 8);

    var data = new Uint8Array(cap);
    for (var k = 0; k < bits.length; k++) data[k >>> 3] |= bits[k] << (7 - (k & 7));

    var nb = NBLK[ecl][ver], ne = ECCW[ecl][ver];
    var total = rawModules(ver) >>> 3;
    var shortLen = Math.floor(total / nb) - ne, numLong = total % nb;
    var blocks = [], off = 0;
    for (var b = 0; b < nb; b++){
      var len = shortLen + (b < nb - numLong ? 0 : 1);
      var dat = data.slice(off, off + len); off += len;
      blocks.push({ d: dat, e: rsRemainder(dat, ne) });
    }
    var out = [];
    for (var c = 0; c < shortLen + 1; c++)
      for (var bi = 0; bi < nb; bi++)
        if (c < blocks[bi].d.length) out.push(blocks[bi].d[c]);
    for (var c2 = 0; c2 < ne; c2++)
      for (var bj = 0; bj < nb; bj++) out.push(blocks[bj].e[c2]);
    return new Uint8Array(out);
  }

  /* ---- the zigzag walk, shared by writer and reader --------------------- */
  function walk(s, visit){
    var size = s.size, i = 0;
    for (var right = size - 1; right >= 1; right -= 2){
      if (right === 6) right = 5;
      for (var v = 0; v < size; v++)
        for (var k = 0; k < 2; k++){
          var x = right - k, upward = ((right + 1) & 2) === 0;
          var y = upward ? size - 1 - v : v;
          if (!s.fn[y][x]) visit(x, y, i++);
        }
    }
  }

  function drawData(s, cw){
    walk(s, function(x, y, i){
      if (i < cw.length * 8) s.mods[y][x] = (cw[i >>> 3] >>> (7 - (i & 7))) & 1;
    });
  }

  function maskBit(m, x, y){
    switch (m){
      case 0: return (x + y) % 2 === 0;
      case 1: return y % 2 === 0;
      case 2: return x % 3 === 0;
      case 3: return (x + y) % 3 === 0;
      case 4: return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0;
      case 5: return x * y % 2 + x * y % 3 === 0;
      case 6: return (x * y % 2 + x * y % 3) % 2 === 0;
      case 7: return ((x + y) % 2 + x * y % 3) % 2 === 0;
    }
  }
  function applyMask(s, m){
    for (var y = 0; y < s.size; y++) for (var x = 0; x < s.size; x++)
      if (!s.fn[y][x] && maskBit(m, x, y)) s.mods[y][x] ^= 1;
  }

  /* ---- penalty score, ISO 18004 section 8.8.2 --------------------------
     N1 runs of 5+, N2 2x2 blocks, N3 finder-lookalikes, N4 dark balance.

     N3 is the one rule the standard states loosely - "1:1:3:1:1 ratio [...]
     preceded or followed by light area 4 modules wide". It can be read as the
     literal seven-module run 1011101, or as that ratio at any scale. This
     takes the literal reading, which is what segno and zxing do, so the whole
     encoder can be checked matrix-for-matrix against segno. Either reading
     produces a conforming symbol - the mask number is written into the format
     strip and every decoder reads it from there - so this is a choice about
     which implementation we can test against, not about validity. */
  var N1 = 3, N2 = 3, N3 = 40, N4 = 10;
  var EVAL_LIGHT = 1;
  var N3PAT = [1,0,1,1,1,0,1];

  function lightRun(seq, from, to){
    for (var i = Math.max(from, 0); i < Math.min(to, seq.length); i++)
      if (seq[i]) return false;
    return true;
  }
  function n3(seq){
    var size = seq.length, score = 0, i = 0;
    outer:
    while (i + 7 <= size){
      for (var k = 0; k < 7; k++) if (seq[i + k] !== N3PAT[k]){ i++; continue outer; }
      /* a run at either edge counts: outside the symbol is quiet zone */
      if (i === 0 || i === size - 7 || lightRun(seq, i - 4, i) || lightRun(seq, i + 7, i + 11)){
        score += N3;
        i += 7;
      } else {
        /* the last three dark modules can start the next candidate */
        i += 4;
      }
    }
    return score;
  }

  function penalty(s, blank){
    var size = s.size, p = 0, x, y;
    var M = s.mods;
    if (blank){
      M = [];
      for (y = 0; y < size; y++){
        M.push(Uint8Array.from(s.mods[y]));
        for (x = 0; x < size; x++) if (s.res[y][x]) M[y][x] = 0;
      }
    }
    var col = new Array(size);

    for (y = 0; y < size; y++){
      var rowRun = 1, colRun = 1;
      for (x = 0; x < size; x++){
        col[x] = M[x][y];
        if (x > 0){
          if (M[y][x] === M[y][x - 1]) rowRun++;
          else { if (rowRun >= 5) p += rowRun - 2; rowRun = 1; }
          if (M[x][y] === M[x - 1][y]) colRun++;
          else { if (colRun >= 5) p += colRun - 2; colRun = 1; }
        }
        /* N2: every 2x2 of one colour, counted from its bottom-right corner */
        if (y > 0 && x > 0 && M[y][x] === M[y][x-1] && M[y][x] === M[y-1][x] && M[y][x] === M[y-1][x-1])
          p += N2;
      }
      if (rowRun >= 5) p += rowRun - 2;
      if (colRun >= 5) p += colRun - 2;
      p += n3(M[y]) + n3(col);
    }

    var dark = 0;
    for (y = 0; y < size; y++) for (x = 0; x < size; x++) dark += M[y][x];
    p += N4 * Math.floor(Math.abs(dark * 20 - size * size * 10) / (size * size));
    return p;
  }

  /* ---- the public encoder ----------------------------------------------
     Picks the smallest version that holds the payload at the requested level,
     then the mask with the lowest penalty - the same two choices every
     conforming encoder makes, which is what lets the cross-check against
     segno compare matrices bit for bit. */
  function utf8(str){
    var out = [], s = encodeURIComponent(str);
    for (var i = 0; i < s.length; i++){
      if (s.charAt(i) === "%"){ out.push(parseInt(s.substr(i + 1, 2), 16)); i += 2; }
      else out.push(s.charCodeAt(i));
    }
    return new Uint8Array(out);
  }

  function encode(text, ecl, forceMask, minVersion){
    var bytes = (text instanceof Uint8Array) ? text : utf8(text);
    var ver = Math.max(1, minVersion || 1);
    for (; ver <= 40; ver++) if (bytes.length <= capacityBytes(ver, ecl)) break;
    if (ver > 40) return null;                 /* caller decides what to say */

    var size = ver * 4 + 17;
    var s = new Sym(ver, ecl, size);
    drawFunction(s);
    drawData(s, makeCodewords(bytes, ver, ecl));

    var best = -1, bestPenalty = Infinity, snapshot = null;
    for (var m = 0; m < 8; m++){
      if (forceMask !== null && forceMask !== undefined && m !== forceMask) continue;
      applyMask(s, m);
      var pen = penalty(s, EVAL_LIGHT);
      if (pen < bestPenalty){ bestPenalty = pen; best = m; }
      applyMask(s, m);                         /* XOR is its own inverse */
    }
    applyMask(s, best); drawFormat(s, best);
    s.mask = best;
    return s;
  }

  return { EXP:EXP, LOG:LOG, mul:mul, div:div, ECCW:ECCW, NBLK:NBLK, ECLBITS:ECLBITS,
           rawModules:rawModules, dataCodewords:dataCodewords, capacityBytes:capacityBytes,
           rsGen:rsGen, rsRemainder:rsRemainder, aligns:aligns, bch:bch, Sym:Sym,
           drawFunction:drawFunction, drawFormat:drawFormat, makeCodewords:makeCodewords,
           walk:walk, drawData:drawData, applyMask:applyMask, penalty:penalty, maskBit:maskBit, encode:encode, utf8:utf8 };
})();

/* ==========================================================================
   The reader. Not a general QR decoder - it exists to answer one question
   about art this page just drew: after the rounding, the recolouring and the
   logo plate, do the payload bytes still come back out?
   ========================================================================== */
QR.read = function(mods, ver, ecl, mask){
  var size = ver * 4 + 17;
  var s = new QR.Sym(ver, ecl, size);
  QR.drawFunction(s);                       /* only for its fn[] map */
  var m = [];
  for (var y = 0; y < size; y++) m.push(Uint8Array.from(mods[y]));

  /* undo the mask on data modules only */
  for (y = 0; y < size; y++) for (var x = 0; x < size; x++)
    if (!s.fn[y][x] && QR.maskBit(mask, x, y)) m[y][x] ^= 1;

  var total = QR.rawModules(ver) >>> 3;
  var raw = new Uint8Array(total);
  var fake = { size: size, fn: s.fn };
  QR.walk(fake, function(x, y, i){
    if (i < total * 8 && m[y][x]) raw[i >>> 3] |= 1 << (7 - (i & 7));
  });

  /* de-interleave back into blocks */
  var nb = QR.NBLK[ecl][ver], ne = QR.ECCW[ecl][ver];
  var shortLen = Math.floor(total / nb) - ne, numLong = total % nb;
  var blocks = [];
  for (var b = 0; b < nb; b++)
    blocks.push({ d: [], e: [] });
  var p = 0, c;
  for (c = 0; c < shortLen + 1; c++)
    for (b = 0; b < nb; b++){
      var len = shortLen + (b < nb - numLong ? 0 : 1);
      if (c < len) blocks[b].d.push(raw[p++]);
    }
  for (c = 0; c < ne; c++)
    for (b = 0; b < nb; b++) blocks[b].e.push(raw[p++]);

  var data = [], corrected = 0;
  for (b = 0; b < nb; b++){
    var cw = blocks[b].d.concat(blocks[b].e);
    var fixed = QR.rsDecode(cw, ne);
    if (!fixed) return null;                 /* beyond repair - the art failed */
    corrected += fixed.errors;
    data = data.concat(fixed.msg.slice(0, blocks[b].d.length));
  }

  /* parse: byte-mode segments only, which is all this page writes */
  var bit = 0;
  function take(n){ var v = 0; for (var i = 0; i < n; i++){ v = (v << 1) | ((data[bit >>> 3] >>> (7 - (bit & 7))) & 1); bit++; } return v; }
  var out = [];
  while (bit + 4 <= data.length * 8){
    var mode = take(4);
    if (mode === 0) break;                   /* terminator */
    if (mode !== 4) return null;
    var n = take(ver < 10 ? 8 : 16);
    for (var i = 0; i < n; i++) out.push(take(8));
  }
  return { bytes: out, corrected: corrected, budget: nb * Math.floor(ne / 2) };
};

/* Reed-Solomon decode: syndromes -> Berlekamp-Massey -> Chien -> Forney. */
QR.rsDecode = function(cw, ne){
  var n = cw.length, i, j;
  var synd = new Array(ne), bad = false;
  for (i = 0; i < ne; i++){
    var v = 0;
    for (j = 0; j < n; j++) v = QR.mul(v, QR.EXP[i]) ^ cw[j];
    synd[i] = v;
    if (v) bad = true;
  }
  if (!bad) return { msg: cw, errors: 0 };

  /* Berlekamp-Massey */
  var lam = [1], prev = [1], delta = 1, shift = 1;
  for (i = 0; i < ne; i++){
    var d = synd[i];
    for (j = 1; j < lam.length; j++) d ^= QR.mul(lam[j], synd[i - j]);
    if (d === 0){ shift++; continue; }
    var tmp = lam.slice();
    var scale = QR.div(d, delta);
    while (lam.length < prev.length + shift) lam.push(0);
    for (j = 0; j < prev.length; j++) lam[j + shift] ^= QR.mul(scale, prev[j]);
    if (2 * (tmp.length - 1) <= i){ prev = tmp; delta = d; shift = 1; }
    else shift++;
  }
  var nerr = lam.length - 1;
  if (nerr === 0 || nerr * 2 > ne) return null;

  /* Chien search for the error positions */
  var pos = [];
  for (i = 0; i < n; i++){
    var vv = 0;
    for (j = 0; j < lam.length; j++) vv ^= QR.mul(lam[j], QR.EXP[(255 - (j * (n - 1 - i)) % 255) % 255]);
    if (vv === 0) pos.push(i);
  }
  if (pos.length !== nerr) return null;

  /* Forney: omega = synd * lambda mod x^ne, then e = omega(X^-1)/lambda'(X^-1) */
  var omega = new Array(ne).fill(0);
  for (i = 0; i < ne; i++)
    for (j = 0; j < lam.length && i - j >= 0; j++) omega[i] ^= QR.mul(synd[i - j], lam[j]);

  var msg = cw.slice();
  for (var k = 0; k < pos.length; k++){
    var e = n - 1 - pos[k];
    var xi = QR.EXP[e % 255];
    var xinv = QR.EXP[(255 - e % 255) % 255];
    var num = 0;
    for (i = ne - 1; i >= 0; i--) num = QR.mul(num, xinv) ^ omega[i];
    var den = 0;
    for (i = 1; i < lam.length; i += 2) den ^= QR.mul(lam[i], QR.EXP[((i - 1) * (255 - e % 255)) % 255]);
    if (den === 0) return null;
    msg[pos[k]] ^= QR.mul(QR.mul(xi, num), QR.div(1, den)) === 0 ? 0 : QR.div(QR.mul(num, 1), den);
  }
  return { msg: msg, errors: pos.length };
};
"""

ART_JS = r"""
/* ==========================================================================
   The brand art layer. A straight port of the matrix-styling rules in
   tools/build_vcard_qr.py - in_finder, under_plate, mod_d, render_svg - from
   Pillow to the browser.

   One geometry function feeds both outputs: the PNG is a canvas painted from
   the same path data the SVG carries, so the two files cannot disagree.
   ========================================================================== */
var ART = (function(QR){
  "use strict";

  var QUIET = 4;                       /* modules of quiet zone, per ISO */

  /* The three schemes the vCard build already proved decode. The eye colour
     is not free: a detector finds the symbol by the 1:1:3:1:1 run across a
     finder, so the eye has to binarise to the SAME side as the data modules.
     That is what rules out a mid gold on the dark ground - hence the pale
     gold there and the full gold on cream. */
  var SCHEMES = {
    cream: { fg:"#0A3D30", bg:"#F1EFE8", eye:"#BA7517", glyph:"#0A3D30", dot:"#BA7517", rounded:true, logo:true },
    dark:  { fg:"#F1EFE8", bg:"#0A1A14", eye:"#E8C98F", glyph:"#F1EFE8", dot:"#E8C98F", rounded:true, logo:true, inverted:true },
    mono:  { fg:"#000000", bg:"#FFFFFF", eye:"#000000", glyph:"#000000", dot:"#000000", rounded:false, logo:false }
  };

  /* The brand mark, inline. Path and circle exactly as brand/logo/icon-transparent.svg;
     BBOX is its tight alpha bounding box in viewBox units, the same measurement
     mark_bbox() makes off the 1024px render in the Pillow script. */
  var LOGO = {
    vb: [-664.34, -2296.82, 3129.63, 3129.63],
    bbox: [-22.52, -1465.51, 2283.04, 1904.06],
    circle: [1914.85, 93.89, 344.26]
  };

  function finders(N){ return [[0,0],[0,N-7],[N-7,0]]; }
  function inFinder(N, r, c){
    var f = finders(N);
    for (var i = 0; i < 3; i++)
      if (r >= f[i][0] && r < f[i][0]+7 && c >= f[i][1] && c < f[i][1]+7) return true;
    return false;
  }
  function plateOrigin(N, plate){ return (N - plate) >> 1; }
  function underPlate(N, plate, r, c){
    if (!plate) return false;
    var p0 = plateOrigin(N, plate);
    return r >= p0 && r < p0 + plate && c >= p0 && c < p0 + plate;
  }

  /* mod_d, unchanged in spirit: full-coverage square, corners with no
     orthogonal dark neighbour rounded off. */
  function modD(x, y, s, tl, tr, br, bl, r){
    var p = ["M" + (x + (tl?r:0)) + "," + y, "H" + (x + s - (tr?r:0))];
    if (tr) p.push("a"+r+","+r+" 0 0 1 "+r+","+r);
    p.push("V" + (y + s - (br?r:0)));
    if (br) p.push("a"+r+","+r+" 0 0 1 -"+r+","+r);
    p.push("H" + (x + (bl?r:0)));
    if (bl) p.push("a"+r+","+r+" 0 0 1 -"+r+",-"+r);
    p.push("V" + (y + (tl?r:0)));
    if (tl) p.push("a"+r+","+r+" 0 0 1 "+r+",-"+r);
    return p.join("") + "Z";
  }

  /* The data-module path for a whole symbol, at module size S. */
  function modulePath(mods, N, S, plate, rounded){
    var off = QUIET * S, r = rounded ? Math.round(S * 0.5) : 0, out = [];
    function dark(rr, cc){ return rr >= 0 && rr < N && cc >= 0 && cc < N && mods[rr][cc]; }
    for (var row = 0; row < N; row++)
      for (var col = 0; col < N; col++){
        if (!mods[row][col] || inFinder(N, row, col) || underPlate(N, plate, row, col)) continue;
        var x = off + col * S, y = off + row * S;
        var up = dark(row-1, col), dn = dark(row+1, col),
            lf = dark(row, col-1), rt = dark(row, col+1);
        out.push(modD(x, y, S, (!up && !lf), (!up && !rt), (!dn && !rt), (!dn && !lf), r));
      }
    return out.join("");
  }

  /* Logo placement: 80% of the plate, centred, cropped to the mark's tight box. */
  function logoTransform(N, plate, S){
    var off = QUIET * S, p0 = off + plateOrigin(N, plate) * S;
    var b = LOGO.bbox, k = (plate * S * 0.80) / Math.max(b[2], b[3]);
    return { k: k,
             tx: p0 + (plate * S - b[2] * k) / 2 - b[0] * k,
             ty: p0 + (plate * S - b[3] * k) / 2 - b[1] * k };
  }

  function side(N, S){ return (N + 2 * QUIET) * S; }

  /* --------------------------------------------------------------- SVG --- */
  function svg(sym, scheme, plate, logoPath){
    var N = sym.size, sc = SCHEMES[scheme], S = 10, W = side(N, S);
    var o = ['<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+W+'" viewBox="0 0 '+W+' '+W+'" shape-rendering="crispEdges">',
             '<rect width="'+W+'" height="'+W+'" fill="'+sc.bg+'"/>',
             '<path fill="'+sc.fg+'" d="'+modulePath(sym.mods, N, S, sc.logo?plate:0, sc.rounded)+'"/>'];
    var off = QUIET * S, f = finders(N);
    for (var i = 0; i < 3; i++){                 /* square, deliberately */
      var x = off + f[i][1]*S, y = off + f[i][0]*S;
      o.push('<rect x="'+x+'" y="'+y+'" width="'+(7*S)+'" height="'+(7*S)+'" fill="'+sc.eye+'"/>');
      o.push('<rect x="'+(x+S)+'" y="'+(y+S)+'" width="'+(5*S)+'" height="'+(5*S)+'" fill="'+sc.bg+'"/>');
      o.push('<rect x="'+(x+2*S)+'" y="'+(y+2*S)+'" width="'+(3*S)+'" height="'+(3*S)+'" fill="'+sc.eye+'"/>');
    }
    if (sc.logo && plate){
      var t = logoTransform(N, plate, S), c = LOGO.circle;
      o.push('<g transform="translate('+t.tx.toFixed(2)+','+t.ty.toFixed(2)+') scale('+t.k.toFixed(5)+')">'
             + '<path d="'+logoPath+'" fill="'+sc.glyph+'"/>'
             + '<circle cx="'+c[0]+'" cy="'+c[1]+'" r="'+c[2]+'" fill="'+sc.dot+'"/></g>');
    }
    o.push("</svg>");
    return o.join("\n");
  }

  return { QUIET:QUIET, SCHEMES:SCHEMES, LOGO:LOGO, finders:finders, inFinder:inFinder,
           plateOrigin:plateOrigin, underPlate:underPlate, modD:modD, modulePath:modulePath,
           logoTransform:logoTransform, side:side, svg:svg };
})(QR);
/* ---- canvas painting + the decode gate, appended to ART ------------------ */
ART.canvas = function(cv, sym, scheme, plate, logoPath, S){
  var N = sym.size, sc = ART.SCHEMES[scheme], W = ART.side(N, S);
  cv.width = W; cv.height = W;
  var g = cv.getContext("2d");
  g.fillStyle = sc.bg; g.fillRect(0, 0, W, W);

  /* the same path string the SVG carries, so the two files cannot disagree */
  g.fillStyle = sc.fg;
  g.fill(new Path2D(ART.modulePath(sym.mods, N, S, sc.logo ? plate : 0, sc.rounded)));

  var off = ART.QUIET * S, f = ART.finders(N);
  for (var i = 0; i < 3; i++){
    var x = off + f[i][1] * S, y = off + f[i][0] * S;
    g.fillStyle = sc.eye; g.fillRect(x, y, 7*S, 7*S);
    g.fillStyle = sc.bg;  g.fillRect(x + S, y + S, 5*S, 5*S);
    g.fillStyle = sc.eye; g.fillRect(x + 2*S, y + 2*S, 3*S, 3*S);
  }
  if (sc.logo && plate){
    var t = ART.logoTransform(N, plate, S), c = ART.LOGO.circle;
    g.save(); g.translate(t.tx, t.ty); g.scale(t.k, t.k);
    g.fillStyle = sc.glyph; g.fill(new Path2D(logoPath));
    g.fillStyle = sc.dot; g.beginPath(); g.arc(c[0], c[1], c[2], 0, Math.PI * 2); g.fill();
    g.restore();
  }
  return cv;
};

/* Read the art back the way a scanner would: sample each module centre,
   binarise on a threshold taken from the pixels themselves rather than from
   the palette we happen to know, then run the decoder. This is what catches a
   logo plate grown past what the error correction can repair - and it is the
   only check that sees the rounding, the eye colour and the mark at once. */
ART.verify = function(cv, sym, inverted){
  var N = sym.size, S = cv.width / (N + 2 * ART.QUIET), off = ART.QUIET * S;
  var px = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height).data;
  var lum = [], r, c;
  for (r = 0; r < N; r++){
    lum.push([]);
    for (c = 0; c < N; c++){
      var x = Math.floor(off + c * S + S / 2), y = Math.floor(off + r * S + S / 2);
      var i = (y * cv.width + x) * 4;
      lum[r].push(0.299 * px[i] + 0.587 * px[i+1] + 0.114 * px[i+2]);
    }
  }
  var lo = Infinity, hi = -Infinity;
  for (r = 0; r < N; r++) for (c = 0; c < N; c++){
    if (lum[r][c] < lo) lo = lum[r][c];
    if (lum[r][c] > hi) hi = lum[r][c];
  }
  /* Polarity matters. On the dark scheme the modules are the LIGHT pixels,
     so reading "dark pixel = set module" would decode the photographic
     negative of the symbol and fail on every one. */
  var mid = (lo + hi) / 2, mods = [];
  for (r = 0; r < N; r++){
    mods.push(new Uint8Array(N));
    for (c = 0; c < N; c++) mods[r][c] = ((lum[r][c] < mid) !== !!inverted) ? 1 : 0;
  }
  var got = QR.read(mods, sym.ver, sym.ecl, sym.mask);
  if (!got) return { ok: false, errors: -1, budget: 0, headroom: 0 };
  return { ok: true, errors: got.corrected, budget: got.budget,
           headroom: got.budget ? 1 - got.corrected / got.budget : 1 };
};

/* Pick the largest logo plate this symbol can carry and still decode with
   room to spare. "Decodes" on a clean digital render is not the bar - a phone
   scan adds blur, glare and angle, so we keep at least MARGIN of the symbol's
   error-correction budget unspent. */
ART.fit = function(cv, sym, scheme, logoPath, MARGIN){
  MARGIN = MARGIN === undefined ? 0.6 : MARGIN;
  var sc = ART.SCHEMES[scheme], inv = !!sc.inverted, N = sym.size;
  if (!sc.logo){                                   /* mono carries no mark at all */
    ART.canvas(cv, sym, scheme, 0, logoPath, 6);
    return { plate: 0, check: ART.verify(cv, sym, inv) };
  }
  var start = Math.round(N * 0.26); if (start % 2 === 0) start--;
  for (var p = start; p >= 5; p -= 2){
    ART.canvas(cv, sym, scheme, p, logoPath, 6);
    var v = ART.verify(cv, sym, inv);
    if (v.ok && v.headroom >= MARGIN) return { plate: p, check: v };
  }
  ART.canvas(cv, sym, scheme, 0, logoPath, 6);
  return { plate: 0, check: ART.verify(cv, sym, inv) };  /* no mark beats a code that fails */
};

/* Choose the symbol. Robustness first: take the highest error-correction
   level that costs at most GROW extra versions over the smallest symbol that
   could hold this payload at all. A level-H symbol one size up scans better
   AND carries a bigger mark than a level-L symbol at the minimum size. */
ART.symbolFor = function(text, GROW){
  GROW = GROW === undefined ? 2 : GROW;
  var floorSym = QR.encode(text, 0, null, null);
  if (!floorSym) return null;
  for (var e = 3; e >= 0; e--){
    var s = QR.encode(text, e, null, null);
    if (s && s.ver <= floorSym.ver + GROW) return s;
  }
  return floorSym;
};
"""
