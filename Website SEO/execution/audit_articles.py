#!/usr/bin/env python3
"""
audit_articles.py
Full quality audit of all English blog articles for aiprofitlab.io
Scores each article on 7 criteria and outputs structured report data.
"""

import os
import re
import json
from pathlib import Path
from html.parser import HTMLParser
from datetime import date

BLOG_DIR = Path("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/en")
OUTPUT_DIR = Path("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/.tmp/audit")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# GCC/Oman local keywords (case-insensitive)
LOCAL_KEYWORDS = [
    "oman", "muscat", "gcc", "uae", "saudi", "vision 2040", "vision2040",
    "pdpl", "omani", "gulf", "solopreneur", "clinic", "hypermarket",
    "real estate agent", "duqm", "sohar", "salalah", "nizwa", "bahrain",
    "qatar", "kuwait", "riyadh", "dubai", "abu dhabi", "mena",
    "sultanate", "royal decree", "omantel", "maeen", "otech"
]

# Generic/weak title patterns
GENERIC_TITLE_PATTERNS = [
    r"supercharge your business",
    r"^ai for (your )?business",
    r"unlock (the )?power of ai",
    r"revolutionize your",
    r"transform your business",
    r"take your business to the next level",
]

# CTA link patterns
CTA_LINK_PATTERNS = [
    r"/contact", r"/services", r"wa\.me", r"whatsapp", r"demo",
    r"book", r"schedule", r"consult", r"get started", r"free"
]

# Strong CTA text patterns
STRONG_CTA_TEXT = [
    r"book a free", r"contact us", r"schedule a", r"get a free",
    r"talk to us", r"see how it works", r"request a demo",
    r"start your", r"claim your", r"book now", r"let's talk",
    r"reach out", r"whatsapp us"
]


class HTMLStripper(HTMLParser):
    """Extract text from HTML, tracking structure."""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self.in_skip = False
        self.skip_tags = {"script", "style", "nav", "header", "footer", "noscript"}
        self.skip_depth = 0
        self.title = ""
        self.in_title = False
        self.h1 = ""
        self.in_h1 = False
        self.meta_desc = ""
        self.h2_tags = []
        self.in_h2 = False
        self.current_h2 = ""
        self.article_text_parts = []
        self.in_article = False
        self.article_depth = 0
        self.main_text_parts = []
        self.in_main = False
        self.schema_json = []
        self.in_schema = False
        self.all_links = []
        self.in_a = False
        self.current_a_href = ""
        self.current_a_text = ""
        self.full_text_parts = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "title":
            self.in_title = True
        
        if tag == "h1":
            self.in_h1 = True
        
        if tag == "h2":
            self.in_h2 = True
            self.current_h2 = ""
        
        if tag == "meta":
            if attrs_dict.get("name", "").lower() == "description":
                self.meta_desc = attrs_dict.get("content", "")
        
        if tag == "a":
            self.in_a = True
            self.current_a_href = attrs_dict.get("href", "")
            self.current_a_text = ""
        
        if tag == "script":
            if attrs_dict.get("type") == "application/ld+json":
                self.in_schema = True
                self.skip_depth += 1
            else:
                self.skip_depth += 1
                self.in_skip = True
        
        if tag in self.skip_tags and tag != "script":
            self.skip_depth += 1
            self.in_skip = True
        
        if tag == "article":
            self.in_article = True
            self.article_depth += 1
        
        if tag == "main":
            self.in_main = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        
        if tag == "h1":
            self.in_h1 = False
        
        if tag == "h2":
            if self.current_h2.strip():
                self.h2_tags.append(self.current_h2.strip())
            self.in_h2 = False
        
        if tag == "a":
            if self.current_a_href:
                self.all_links.append({
                    "href": self.current_a_href,
                    "text": self.current_a_text.strip()
                })
            self.in_a = False
        
        if tag == "script":
            self.skip_depth = max(0, self.skip_depth - 1)
            if self.skip_depth == 0:
                self.in_skip = False
                self.in_schema = False
        
        if tag in self.skip_tags and tag != "script":
            self.skip_depth = max(0, self.skip_depth - 1)
            if self.skip_depth == 0:
                self.in_skip = False
        
        if tag == "article":
            self.article_depth -= 1
            if self.article_depth == 0:
                self.in_article = False
        
        if tag == "main":
            self.in_main = False

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        
        if self.in_schema:
            self.schema_json.append(data)
            return
        
        if self.in_skip:
            return
        
        if self.in_title:
            self.title += data
        
        if self.in_h1:
            self.h1 += data
        
        if self.in_h2:
            self.current_h2 += data
        
        if self.in_a:
            self.current_a_text += data
        
        self.full_text_parts.append(data)
        
        if self.in_article:
            self.article_text_parts.append(data)
        elif self.in_main:
            self.main_text_parts.append(data)

    def get_clean_title(self):
        return self.title.strip()
    
    def get_clean_h1(self):
        return self.h1.strip()
    
    def get_body_text(self):
        """Get article/main body text for word counting."""
        if self.article_text_parts:
            return " ".join(self.article_text_parts)
        elif self.main_text_parts:
            return " ".join(self.main_text_parts)
        else:
            return " ".join(self.full_text_parts)
    
    def get_full_text(self):
        return " ".join(self.full_text_parts)


