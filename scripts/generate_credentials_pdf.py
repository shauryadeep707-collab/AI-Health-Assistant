import os
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf():
    pdf_path = r'c:\Users\shaur\OneDrive\Desktop\bestproject\AI-Health-Assistant\demo_patient_credentials.pdf'
    desktop_pdf_path = r'c:\Users\shaur\OneDrive\Desktop\bestproject\demo_patient_credentials.pdf'
    artifact_pdf_path = r'C:\Users\shaur\.gemini\antigravity\brain\d99d3cdf-ea47-4066-84ee-3fb1dd935670\demo_patient_credentials.pdf'

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1e3a8a')
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#4b5563')
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=8
    )

    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1f2937')
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#111827')
    )

    badge_patient = ParagraphStyle(
        'BadgePatient',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#065f46')
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1d4ed8')
    )

    code_pass = ParagraphStyle(
        'CodePass',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#b91c1c')
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph('AI Health Assistant — Demo Credentials', title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph('Official Testing &amp; Evaluation Access Document &bull; Confidential Demo Persona Passwords', subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=12))

    # Section 1: Patient Credentials
    story.append(Paragraph('1. Demo Patient Accounts (Login ID &amp; Password)', section_heading))
    story.append(Paragraph('Use these credentials to log in as a patient and test the AI symptom checker, dialogue summary, and doctor routing.', subtitle_style))
    story.append(Spacer(1, 8))

    patient_headers = [
        Paragraph('<b>Persona</b>', cell_bold),
        Paragraph('<b>Patient Name</b>', cell_bold),
        Paragraph('<b>Login ID (Email)</b>', cell_bold),
        Paragraph('<b>Password</b>', cell_bold),
        Paragraph('<b>Profile Context</b>', cell_bold)
    ]

    patient_row1 = [
        Paragraph('<b>Primary Demo Patient</b><br/><font color="#047857">Standard Testing</font>', badge_patient),
        Paragraph('Rahul Sharma', cell_style),
        Paragraph('patient@demo.com', code_style),
        Paragraph('Patient@123', code_pass),
        Paragraph('Age: 28 &bull; Male<br/>History: None<br/>Phone: +91 98765 43210', cell_style)
    ]

    patient_row2 = [
        Paragraph('<b>Secondary Demo Patient</b><br/><font color="#047857">Chronic History</font>', badge_patient),
        Paragraph('Priya Gupta', cell_style),
        Paragraph('patient2@demo.com', code_style),
        Paragraph('Patient@123', code_pass),
        Paragraph('Age: 35 &bull; Female<br/>History: Asthma<br/>Allergies: Penicillin<br/>Phone: +91 98765 43211', cell_style)
    ]

    patient_table_data = [patient_headers, patient_row1, patient_row2]

    col_widths = [115, 85, 125, 95, 120]
    patient_table = Table(patient_table_data, colWidths=col_widths)
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 14))

    # Section 2: Other Demo Accounts (Doctor & Admin)
    story.append(Paragraph('2. Doctor &amp; Admin Demo Accounts (For Verification &amp; Review)', section_heading))
    story.append(Paragraph('Log in as Doctor to review incoming consultations and auto-routed patient summaries. Log in as Admin to manage users and doctor approvals.', subtitle_style))
    story.append(Spacer(1, 8))

    other_headers = [
        Paragraph('<b>Role</b>', cell_bold),
        Paragraph('<b>Account Name</b>', cell_bold),
        Paragraph('<b>Login ID (Email)</b>', cell_bold),
        Paragraph('<b>Password</b>', cell_bold),
        Paragraph('<b>Capabilities</b>', cell_bold)
    ]

    doctor_row = [
        Paragraph('<b>Verified Doctor</b>', cell_bold),
        Paragraph('Dr. Rajesh Sharma, MD', cell_style),
        Paragraph('doctor@demo.com', code_style),
        Paragraph('Doctor@123', code_pass),
        Paragraph('Review FIFO consultation queue, view dialogue summary, provide medical advice &amp; prescription.', cell_style)
    ]

    admin_row = [
        Paragraph('<b>System Admin</b>', cell_bold),
        Paragraph('Admin User', cell_style),
        Paragraph('admin@demo.com', code_style),
        Paragraph('Admin@123', code_pass),
        Paragraph('Doctor verification with audit trail, user management, license inspection.', cell_style)
    ]

    other_table = Table([other_headers, doctor_row, admin_row], colWidths=col_widths)
    other_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(other_table)
    story.append(Spacer(1, 14))

    # Section 3: Login Instructions
    story.append(Paragraph('3. Quick Login Instructions', section_heading))
    instructions_text = (
        '<b>Step 1:</b> Open <b>http://localhost:5000/pages/login.html</b> in your web browser.<br/>'
        '<b>Step 2:</b> Enter the Patient <b>Email / ID</b> (e.g. <code>patient@demo.com</code>).<br/>'
        '<b>Step 3:</b> Enter the <b>Password</b> (<code>Patient@123</code>).<br/>'
        '<b>Step 4:</b> Click <b>Sign In</b> to enter the patient portal, start a symptom assessment, or check past summaries.<br/>'
        '<i>Note: To keep public landing pages clean and professional, demo credentials are provided in this reference document.</i>'
    )
    instructions_box = Table(
        [[Paragraph(instructions_text, cell_style)]],
        colWidths=[540]
    )
    instructions_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(instructions_box)

    doc.build(story)

    # Copy to project root and artifact directory
    shutil.copyfile(pdf_path, desktop_pdf_path)
    os.makedirs(os.path.dirname(artifact_pdf_path), exist_ok=True)
    shutil.copyfile(pdf_path, artifact_pdf_path)

    print('PDF successfully generated at:')
    print(f'  {pdf_path}')
    print(f'  {desktop_pdf_path}')
    print(f'  {artifact_pdf_path}')

if __name__ == '__main__':
    generate_pdf()
