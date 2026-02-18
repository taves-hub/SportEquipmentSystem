#!/usr/bin/env python3
"""
Convert Storekeeper Manual from Markdown to PDF using reportlab
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import re

# Input and output paths
input_file = Path('STOREKEEPER_MANUAL.md')
output_file = Path('STOREKEEPER_MANUAL.pdf')

# Read the markdown file
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Create PDF
doc = SimpleDocTemplate(
    str(output_file),
    pagesize=A4,
    rightMargin=0.75*inch,
    leftMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
)

# Create styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='Justify',
    parent=styles['Normal'],
    alignment=TA_JUSTIFY,
    fontSize=11,
    leading=14,
))

styles.add(ParagraphStyle(
    name='Title1',
    parent=styles['Heading1'],
    fontSize=28,
    textColor=colors.HexColor('#1a5f0a'),
    spaceAfter=12,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold',
))

styles.add(ParagraphStyle(
    name='Heading2_Custom',
    parent=styles['Heading2'],
    fontSize=20,
    textColor=colors.HexColor('#2d7a1f'),
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold',
))

styles.add(ParagraphStyle(
    name='Heading3_Custom',
    parent=styles['Heading3'],
    fontSize=14,
    textColor=colors.HexColor('#3a8f2f'),
    spaceAfter=10,
    spaceBefore=10,
    fontName='Helvetica-Bold',
))

# Parse markdown and create elements
elements = []

# Title
elements.append(Paragraph("Sports Equipment Management System", styles['Title1']))
elements.append(Paragraph("Storekeeper User Manual", styles['Title1']))
elements.append(Spacer(1, 0.5*inch))

# Split content by sections
lines = content.split('\n')
i = 0
while i < len(lines):
    line = lines[i]
    
    # Skip empty lines at the beginning
    if not line.strip():
        i += 1
        continue
    
    # Title 1 (single #)
    if line.startswith('# ') and not line.startswith('## '):
        title = line[2:].strip()
        if title not in ["Sports Equipment Management System", "Storekeeper User Manual"]:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(title, styles['Heading2_Custom']))
            elements.append(Spacer(1, 0.1*inch))
    
    # Title 2 (double ##)
    elif line.startswith('## '):
        title = line[3:].strip()
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph(title, styles['Heading3_Custom']))
        elements.append(Spacer(1, 0.08*inch))
    
    # Title 3 (triple ###)
    elif line.startswith('### '):
        title = line[4:].strip()
        elements.append(Paragraph(f"<b>{title}</b>", styles['Normal']))
        elements.append(Spacer(1, 0.05*inch))
    
    # Horizontal rule
    elif line.strip() == '---':
        elements.append(Spacer(1, 0.1*inch))
        from reportlab.platypus import HRFlowable
        elements.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1a5f0a')))
        elements.append(Spacer(1, 0.1*inch))
    
    # Regular paragraph
    elif line.strip() and not line.startswith('#') and not line.startswith('|'):
        # Clean up markdown formatting
        text = line.strip()
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'`(.*?)`', r'<font face="Courier" size="9">\1</font>', text)
        
        elements.append(Paragraph(text, styles['Justify']))
        elements.append(Spacer(1, 0.08*inch))
    
    # Bullet points
    elif line.startswith('- ') or line.startswith('* '):
        bullet_text = line[2:].strip()
        bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
        bullet_text = re.sub(r'`(.*?)`', r'<font face="Courier" size="9">\1</font>', bullet_text)
        elements.append(Paragraph(f"• {bullet_text}", styles['Justify']))
        elements.append(Spacer(1, 0.05*inch))
    
    # Numbered list
    elif re.match(r'^\d+\.\s', line):
        list_text = re.sub(r'^\d+\.\s', '', line).strip()
        list_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', list_text)
        list_text = re.sub(r'`(.*?)`', r'<font face="Courier" size="9">\1</font>', list_text)
        elements.append(Paragraph(f"• {list_text}", styles['Justify']))
        elements.append(Spacer(1, 0.05*inch))
    
    i += 1

# Build PDF
try:
    doc.build(elements)
    print(f"✓ Successfully converted to PDF!")
    print(f"  File location: {output_file.absolute()}")
    print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")
except Exception as e:
    print(f"✗ Error converting to PDF: {e}")
    import traceback
    traceback.print_exc()