def parse_html(filepath):
    """Parse HTML file and return structured data."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    parser = HTMLStripper()
    parser.feed(content)
    
    body_text = parser.get_body_text()
    full_text = parser.get_full_text()
    word_count = len(body_text.split())
    
    # Get last 200 words of body for CTA check
    body_words = body_text.split()
    last_200 = " ".join(body_words[-200:]) if len(body_words) > 200 else body_text
    
    # Get first paragraph (first ~100 words)
    first_100 = " ".join(body_words[:100]) if len(body_words) > 100 else body_text
    
    # Extract schema JSON
    schema_data = []
    for s in parser.schema_json:
        try:
            schema_data.append(json.loads(s))
        except:
            pass
    
    return {
        "title": parser.get_clean_title(),
        "h1": parser.get_clean_h1(),
        "meta_desc": parser.meta_desc,
        "h2_tags": parser.h2_tags,
        "word_count": word_count,
        "body_text": body_text,
        "full_text": full_text,
        "last_200": last_200,
        "first_100": first_100,
        "links": parser.all_links,
        "schema": schema_data,
        "raw_html": content
    }


def score_criterion_1(data):
    """Title & Hook Strength."""
    title = data["title"].lower()
    h1 = data["h1"].lower()
    first_para = data["first_100"].lower()
    
    # Check for generic title patterns
    is_generic = any(re.search(p, title) for p in GENERIC_TITLE_PATTERNS)
    
    # Check for specifics in title: numbers, locations, outcomes
    has_specific = bool(re.search(r'\d+', title)) or \
                   any(kw in title for kw in ["oman", "muscat", "gcc", "uae", "guide", 
                                               "how to", "why", "when", "cost", "roi",
                                               "step", "tool", "free", "best", "top"])
    
    # Check opening hook quality
    is_self_promo = any(p in first_para for p in ["we are", "we provide", "our company", 
                                                     "ai profit lab is", "welcome to",
                                                     "at ai profit lab"])
    
    title_h1_match = title.strip() == h1.strip() or (h1 and title.startswith(h1[:30]))
    
    if is_generic:
        return "FAIL", "Title is generic filler with no specific benefit or outcome"
    
    if has_specific and not is_self_promo and len(title) > 20:
        if not title_h1_match and h1:
            return "NEEDS WORK", "Title specific but H1 and title tag differ"
        return "PASS", "Title contains specific benefit/keyword; hook addresses reader"
    
    if is_self_promo:
        return "FAIL", "Opening paragraph is self-promotional"
    
    return "NEEDS WORK", "Title acceptable but lacks strong hook or specificity"


def score_criterion_2(data):
    """Word Count & Depth."""
    wc = data["word_count"]
    body = data["body_text"].lower()
    
    # Count concrete markers: numbers/stats, bullet lists, examples
    number_count = len(re.findall(r'\b\d+[\.,]?\d*\s*(%|percent|omr|usd|rial|hours?|days?|minutes?|seconds?|weeks?|months?|years?|x\b)', body))
    example_markers = len(re.findall(r'\b(for example|for instance|such as|case study|e\.g\.|specifically|in practice|real.world|scenario)\b', body))
    step_markers = len(re.findall(r'\b(step \d|first|second|third|finally|next|then|step-by-step|how to)\b', body))
    
    concrete_count = number_count + example_markers + step_markers
    
    if wc >= 900 and concrete_count >= 3:
        return "PASS", f"{wc} words with {concrete_count} concrete examples/steps/data points"
    elif wc >= 900:
        return "NEEDS WORK", f"{wc} words but lacks 3+ concrete examples or data points"
    elif wc >= 600:
        return "NEEDS WORK", f"{wc} words — below 900 threshold"
    else:
        return "FAIL", f"Only {wc} words — well below 600-word minimum"


def score_criterion_3(data):
    """GCC / Oman Local Relevance."""
    body_lower = data["body_text"].lower()
    title_lower = data["title"].lower()
    
    found = []
    for kw in LOCAL_KEYWORDS:
        count = len(re.findall(r'\b' + re.escape(kw) + r'\b', body_lower))
        if count > 0:
            found.append((kw, count))
    
    total_mentions = sum(c for _, c in found)
    unique_terms = len(found)
    
    # Check if local refs are ONLY in title
    title_only = all(kw in title_lower for kw, _ in found) and unique_terms <= 2
    
    if unique_terms >= 3 and not title_only:
        return "PASS", f"{unique_terms} local terms woven naturally ({total_mentions} total mentions)"
    elif unique_terms >= 1:
        if title_only:
            return "NEEDS WORK", "Local refs only in title/headline, not woven into body"
        return "NEEDS WORK", f"Only {unique_terms}-{total_mentions} local reference(s) found"
    else:
        return "FAIL", "Zero local GCC/Oman references — generic article"


def score_criterion_4(data):
    """Structured for LLM Citation."""
    h2_count = len(data["h2_tags"])
    body = data["body_text"]
    
    # Check for direct quotable answers: "X is Y", "To do X, you need Y"
    quotable_patterns = [
        r'[A-Z][^.]{5,50} is [a-z][^.]{5,60}\.',
        r'[A-Z][^.]{5,50} means [a-z][^.]{5,60}\.',
        r'To [a-z][^,]{5,40}, you (need|must|should|can)[^.]{5,60}\.',
        r'The (best|fastest|easiest|most) way to[^.]{10,80}\.',
        r'A [A-Za-z ]+ is (a |an |the )?[a-z][^.]{10,80}\.',
    ]
    quotable_count = sum(1 for p in quotable_patterns if re.search(p, body))
    
    # Check for specific numbers/stats
    stat_count = len(re.findall(r'\b\d+[\.,]?\d*\s*(%|percent|omr|usd|\$|rial|x\b)', body.lower()))
    
    if h2_count >= 3 and quotable_count >= 1 and stat_count >= 1:
        return "PASS", f"{h2_count} H2s, {quotable_count} quotable answers, {stat_count} stats"
    elif h2_count == 0:
        return "FAIL", "No H2 subheadings — unstructured prose, not LLM-citable"
    elif h2_count < 3 or quotable_count == 0 or stat_count == 0:
        missing = []
        if h2_count < 3: missing.append(f"only {h2_count} H2s")
        if quotable_count == 0: missing.append("no quotable answers")
        if stat_count == 0: missing.append("no stats/numbers")
        return "NEEDS WORK", "; ".join(missing)
    
    return "NEEDS WORK", f"{h2_count} H2s but structure could be stronger"


def score_criterion_5(data):
    """Call to Action."""
    last_200 = data["last_200"].lower()
    links = data["links"]
    
    # Check for CTA links in all links
    cta_links = [l for l in links if any(re.search(p, l["href"].lower()) for p in CTA_LINK_PATTERNS)]
    
    # Check strong CTA text in last 200 words
    strong_cta = any(re.search(p, last_200) for p in STRONG_CTA_TEXT)
    
    # Check for any CTA text
    weak_cta = bool(re.search(r'\b(learn more|get started|contact|reach out|book|schedule|demo|free|whatsapp)\b', last_200))
    
    if strong_cta and cta_links:
        return "PASS", "Clear specific CTA with action verb and working link"
    elif weak_cta and cta_links:
        return "NEEDS WORK", "CTA present but text is vague or generic"
    elif strong_cta and not cta_links:
        return "NEEDS WORK", "Good CTA text but no clickable link found"
    elif weak_cta:
        return "NEEDS WORK", "Weak CTA text, no strong action link"
    else:
        return "FAIL", "No CTA found in last 200 words of article"


def score_criterion_6(data, all_meta_descs):
    """Meta Description Quality."""
    meta = data["meta_desc"]
    
    if not meta:
        return "FAIL", "Meta description is completely missing"
    
    # Check for the specific bad pattern
    if re.search(r"supercharge your business", meta.lower()):
        return "FAIL", "Contains 'Supercharge your business' — flagged generic filler"
    
    # Check for duplicates
    current_count = all_meta_descs.count(meta)
    if current_count > 1:
        return "FAIL", "Duplicate meta description — identical to another article"
    
    length = len(meta)
    has_keyword = any(kw in meta.lower() for kw in ["oman", "muscat", "gcc", "ai", "whatsapp", 
                                                      "automation", "business", "cost", "roi",
                                                      "guide", "how to"])
    
    if 130 <= length <= 160 and has_keyword:
        return "PASS", f"{length} chars, contains specific keyword/benefit"
    elif length < 100:
        return "NEEDS WORK", f"Too short at {length} chars — below 100"
    elif length > 170:
        return "NEEDS WORK", f"Too long at {length} chars — over 170"
    elif not has_keyword:
        return "NEEDS WORK", f"{length} chars but too generic, lacks specific keyword"
    else:
        return "NEEDS WORK", f"{length} chars — acceptable but not optimal (130–160 target)"


def score_criterion_7(data, all_articles):
    """Duplicate / Overlap Risk."""
    title = data["title"].lower()
    h2s = [h.lower() for h in data["h2_tags"]]
    
    # Extract core topic words (nouns, keywords)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
                  "of", "with", "by", "from", "how", "why", "what", "when", "is", "are",
                  "your", "our", "their", "its", "this", "that", "these", "those",
                  "can", "will", "do", "does", "did", "be", "been", "being", "have",
                  "has", "had", "not", "no", "more", "most", "all", "any", "both"}
    
    title_words = set(w for w in re.sub(r'[^\w\s]', '', title).split() if w not in stop_words and len(w) > 3)
    
    overlapping = []
    for other in all_articles:
        if other["filepath"] == data["filepath"]:
            continue
        other_title = other["title"].lower()
        other_words = set(w for w in re.sub(r'[^\w\s]', '', other_title).split() 
                         if w not in stop_words and len(w) > 3)
        
        # Jaccard similarity
        intersection = title_words & other_words
        union = title_words | other_words
        if union:
            similarity = len(intersection) / len(union)
            if similarity > 0.45:
                overlapping.append((other["filepath"].name, similarity))
    
    if not overlapping:
        return "PASS", "Unique angle, no substantial topic overlap detected"
    elif len(overlapping) == 1:
        best = max(overlapping, key=lambda x: x[1])
        return "NEEDS WORK", f"Overlaps with {best[0][:40]} ({best[1]:.0%} similarity)"
    else:
        best = max(overlapping, key=lambda x: x[1])
        return "FAIL", f"Overlaps with {len(overlapping)} articles; highest: {best[0][:30]} ({best[1]:.0%})"


def get_overall_rating(scores):
    """Calculate overall rating based on scores."""
    score_map = {"PASS": 2, "NEEDS WORK": 1, "FAIL": 0}
    total = sum(score_map[s] for s, _ in scores)
    max_score = 14  # 7 criteria × 2
    
    ratio = total / max_score
    fail_count = sum(1 for s, _ in scores if s == "FAIL")
    
    if fail_count == 0 and ratio >= 0.85:
        return "STRONG"
    elif fail_count <= 1 and ratio >= 0.64:
        return "ACCEPTABLE"
    elif fail_count <= 2 and ratio >= 0.43:
        return "NEEDS REVISION"
    else:
        return "REWRITE RECOMMENDED"


def get_top_fix(scores, data):
    """Determine the single most impactful fix."""
    criteria_names = [
        "Title & Hook", "Word Count", "GCC/Oman Relevance",
        "LLM Citation Structure", "Call to Action", "Meta Description", "Duplicate Risk"
    ]
    
    # Priority order for fixes (most impactful first)
    priority = [2, 1, 5, 3, 4, 6, 0]  # GCC, WordCount, CTA, LLM, CTA, Meta, Title
    
    for idx in priority:
        s, reason = scores[idx]
        if s == "FAIL":
            return f"[{criteria_names[idx]}] {reason}"
    
    for idx in priority:
        s, reason = scores[idx]
        if s == "NEEDS WORK":
            return f"[{criteria_names[idx]}] {reason}"
    
    return "All criteria passing — minor polish only"


def format_article_report(n, data, scores, overall, top_fix):
    """Format a single article report."""
    s1, r1 = scores[0]
    s2, r2 = scores[1]
    s3, r3 = scores[2]
    s4, r4 = scores[3]
    s5, r5 = scores[4]
    s6, r6 = scores[5]
    s7, r7 = scores[6]
    
    meta_display = data["meta_desc"] if data["meta_desc"] else "MISSING"
    if len(meta_display) > 160:
        meta_display = meta_display[:157] + "..."
    
    return f"""---
