"""
Generate Test Claim PDFs with Fraud Indicators
Creates sample claim documents that trigger various fraud detection flags
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor, black, grey


def setup_styles():
    """Setup custom paragraph styles"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ClaimHeader',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HexColor('#1a73e8'),
        spaceAfter=12,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=black,
        spaceBefore=12,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name='ClaimBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8
    ))

    return styles


def create_claim_pdf(filename, claim_data, output_dir):
    """Create a claim PDF with given data"""
    output_path = output_dir / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = setup_styles()
    story = []

    # Header
    story.append(Paragraph("INSURANCE CLAIM FORM", styles['ClaimHeader']))
    story.append(Spacer(1, 0.2 * inch))

    # Claim Info Table
    claim_info_data = [
        ['Claim Number:', claim_data['claim_number']],
        ['Policy Number:', claim_data['policy_number']],
        ['Claim Amount:', f"${claim_data['claim_amount']:,.2f}"],
        ['Incident Type:', claim_data['incident_type'].title()],
        ['Incident Date:', claim_data['incident_date']],
        ['Report Date:', claim_data['report_date']],
    ]

    claim_table = Table(claim_info_data, colWidths=[2*inch, 4*inch])
    claim_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(claim_table)
    story.append(Spacer(1, 0.3 * inch))

    # Insured Information
    story.append(Paragraph("INSURED INFORMATION", styles['SectionHeader']))
    insured_data = [
        ['Name:', claim_data['insured_name']],
        ['Address:', claim_data['insured_address']],
        ['Phone:', claim_data['insured_phone']],
    ]

    insured_table = Table(insured_data, colWidths=[1.5*inch, 4.5*inch])
    insured_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(insured_table)
    story.append(Spacer(1, 0.2 * inch))

    # Incident Description
    story.append(Paragraph("INCIDENT DESCRIPTION", styles['SectionHeader']))
    story.append(Paragraph(claim_data['description'], styles['ClaimBody']))
    story.append(Spacer(1, 0.2 * inch))

    # Injuries (if any)
    if claim_data.get('injuries'):
        story.append(Paragraph("INJURIES REPORTED", styles['SectionHeader']))
        for injury in claim_data['injuries']:
            injury_text = f"<b>{injury['person']}:</b> {injury['severity'].title()} - {injury['description']}"
            story.append(Paragraph(injury_text, styles['ClaimBody']))
        story.append(Spacer(1, 0.2 * inch))

    # Additional Information
    if claim_data.get('additional_info'):
        story.append(Paragraph("ADDITIONAL INFORMATION", styles['SectionHeader']))
        story.append(Paragraph(claim_data['additional_info'], styles['ClaimBody']))

    # Build PDF
    doc.build(story)
    print(f"✅ Generated: {filename}")
    return output_path


def generate_late_reporting_claim():
    """Test Case 1: Late Reporting (45 days late)"""
    incident_date = datetime.now() - timedelta(days=45)
    report_date = datetime.now()

    return {
        'claim_number': 'CLM-LATE-001',
        'policy_number': 'AUTO-999888-CA',
        'claim_amount': 8500.00,
        'incident_type': 'auto',
        'incident_date': incident_date.strftime('%Y-%m-%d'),
        'report_date': report_date.strftime('%Y-%m-%d'),
        'insured_name': 'Michael Johnson',
        'insured_address': '456 Oak Street, Los Angeles, CA 90001',
        'insured_phone': '(310) 555-2468',
        'description': '''
On the date of the incident, I was driving my 2018 Honda Accord westbound on Main Street
when another vehicle ran a red light and struck my vehicle on the driver's side. The other
driver was clearly at fault. My vehicle sustained significant damage to the door and frame.
I was unable to report this earlier due to traveling out of the country for business.
        '''.strip(),
        'injuries': [
            {'person': 'Michael Johnson', 'severity': 'moderate', 'description': 'Lower back pain and neck strain'}
        ],
        'additional_info': 'I have photos of the damage and the other driver admitted fault at the scene.'
    }


def generate_inconsistent_story_claim():
    """Test Case 2: Inconsistent Story (contradicting statements)"""
    incident_date = datetime.now() - timedelta(days=5)
    report_date = datetime.now() - timedelta(days=3)

    return {
        'claim_number': 'CLM-INCON-002',
        'policy_number': 'AUTO-777666-TX',
        'claim_amount': 12500.00,
        'incident_type': 'auto',
        'incident_date': incident_date.strftime('%Y-%m-%d'),
        'report_date': report_date.strftime('%Y-%m-%d'),
        'insured_name': 'Sarah Martinez',
        'insured_address': '789 Pine Avenue, Houston, TX 77001',
        'insured_phone': '(713) 555-8901',
        'description': '''
I was stopped at a traffic light when suddenly my vehicle was impacted from behind by
another vehicle. The other driver was clearly moving too fast for the conditions. I had
clear visibility of the entire intersection. There were no injuries at the scene.
        '''.strip(),
        'injuries': [
            {'person': 'Sarah Martinez', 'severity': 'moderate', 'description': 'Whiplash and neck injury requiring medical attention'}
        ],
        'additional_info': '''
After further reflection, I remember the weather was poor and I couldn\'t see very well.
The impact happened while I was still moving slowly. I later discovered I had sustained
injuries that weren\'t immediately apparent.
        '''
    }


