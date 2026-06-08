#!/usr/bin/env python3
import sys
import os
import re

def check_html_structure(content):
    issues = []
    if not re.search(r'<h1[^>]*>', content, re.IGNORECASE):
        issues.append("Missing <h1> tag. GEO requires clear primary headings.")
    if content.count('<h1') > 1:
        issues.append("Multiple <h1> tags found. Only one <h1> is recommended.")
    if not re.search(r'<meta\s+name=["\']description["\']', content, re.IGNORECASE):
        issues.append("Missing meta description.")
    return issues

def check_markdown_structure(content):
    issues = []
    if not re.search(r'^#\s+', content, re.MULTILINE):
        issues.append("Missing H1 heading (#). GEO requires a clear primary title.")
    if len(re.findall(r'^#\s+', content, re.MULTILINE)) > 1:
        issues.append("Multiple H1 headings found. Use only one # heading.")
    if not re.search(r'\*\*(.*?)\*\*', content):
        issues.append("No bold text found. LLMs favor bolded key concepts for entity extraction.")
    if not re.search(r'^[-*]\s+', content, re.MULTILINE):
        issues.append("No lists found. Structured lists improve GEO performance.")
    return issues

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_structure.py <file_path>")
        sys.exit(1)
        
    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    ext = os.path.splitext(filepath)[1].lower()
    print(f"Scanning {filepath} for structural layout anomalies...")
    
    issues = []
    if ext in ['.html', '.htm']:
        issues = check_html_structure(content)
    elif ext in ['.md', '.mdx']:
        issues = check_markdown_structure(content)
    else:
        print("Unsupported file type. Please provide a Markdown (.md) or HTML (.html) file.")
        sys.exit(0)
        
    if issues:
        print("\nStructural Anomalies Detected:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("\nNo structural anomalies found. Layout is optimized for GEO.")

if __name__ == "__main__":
    main()