ARTICLE #{n}
File: blog/en/{data['filepath'].name}
Title tag: {data['title'] or 'MISSING — CRITICAL ERROR'}
H1: {data['h1'] or 'MISSING'}
Meta description: {meta_display}
Word count: {data['word_count']}

SCORES:
1. Title & Hook:        {s1} — {r1}
2. Word Count & Depth:  {s2} — {r2}
3. GCC/Oman Relevance:  {s3} — {r3}
4. LLM Citation:        {s4} — {r4}
5. Call to Action:      {s5} — {r5}
6. Meta Description:    {s6} — {r6}
7. Duplicate Risk:      {s7} — {r7}

OVERALL: {overall}
#1 FIX:  {top_fix}
"""


def main():
    print("=== AI Profit Lab — Article Quality Audit ===")
    print(f"Scanning: {BLOG_DIR}")
    
    # Collect all HTML files (sorted)
    files = sorted([f for f in BLOG_DIR.glob("*.html")])
    print(f"Found {len(files)} article files\n")
    
    # First pass: parse all files to get meta descs for duplicate detection
    print("Pass 1: Parsing all files...")
    all_data = []
    for f in files:
        try:
            parsed = parse_html(f)
            parsed["filepath"] = f
            all_data.append(parsed)
        except Exception as e:
            print(f"  ERROR parsing {f.name}: {e}")
            all_data.append({
                "filepath": f, "title": "PARSE ERROR", "h1": "", 
                "meta_desc": "", "h2_tags": [], "word_count": 0,
                "body_text": "", "full_text": "", "last_200": "",
                "first_100": "", "links": [], "schema": [], "raw_html": ""
            })
    
    all_meta_descs = [d["meta_desc"] for d in all_data]
    print(f"Pass 1 complete. Auditing {len(all_data)} articles...\n")
    
    # Second pass: score all articles
    results = []
    checkpoint_text = ""
    
    for i, data in enumerate(all_data, 1):
        n = i
        print(f"  Auditing #{n}: {data['filepath'].name}")
        
        scores = [
            score_criterion_1(data),
            score_criterion_2(data),
            score_criterion_3(data),
            score_criterion_4(data),
            score_criterion_5(data),
            score_criterion_6(data, all_meta_descs),
            score_criterion_7(data, all_data),
        ]
        
        overall = get_overall_rating(scores)
        top_fix = get_top_fix(scores, data)
        
        result = {
            "n": n,
            "data": data,
            "scores": scores,
            "overall": overall,
            "top_fix": top_fix
        }
        results.append(result)
        
        report_block = format_article_report(n, data, scores, overall, top_fix)
        checkpoint_text += report_block
        
        # Save checkpoint every 10 articles
        if i % 10 == 0:
            checkpoint_path = OUTPUT_DIR / f"checkpoint_articles_{i}.md"
            with open(checkpoint_path, "w") as cf:
                cf.write(f"# Article Audit Checkpoint — Articles 1–{i}\n\n")
                cf.write(checkpoint_text)
            print(f"\n  ✅ Checkpoint saved: articles 1–{i}\n")
    
    print("\nGenerating final summary...\n")
    
    # Build summary table
    table_rows = []
    for r in results:
        fname = r["data"]["filepath"].name
        title_short = r["data"]["title"][:55] + "..." if len(r["data"]["title"]) > 55 else r["data"]["title"]
        fix_short = r["top_fix"][:60] + "..." if len(r["top_fix"]) > 60 else r["top_fix"]
        table_rows.append(f"| {r['n']} | {fname} | {title_short} | {r['overall']} | {fix_short} |")
    
    # Statistics
    totals = {"STRONG": 0, "ACCEPTABLE": 0, "NEEDS REVISION": 0, "REWRITE RECOMMENDED": 0}
    for r in results:
        totals[r["overall"]] += 1
    total_n = len(results)
    
    # Failure patterns per criterion
    crit_names = ["Title & Hook", "Word Count & Depth", "GCC/Oman Relevance", 
                  "LLM Citation", "Call to Action", "Meta Description", "Duplicate Risk"]
    crit_fails = [0] * 7
    crit_needs_work = [0] * 7
    for r in results:
        for i, (s, _) in enumerate(r["scores"]):
            if s == "FAIL":
                crit_fails[i] += 1
            elif s == "NEEDS WORK":
                crit_needs_work[i] += 1
    
    crit_issues = [(crit_fails[i] + crit_needs_work[i], crit_names[i], crit_fails[i], crit_needs_work[i]) 
                   for i in range(7)]
    crit_issues.sort(reverse=True)
    
    # Duplicate clusters
    clusters = {}
    processed = set()
    for r in results:
        fname = r["data"]["filepath"].name
        if fname in processed:
            continue
        for s, reason in [r["scores"][6]]:
            if s in ("FAIL", "NEEDS WORK") and "overlaps with" in reason.lower():
                # Find related articles
                cluster_key = None
                for body_kw in ["whatsapp", "oman", "ai automation", "pdpl", "vision 2040", 
                                 "real estate", "clinic", "hypermarket", "retail", "ceo dashboard",
                                 "logistics", "data", "sovereign"]:
                    if body_kw in r["data"]["title"].lower():
                        cluster_key = body_kw.upper()
                        break
                if cluster_key:
                    if cluster_key not in clusters:
                        clusters[cluster_key] = []
                    clusters[cluster_key].append(f"  - {fname} — \"{r['data']['title'][:60]}\"")
                    processed.add(fname)
    
    # Quick wins: NEEDS REVISION or REWRITE with at most 1 FAIL and many NEEDS WORK
    quick_wins = []
    for r in results:
        fail_count = sum(1 for s, _ in r["scores"] if s == "FAIL")
        needs_work_count = sum(1 for s, _ in r["scores"] if s == "NEEDS WORK")
        if r["overall"] in ("NEEDS REVISION", "ACCEPTABLE") and fail_count <= 1 and needs_work_count >= 2:
            # Score by word count (higher = more traffic potential)
            quick_wins.append((r["data"]["word_count"], r))
    quick_wins.sort(reverse=True)
    quick_wins = quick_wins[:5]
    
    # Build final report
    today = date.today().strftime("%Y-%m-%d")
    
    final_report = f"""# AI Profit Lab — Full Article Quality Audit
