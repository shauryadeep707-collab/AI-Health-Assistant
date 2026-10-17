"""
Script to generate official PDF and high-resolution PNG image
for all System Login Credentials, User Accounts, and Passwords.
Stores output in the credentials/ folder.
"""

import os
import sys

# Ensure reportlab and PIL are available
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image, ImageDraw, ImageFont

CREDENTIALS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'credentials'))
os.makedirs(CREDENTIALS_DIR, exist_ok=True)

def generate_pdf():
    pdf_path = os.path.join(CREDENTIALS_DIR, 'SYSTEM_LOGIN_PASSWORDS.pdf')
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f766e'),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )

    bold_body = ParagraphStyle(
        'TableBodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    code_style = ParagraphStyle(
        'TableCode',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0957d0')
    )

    pass_style = ParagraphStyle(
        'TablePass',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#b91c1c')
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("AI Health Assistant – System Access &amp; Credentials Key", title_style))
    elements.append(Paragraph("CONFIDENTIAL REFERENCE SHEET &bull; Keep secure &bull; Not for public display on website", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f766e'), spaceAfter=14))

    # SECTION 1: MASTER SUMMARY TABLE
    elements.append(Paragraph("1. Primary Demonstration Accounts (Quick Access)", section_heading))

    summary_data = [
        [
            Paragraph("<b>Role / Access</b>", bold_body),
            Paragraph("<b>Name</b>", bold_body),
            Paragraph("<b>Email (Login ID)</b>", bold_body),
            Paragraph("<b>Password</b>", bold_body),
            Paragraph("<b>Direct Portal URL</b>", bold_body)
        ],
        [
            Paragraph("🛡️ <b>Administrator</b>", bold_body),
            Paragraph("Admin User", body_style),
            Paragraph("admin@demo.com", code_style),
            Paragraph("Admin@123", pass_style),
            Paragraph("/pages/admin.html", body_style)
        ],
        [
            Paragraph("👨‍⚕️ <b>Doctor (General)</b>", bold_body),
            Paragraph("Dr. Amit Verma (MBBS, MD)", body_style),
            Paragraph("doctor@demo.com", code_style),
            Paragraph("Doctor@123", pass_style),
            Paragraph("/pages/login.html", body_style)
        ],
        [
            Paragraph("👨‍⚕️ <b>Doctor (ENT)</b>", bold_body),
            Paragraph("Dr. Sneha Patel (MBBS, MS)", body_style),
            Paragraph("doctor2@demo.com", code_style),
            Paragraph("Doctor@123", pass_style),
            Paragraph("/pages/login.html", body_style)
        ],
        [
            Paragraph("👨‍⚕️ <b>Doctor (Pulmono)</b>", bold_body),
            Paragraph("Dr. Rajesh Kumar (MBBS, MD)", body_style),
            Paragraph("doctor3@demo.com", code_style),
            Paragraph("Doctor@123", pass_style),
            Paragraph("/pages/login.html", body_style)
        ],
        [
            Paragraph("👤 <b>Patient (General)</b>", bold_body),
            Paragraph("Rahul Sharma (28y, M)", body_style),
            Paragraph("patient@demo.com", code_style),
            Paragraph("Patient@123", pass_style),
            Paragraph("/pages/login.html", body_style)
        ],
        [
            Paragraph("👤 <b>Patient (Asthma)</b>", bold_body),
            Paragraph("Priya Gupta (32y, F)", body_style),
            Paragraph("patient2@demo.com", code_style),
            Paragraph("Patient@123", pass_style),
            Paragraph("/pages/login.html", body_style)
        ]
    ]

    summary_table = Table(summary_data, colWidths=[110, 120, 115, 80, 95])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # SECTION 2: ALL REGISTERED DOCTOR PROFILES
    elements.append(Paragraph("2. Complete Verified Specialist Doctors Directory (12 Doctors)", section_heading))

    doc_rows = [
        [
            Paragraph("<b>#</b>", bold_body),
            Paragraph("<b>Doctor Name &amp; Degrees</b>", bold_body),
            Paragraph("<b>Specialization</b>", bold_body),
            Paragraph("<b>Email</b>", bold_body),
            Paragraph("<b>Password</b>", bold_body),
            Paragraph("<b>Fee / City</b>", bold_body)
        ],
        [Paragraph("1", body_style), Paragraph("Dr. Amit Verma, MBBS, MD", bold_body), Paragraph("General Physician", body_style), Paragraph("doctor@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹500 / Dehradun", body_style)],
        [Paragraph("2", body_style), Paragraph("Dr. Sneha Patel, MBBS, MS", bold_body), Paragraph("ENT Specialist", body_style), Paragraph("doctor2@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹600 / Dehradun", body_style)],
        [Paragraph("3", body_style), Paragraph("Dr. Rajesh Kumar, MBBS, MD", bold_body), Paragraph("Pulmonologist", body_style), Paragraph("doctor3@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹700 / Dehradun", body_style)],
        [Paragraph("4", body_style), Paragraph("Dr. Meera Singh, MBBS, DNB", bold_body), Paragraph("Pediatrician", body_style), Paragraph("doctor4@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹550 / Dehradun", body_style)],
        [Paragraph("5", body_style), Paragraph("Dr. Arun Joshi, MBBS, MD", bold_body), Paragraph("Dermatologist", body_style), Paragraph("doctor5@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹650 / Dehradun", body_style)],
        [Paragraph("6", body_style), Paragraph("Dr. Kavita Rawat, MBBS, DM", bold_body), Paragraph("Cardiologist", body_style), Paragraph("doctor6@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹800 / Dehradun", body_style)],
        [Paragraph("7", body_style), Paragraph("Dr. Suresh Negi, MBBS", bold_body), Paragraph("General Physician", body_style), Paragraph("doctor7@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹450 / Dehradun", body_style)],
        [Paragraph("8", body_style), Paragraph("Dr. Anita Bhatt, MBBS, DM", bold_body), Paragraph("Neurologist", body_style), Paragraph("doctor8@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹850 / Dehradun", body_style)],
        [Paragraph("9", body_style), Paragraph("Dr. Vikram Chauhan, MBBS, MS", bold_body), Paragraph("Orthopedic", body_style), Paragraph("doctor9@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹600 / Dehradun", body_style)],
        [Paragraph("10", body_style), Paragraph("Dr. Pooja Sharma, MBBS, MD", bold_body), Paragraph("Gastroenterologist", body_style), Paragraph("doctor10@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹750 / Dehradun", body_style)],
        [Paragraph("11", body_style), Paragraph("Dr. Ravi Thapa, MBBS", bold_body), Paragraph("General Physician", body_style), Paragraph("doctor11@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹400 / Dehradun", body_style)],
        [Paragraph("12", body_style), Paragraph("Dr. Deepa Kandari, MBBS, MS", bold_body), Paragraph("Gynecologist", body_style), Paragraph("doctor12@demo.com", code_style), Paragraph("Doctor@123", pass_style), Paragraph("₹650 / Dehradun", body_style)]
    ]

    doc_table = Table(doc_rows, colWidths=[20, 150, 105, 110, 75, 60])
    doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(doc_table)
    elements.append(Spacer(1, 14))

    # SECTION 3: CLOUD DATABASE CREDENTIALS
    elements.append(Paragraph("3. Supabase Cloud PostgreSQL Database Key", section_heading))
    db_data = [
        [Paragraph("<b>Parameter</b>", bold_body), Paragraph("<b>Value / URI</b>", bold_body)],
        [Paragraph("Engine", body_style), Paragraph("PostgreSQL 15 (AWS ap-southeast-1)", body_style)],
        [Paragraph("Project Ref", body_style), Paragraph("fpoyfurmqvmqxzpqwszu", code_style)],
        [Paragraph("Database User", body_style), Paragraph("postgres.fpoyfurmqvmqxzpqwszu", code_style)],
        [Paragraph("Database Password", body_style), Paragraph("HealthProject@2026", pass_style)],
        [Paragraph("Connection Host", body_style), Paragraph("aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres", code_style)]
    ]
    db_table = Table(db_data, colWidths=[130, 390])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1'))
    ]))
    elements.append(db_table)

    doc.build(elements)
    print(f"[OK] Generated PDF: {pdf_path}")
    return pdf_path

