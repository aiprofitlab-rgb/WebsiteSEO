#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path
from html.parser import HTMLParser

BLOG_DIR = Path("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/en")
OUTPUT_FILE = Path("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/.tmp/audit/blog_snippets.json")

class HTMLStripper(HTMLParser):
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
        self.article_text_parts = []
        self.in_article = False
        self.article_depth = 0
        self.main_text_parts = []
        self.in_main = False
        self.full_text_parts = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.in_h1 = True
        if tag == "meta":
            if attrs_dict.get("name", "").lower() == "description":
                self.meta_desc = attrs_dict.get("content", "")
        if tag in self.skip_tags:
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
        if tag in self.skip_tags:
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
        if self.in_skip:
            return
        if self.in_title:
            self.title += data
        if self.in_h1:
            self.h1 += data
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
        if self.article_text_parts:
            return " ".join(self.article_text_parts)
        elif self.main_text_parts:
            return " ".join(self.main_text_parts)
        else:
            return " ".join(self.full_text_parts)

def parse_html(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    parser = HTMLStripper()
    parser.feed(content)
    body_text = parser.get_body_text()
    # Get first 300 words
    words = body_text.split()
    snippet = " ".join(words[:300])
    return {
        "filename": filepath.name,
        "title": parser.get_clean_title(),
        "h1": parser.get_clean_h1(),
        "meta_desc": parser.meta_desc,
        "snippet": snippet
    }

def main():
    files = sorted([f for f in BLOG_DIR.glob("*.html")])
    results = []
    for f in files:
        try:
            results.append(parse_html(f))
        except Exception as e:
            print(f"Error parsing {f.name}: {e}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2, ensure_ascii=False)
    print(f"Extracted snippets for {len(results)} articles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