**Date:** {today}
**Total Articles:** {total_n}
**Site:** aiprofitlab.io

---

## PART 1 — INDIVIDUAL ARTICLE AUDITS

{checkpoint_text}

---

## PART 2 — FINAL SUMMARY

### 4A — SUMMARY TABLE

| # | File | Title | Overall | #1 Fix |
|---|------|-------|---------|--------|
"""
    final_report += "\n".join(table_rows)
    
    final_report += f"""

---

### 4B — STATISTICS

- **Total articles audited:** {total_n}
- **STRONG:** {totals['STRONG']} ({totals['STRONG']/total_n*100:.0f}%)
- **ACCEPTABLE:** {totals['ACCEPTABLE']} ({totals['ACCEPTABLE']/total_n*100:.0f}%)
- **NEEDS REVISION:** {totals['NEEDS REVISION']} ({totals['NEEDS REVISION']/total_n*100:.0f}%)
- **REWRITE RECOMMENDED:** {totals['REWRITE RECOMMENDED']} ({totals['REWRITE RECOMMENDED']/total_n*100:.0f}%)

---

### 4C — MOST COMMON FAILURE PATTERNS

Top 3 criteria with the most issues across all articles:

"""
    
    for rank, (total_issues, cname, fails, needs_work) in enumerate(crit_issues[:3], 1):
        examples = {
            "Title & Hook": "Add a specific number, outcome, or location to the title (e.g., '5 Ways Muscat Clinics Save 3 Hours/Day with WhatsApp AI')",
            "Word Count & Depth": "Expand thin articles to 900+ words by adding a real case study, step-by-step walkthrough, or FAQ section",
            "GCC/Oman Relevance": "Weave in 3+ Oman/GCC references: name a Muscat neighbourhood, cite Vision 2040, reference OMR pricing",
            "LLM Citation": "Add 3+ H2 subheadings and at least one sentence in 'X is Y' format with a specific statistic",
            "Call to Action": "End with 'Book a free 30-minute demo → [WhatsApp link]' — specific action + clickable link",
            "Meta Description": "Write a 130–160 char meta that starts with the key benefit, not the brand name",
            "Duplicate Risk": "Merge near-duplicate articles into a single pillar page or sharpen the angle (e.g., one for clinics, one for real estate)"
        }
        fix_example = examples.get(cname, "Review and strengthen this criterion")
        final_report += f"""**#{rank}. {cname}** — {fails} FAILs + {needs_work} NEEDS WORK = {total_issues} issues total