def generate_suspicious_patterns_claim():
    """Test Case 3: Suspicious Patterns (pre-existing, witness unavailable)"""
    incident_date = datetime.now() - timedelta(days=12)
    report_date = datetime.now() - timedelta(days=10)

    return {
        'claim_number': 'CLM-SUSP-003',
        'policy_number': 'AUTO-555444-FL',
        'claim_amount': 15000.00,
        'incident_type': 'auto',
        'incident_date': incident_date.strftime('%Y-%m-%d'),
        'report_date': report_date.strftime('%Y-%m-%d'),
        'insured_name': 'Robert Chen',
        'insured_address': '321 Beach Road, Miami, FL 33101',
        'insured_phone': '(305) 555-4567',
        'description': '''
While driving on I-95, another vehicle merged into my lane without signaling and struck
the passenger side of my vehicle. The damage was extensive. A witness saw the entire
incident but left before I could get their contact information. The witness is unavailable
to provide a statement.
        '''.strip(),
        'injuries': [
            {'person': 'Robert Chen', 'severity': 'serious', 'description': 'Multiple injuries including back strain'},
            {'person': 'Passenger Jane Chen', 'severity': 'moderate', 'description': 'Shoulder and neck whiplash'}
        ],
        'additional_info': '''
I should mention that I had a previous accident in a similar location about 6 months ago.
Some of my current injuries may be related to pre-existing conditions from that incident.
This is actually a similar claim to one I filed last year with a different insurance company.
        '''
    }


def generate_soft_tissue_only_claim():
    """Test Case 4: Soft Tissue Only Injuries"""
    incident_date = datetime.now() - timedelta(days=8)
    report_date = datetime.now() - timedelta(days=7)

    return {
        'claim_number': 'CLM-SOFT-004',
        'policy_number': 'AUTO-333222-NY',
        'claim_amount': 9500.00,
        'incident_type': 'auto',
        'incident_date': incident_date.strftime('%Y-%m-%d'),
        'report_date': report_date.strftime('%Y-%m-%d'),
        'insured_name': 'Jennifer Williams',
        'insured_address': '654 Broadway, New York, NY 10001',
        'insured_phone': '(212) 555-7890',
        'description': '''
I was rear-ended while waiting at a stoplight. The impact was moderate but caused
significant discomfort. All occupants of my vehicle complained of pain following the collision.
        '''.strip(),
        'injuries': [
            {'person': 'Jennifer Williams', 'severity': 'moderate', 'description': 'Severe whiplash and neck strain'},
            {'person': 'Passenger Tom Williams', 'severity': 'moderate', 'description': 'Lower back sprain and soft tissue damage'},
            {'person': 'Passenger Lisa Williams', 'severity': 'minor', 'description': 'Neck strain and shoulder soft tissue injury'},
            {'person': 'Passenger Bobby Williams', 'severity': 'minor', 'description': 'Upper back sprain'},
        ],
        'additional_info': 'All passengers are seeking medical treatment for soft tissue injuries. No visible injuries were present at the scene.'
    }


def generate_excessive_injuries_claim():
    """Test Case 5: Excessive Injuries (>5 injuries)"""
    incident_date = datetime.now() - timedelta(days=10)
    report_date = datetime.now() - timedelta(days=8)

    return {
        'claim_number': 'CLM-EXCESS-005',
        'policy_number': 'AUTO-111000-IL',
        'claim_amount': 25000.00,
        'incident_type': 'auto',
        'incident_date': incident_date.strftime('%Y-%m-%d'),
        'report_date': report_date.strftime('%Y-%m-%d'),
        'insured_name': 'David Thompson',
        'insured_address': '987 Lake Shore Drive, Chicago, IL 60601',
        'insured_phone': '(312) 555-3456',
        'description': '''
Multi-vehicle accident on the highway during rush hour. My vehicle was struck multiple
times by different vehicles. The collision was severe and affected all occupants of my vehicle.
        '''.strip(),
        'injuries': [
            {'person': 'David Thompson', 'severity': 'serious', 'description': 'Neck whiplash, back strain, shoulder injury'},
            {'person': 'Passenger Mary Thompson', 'severity': 'serious', 'description': 'Head contusion, whiplash, wrist sprain'},
            {'person': 'Passenger Tim Thompson', 'severity': 'moderate', 'description': 'Multiple soft tissue injuries, ankle sprain'},
            {'person': 'Passenger Amy Thompson', 'severity': 'moderate', 'description': 'Neck strain, knee injury, bruising'},
            {'person': 'Passenger Kevin Thompson', 'severity': 'moderate', 'description': 'Shoulder strain, elbow injury'},
            {'person': 'Passenger Susan Thompson', 'severity': 'minor', 'description': 'Minor cuts, soft tissue damage'},
        ],
        'additional_info': '''
All six occupants of the vehicle are seeking extensive medical treatment. The witness to
the accident is unavailable. Some injuries may be related to pre-existing conditions.
        '''
    }


