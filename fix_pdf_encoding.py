#!/usr/bin/env python3
"""Fix Unicode encoding issues in generate_system_docs_pdf.py"""

import re

# Read the file
with open('generate_system_docs_pdf.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace special characters with ASCII equivalents
replacements = {
    '•': '-',      # Bullet point
    '✓': '[OK]',   # Checkmark
    '↓': '|',      # Down arrow
    '├': '|',      # Box drawing
    '└': '|',      # Box drawing
    '→': '->',     # Right arrow
    '═': '=',      # Double line
    '║': '|',      # Vertical line
    '─': '-',      # Horizontal line
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Write back
with open('generate_system_docs_pdf.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed encoding issues - running PDF generation...")

# Now run the PDF generator
import subprocess
result = subprocess.run(['python', 'generate_system_docs_pdf.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