- Fix example: *{fix_example}*

"""
    
    final_report += """---

### 4D — DUPLICATE / OVERLAP CLUSTERS

Articles grouped by overlapping core topics (merge or differentiate):

"""
    
    # Build clusters more comprehensively from title analysis
    topic_clusters = {
        "WHATSAPP AUTOMATION": [],
        "OMAN AI / VISION 2040": [],
        "CEO DASHBOARD / REPORTING": [],
        "PDPL / DATA PRIVACY": [],
        "RETAIL / HYPERMARKET": [],
        "CLINIC / MEDICAL": [],
        "REAL ESTATE": [],
        "LOGISTICS / FLEET": [],
        "AI COSTS / ROI": [],
        "SOVEREIGN AI / DATA BORDERS": [],
    }
    
    kw_to_cluster = {
        "whatsapp": "WHATSAPP AUTOMATION",
        "vision 2040": "OMAN AI / VISION 2040",
        "vision2040": "OMAN AI / VISION 2040",
        "national ai": "OMAN AI / VISION 2040",
        "oman gpt": "OMAN AI / VISION 2040",
        "maeen": "OMAN AI / VISION 2040",
        "omantel": "OMAN AI / VISION 2040",
        "oman lens": "OMAN AI / VISION 2040",
        "special zone": "OMAN AI / VISION 2040",
        "ceo dashboard": "CEO DASHBOARD / REPORTING",
        "dashboard": "CEO DASHBOARD / REPORTING",
        "pdpl": "PDPL / DATA PRIVACY",
        "data privacy": "PDPL / DATA PRIVACY",
        "data sovereignty": "SOVEREIGN AI / DATA BORDERS",
        "sovereign": "SOVEREIGN AI / DATA BORDERS",
        "self-hosted": "SOVEREIGN AI / DATA BORDERS",
        "retail": "RETAIL / HYPERMARKET",
        "hypermarket": "RETAIL / HYPERMARKET",
        "shrinkage": "RETAIL / HYPERMARKET",
        "clinic": "CLINIC / MEDICAL",
        "dentist": "CLINIC / MEDICAL",
        "medical": "CLINIC / MEDICAL",
        "real estate": "REAL ESTATE",
        "property": "REAL ESTATE",
        "logistics": "LOGISTICS / FLEET",
        "fleet": "LOGISTICS / FLEET",
        "roi": "AI COSTS / ROI",
        "cost": "AI COSTS / ROI",
    }
    
    for r in results:
        title_lower = r["data"]["title"].lower()
        fname = r["data"]["filepath"].name
        assigned = False
        for kw, cluster in kw_to_cluster.items():
            if kw in title_lower or kw in fname.lower():
                topic_clusters[cluster].append(f"  - `{fname}` — \"{r['data']['title'][:65]}\"")
                assigned = True
                break
    
    for cluster_name, items in topic_clusters.items():
        if len(items) >= 2:
            final_report += f"**{cluster_name} CLUSTER ({len(items)} articles):**\n"
            final_report += "\n".join(items)
            if len(items) > 5:
                final_report += f"\n  → ⚠️ Recommendation: Consolidate into 1–2 pillar articles or assign distinct sub-niches per article.\n\n"
            elif len(items) >= 2:
                final_report += f"\n  → Recommendation: Ensure each article targets a distinct audience segment or search intent.\n\n"
    
    final_report += """---