def generate_combined_fraud_claim():
    """Test Case 6: Combined Fraud Indicators (multiple red flags)"""
    incident_date = datetime.now() - timedelta(days=35)
    report_date = datetime.now() - timedelta(days=2)

    return {
        'claim_number': 'CLM-COMBO-006',
        'policy_number': 'AUTO-888999-GA',
        'claim_amount': 18500.00,
        'incident_type': 'auto',
        'incident_date': incident_date.strftime('%Y-%m-%d'),
        'report_date': report_date.strftime('%Y-%m-%d'),
        'insured_name': 'Patricia Rodriguez',
        'insured_address': '159 Peachtree Street, Atlanta, GA 30301',
        'insured_phone': '(404) 555-6789',
        'description': '''
I was stopped at a red light when another vehicle struck my car from behind. The impact
was significant. I could see clearly that the other driver was at fault. There were no
immediate injuries at the scene. The witness who saw everything is unavailable to provide
a statement.
        '''.strip(),
        'injuries': [
            {'person': 'Patricia Rodriguez', 'severity': 'serious', 'description': 'Severe whiplash and soft tissue damage to neck and shoulders'},
            {'person': 'Passenger Carlos Rodriguez', 'severity': 'serious', 'description': 'Multiple soft tissue injuries including back sprain'},
            {'person': 'Passenger Maria Rodriguez', 'severity': 'moderate', 'description': 'Whiplash and neck strain'},
            {'person': 'Passenger Anna Rodriguez', 'severity': 'moderate', 'description': 'Shoulder and back soft tissue injuries'},
            {'person': 'Passenger Luis Rodriguez', 'severity': 'moderate', 'description': 'Neck strain and lower back sprain'},
            {'person': 'Passenger Sofia Rodriguez', 'severity': 'minor', 'description': 'Minor soft tissue damage'},
        ],
        'additional_info': '''
I apologize for the delay in reporting - I was dealing with personal issues and couldn\'t
file immediately. After the accident, I realized I couldn\'t see very well due to poor
lighting conditions, and I was actually still moving when hit. Several of the injuries may
be related to pre-existing conditions from a previous accident. This is similar to a claim
I filed 8 months ago. Multiple injuries across all passengers require medical attention.
The witness is unavailable.
        '''
    }


def main():
    """Generate all fraud test PDFs"""
    # Create output directory
    backend_dir = Path(__file__).parent.parent
    output_dir = backend_dir / 'test_data' / 'fraud_samples'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🔧 Generating fraud test claim PDFs...")
    print(f"📁 Output directory: {output_dir}")
    print()

    # Generate test cases
    test_cases = [
        ('fraud_test_1_late_reporting.pdf', generate_late_reporting_claim()),
        ('fraud_test_2_inconsistent_story.pdf', generate_inconsistent_story_claim()),
        ('fraud_test_3_suspicious_patterns.pdf', generate_suspicious_patterns_claim()),
        ('fraud_test_4_soft_tissue_only.pdf', generate_soft_tissue_only_claim()),
        ('fraud_test_5_excessive_injuries.pdf', generate_excessive_injuries_claim()),
        ('fraud_test_6_combined_fraud.pdf', generate_combined_fraud_claim()),
    ]

    generated_files = []
    for filename, claim_data in test_cases:
        path = create_claim_pdf(filename, claim_data, output_dir)
        generated_files.append(path)

    print()
    print("✅ All fraud test PDFs generated successfully!")
    print()
    print("📋 Test Cases Generated:")
    print("  1. Late Reporting (45 days) - Should trigger 'late_reporting' flag")
    print("  2. Inconsistent Story - Should trigger 'inconsistent_story' flag")
    print("  3. Suspicious Patterns - Should trigger 'suspicious_pattern' flags")
    print("  4. Soft Tissue Only - Should trigger 'soft_tissue_only' flag")
    print("  5. Excessive Injuries - Should trigger 'excessive_injuries' flag")
    print("  6. Combined Fraud - Should trigger MULTIPLE fraud flags")
    print()
    print("🚀 To test fraud detection:")
    print(f"   1. Copy PDFs from: {output_dir}")
    print(f"   2. To uploads folder: {backend_dir / 'uploads'}")
    print("   3. Watch the dashboard for fraud alerts!")
    print()
    print("💡 Or run: cp test_data/fraud_samples/*.pdf uploads/")


if __name__ == '__main__':
    main()