def generate_image():
    img_path = os.path.join(CREDENTIALS_DIR, 'SYSTEM_LOGIN_PASSWORDS.png')
    
    # 1200 x 1400 high-res card
    width, height = 1200, 1350
    image = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(image)

    # Top Header banner
    draw.rectangle([(0, 0), (width, 140)], fill='#0f766e')
    
    # Fonts
    try:
        font_title = ImageFont.truetype('arial.ttf', 34)
        font_subtitle = ImageFont.truetype('arial.ttf', 18)
        font_h2 = ImageFont.truetype('arialbd.ttf', 22)
        font_regular = ImageFont.truetype('arial.ttf', 16)
        font_bold = ImageFont.truetype('arialbd.ttf', 16)
        font_code = ImageFont.truetype('consola.ttf', 16)
    except Exception:
        font_title = font_subtitle = font_h2 = font_regular = font_bold = font_code = ImageFont.load_default()

    draw.text((40, 30), "AI Health Assistant", fill='#ffffff', font=font_title)
    draw.text((40, 80), "CONFIDENTIAL CREDENTIALS & PASSWORDS REFERENCE SHEET", fill='#ccfbf1', font=font_subtitle)
    draw.text((40, 105), "Private key: Passwords removed from public web pages per security protocol", fill='#99f6e4', font=font_subtitle)

    y = 170

    # Section 1: Main Logins
    draw.text((40, y), "1. PRIMARY DEMO ACCOUNTS (Patient, Doctor, Admin)", fill='#0f766e', font=font_h2)
    y += 35

    # Card background for main logins
    draw.rounded_rectangle([(40, y), (width - 40, y + 260)], radius=12, fill='#f8fafc', outline='#cbd5e1', width=1)
    
    # Headers
    draw.text((60, y + 15), "ROLE", fill='#64748b', font=font_bold)
    draw.text((220, y + 15), "NAME", fill='#64748b', font=font_bold)
    draw.text((460, y + 15), "LOGIN EMAIL", fill='#64748b', font=font_bold)
    draw.text((750, y + 15), "PASSWORD", fill='#64748b', font=font_bold)
    draw.text((950, y + 15), "ACCESS PORTAL", fill='#64748b', font=font_bold)
    draw.line([(60, y + 42), (width - 60, y + 42)], fill='#cbd5e1', width=1)

    accounts = [
        ("🛡️ Administrator", "Admin User", "admin@demo.com", "Admin@123", "/pages/admin.html"),
        ("👨‍⚕️ Doctor (Lead)", "Dr. Amit Verma", "doctor@demo.com", "Doctor@123", "/pages/login.html"),
        ("👨‍⚕️ Doctor (ENT)", "Dr. Sneha Patel", "doctor2@demo.com", "Doctor@123", "/pages/login.html"),
        ("👨‍⚕️ Doctor (Pulmo)", "Dr. Rajesh Kumar", "doctor3@demo.com", "Doctor@123", "/pages/login.html"),
        ("👤 Patient (Demo)", "Rahul Sharma", "patient@demo.com", "Patient@123", "/pages/login.html"),
        ("👤 Patient 2", "Priya Gupta", "patient2@demo.com", "Patient@123", "/pages/login.html")
    ]

    row_y = y + 55
    for role, name, email, pwd, url in accounts:
        draw.text((60, row_y), role, fill='#0f172a', font=font_bold)
        draw.text((220, row_y), name, fill='#1e293b', font=font_regular)
        draw.text((460, row_y), email, fill='#0957d0', font=font_code)
        draw.text((750, row_y), pwd, fill='#b91c1c', font=font_code)
        draw.text((950, row_y), url, fill='#475569', font=font_regular)
        row_y += 32

    y += 290

    # Section 2: Complete Specialist Doctors
    draw.text((40, y), "2. COMPLETE VERIFIED SPECIALIST DOCTORS (All use Password: Doctor@123)", fill='#0f766e', font=font_h2)
    y += 35

    draw.rounded_rectangle([(40, y), (width - 40, y + 360)], radius=12, fill='#ffffff', outline='#cbd5e1', width=1)
    draw.text((60, y + 12), "DOCTOR & DEGREE", fill='#64748b', font=font_bold)
    draw.text((360, y + 12), "SPECIALIZATION", fill='#64748b', font=font_bold)
    draw.text((600, y + 12), "EMAIL ADDRESS", fill='#64748b', font=font_bold)
    draw.text((880, y + 12), "FEE & LOCATION", fill='#64748b', font=font_bold)
    draw.line([(60, y + 38), (width - 60, y + 38)], fill='#e2e8f0', width=1)

    all_doctors = [
        ("Dr. Amit Verma (MBBS, MD)", "General Physician", "doctor@demo.com", "₹500 / Dehradun"),
        ("Dr. Sneha Patel (MBBS, MS)", "ENT Specialist", "doctor2@demo.com", "₹600 / Dehradun"),
        ("Dr. Rajesh Kumar (MBBS, MD)", "Pulmonologist", "doctor3@demo.com", "₹700 / Dehradun"),
        ("Dr. Meera Singh (MBBS, DNB)", "Pediatrician", "doctor4@demo.com", "₹550 / Dehradun"),
        ("Dr. Arun Joshi (MBBS, MD)", "Dermatologist", "doctor5@demo.com", "₹650 / Dehradun"),
        ("Dr. Kavita Rawat (MBBS, DM)", "Cardiologist", "doctor6@demo.com", "₹800 / Dehradun"),
        ("Dr. Suresh Negi (MBBS)", "General Physician", "doctor7@demo.com", "₹450 / Dehradun"),
        ("Dr. Anita Bhatt (MBBS, DM)", "Neurologist", "doctor8@demo.com", "₹850 / Dehradun"),
        ("Dr. Vikram Chauhan (MBBS, MS)", "Orthopedic", "doctor9@demo.com", "₹600 / Dehradun"),
        ("Dr. Pooja Sharma (MBBS, MD)", "Gastroenterologist", "doctor10@demo.com", "₹750 / Dehradun"),
        ("Dr. Ravi Thapa (MBBS)", "General Physician", "doctor11@demo.com", "₹400 / Dehradun"),
        ("Dr. Deepa Kandari (MBBS, MS)", "Gynecologist", "doctor12@demo.com", "₹650 / Dehradun"),
    ]

    doc_y = y + 48
    for doc_name, spec, doc_email, fee in all_doctors:
        draw.text((60, doc_y), doc_name, fill='#0f172a', font=font_bold)
        draw.text((360, doc_y), spec, fill='#0d9488', font=font_regular)
        draw.text((600, doc_y), doc_email, fill='#0957d0', font=font_code)
        draw.text((880, doc_y), fee, fill='#475569', font=font_regular)
        doc_y += 25

    y += 390

    # Section 3: Supabase Cloud Database Key
    draw.text((40, y), "3. SUPABASE CLOUD DATABASE CONNECTION KEY", fill='#0f766e', font=font_h2)
    y += 35

    draw.rounded_rectangle([(40, y), (width - 40, y + 150)], radius=12, fill='#f1f5f9', outline='#cbd5e1', width=1)
    draw.text((60, y + 18), "Database Host:", fill='#475569', font=font_bold)
    draw.text((220, y + 18), "aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres", fill='#0f172a', font=font_code)

    draw.text((60, y + 50), "Database User:", fill='#475569', font=font_bold)
    draw.text((220, y + 50), "postgres.fpoyfurmqvmqxzpqwszu", fill='#0f172a', font=font_code)

    draw.text((60, y + 82), "Database Password:", fill='#475569', font=font_bold)
    draw.text((220, y + 82), "HealthProject@2026", fill='#b91c1c', font=font_code)

    draw.text((60, y + 114), "Security Notice:", fill='#475569', font=font_bold)
    draw.text((220, y + 114), "Credentials have been removed from website pages. Keep this sheet secure.", fill='#059669', font=font_regular)

    image.save(img_path, format='PNG')
    print(f"[OK] Generated PNG: {img_path}")
    return img_path

if __name__ == '__main__':
    generate_pdf()
    generate_image()