### 4E — QUICK WINS (Top 5 articles to fix first)

Articles where a small fix would have the highest impact (ranked by traffic potential × effort):

"""
    
    for rank, (wc, r) in enumerate(quick_wins, 1):
        fail_count = sum(1 for s, _ in r["scores"] if s == "FAIL")
        needs_work_count = sum(1 for s, _ in r["scores"] if s == "NEEDS WORK")
        final_report += f"""**#{rank}. `{r['data']['filepath'].name}`**
- Title: {r['data']['title']}
- Overall: {r['overall']} | Word count: {wc} | FAILs: {fail_count} | NEEDS WORK: {needs_work_count}
- Top fix: {r['top_fix']}

"""
    
    final_report += f"""---

*Report generated: {today} | AI Profit Lab — aiprofitlab.io | International Gulf Lotus SPC*
"""
    
    # Save final report
    final_path = OUTPUT_DIR / f"ARTICLE_AUDIT_{today}.md"
    with open(final_path, "w") as f:
        f.write(final_report)
    
    print(f"\n✅ Final audit report saved: {final_path}")
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Total audited: {total_n}")
    print(f"   STRONG:              {totals['STRONG']} ({totals['STRONG']/total_n*100:.0f}%)")
    print(f"   ACCEPTABLE:          {totals['ACCEPTABLE']} ({totals['ACCEPTABLE']/total_n*100:.0f}%)")
    print(f"   NEEDS REVISION:      {totals['NEEDS REVISION']} ({totals['NEEDS REVISION']/total_n*100:.0f}%)")
    print(f"   REWRITE RECOMMENDED: {totals['REWRITE RECOMMENDED']} ({totals['REWRITE RECOMMENDED']/total_n*100:.0f}%)")
    
    print(f"\n📋 TOP FAILURE CRITERIA:")
    for total_issues, cname, fails, nw in crit_issues[:3]:
        print(f"   {cname}: {fails} FAILs + {nw} NEEDS WORK = {total_issues} issues")
    
    return final_path


if __name__ == "__main__":
    main()
