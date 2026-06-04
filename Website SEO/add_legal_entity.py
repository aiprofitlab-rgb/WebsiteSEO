"""
add_legal_entity.py
Adds "International Gulf Lotus SPC" legal entity branding across the site:
1. Footer copyright lines (English & Arabic variants)
2. Schema.org JSON-LD legalName property
"""

import os
import re

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public_html")

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changes = []

    # =========================================================================
    # 1. FOOTER COPYRIGHT — English variants
    # =========================================================================

    # Pattern A: "Profit Lab • All Rights Reserved • Muscat, Oman"
    content = content.replace(
        'Profit Lab • All Rights Reserved • Muscat, Oman',
        'Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved • Muscat, Oman'
    )

    # Pattern B: "Profit Lab • All Rights Reserved • Serving the GCC"
    content = content.replace(
        'Profit Lab • All Rights Reserved • Serving the GCC',
        'Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved • Serving the GCC'
    )

    # =========================================================================
    # 2. FOOTER COPYRIGHT — Arabic variants
    # =========================================================================

    # Pattern A: "Profit Lab • جميع الحقوق محفوظة • مسقط، عمان"
    content = content.replace(
        'Profit Lab • جميع الحقوق محفوظة • مسقط، عمان',
        'Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة • مسقط، عمان'
    )

    # Pattern B: "Profit Lab • جميع الحقوق محفوظة • نخدم دول الخليج"
    content = content.replace(
        'Profit Lab • جميع الحقوق محفوظة • نخدم دول الخليج',
        'Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة • نخدم دول الخليج'
    )

    # =========================================================================
    # 3. SCHEMA.ORG — Add legalName after "name": "AI Profit Lab"
    #    Only in JSON-LD blocks (ProfessionalService and Organization schemas)
    # =========================================================================

    # Add legalName after "name": "AI Profit Lab" where it doesn't already exist
    # We need to be careful to only add it once per occurrence and not inside Article schemas
    if '"legalName"' not in content:
        # Pattern: "name": "AI Profit Lab" followed by a comma and newline (in JSON-LD)
        # We match it in the context of ProfessionalService or Organization schemas
        content = re.sub(
            r'("@type":\s*"ProfessionalService",\s*\n\s*"name":\s*"AI Profit Lab")',
            r'\1,\n  "legalName": "International Gulf Lotus SPC"',
            content
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Updated: {os.path.relpath(filepath, BASE_DIR)}")
        return True
    else:
        return False


def main():
    updated_count = 0
    scanned_count = 0

    for root, dirs, files in os.walk(BASE_DIR):
        for fname in files:
            if fname.endswith('.html'):
                filepath = os.path.join(root, fname)
                scanned_count += 1
                if process_file(filepath):
                    updated_count += 1

    print(f"\nDone. Scanned {scanned_count} HTML files, updated {updated_count}.")


if __name__ == "__main__":
    main()
