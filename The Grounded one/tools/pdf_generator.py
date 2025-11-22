"""
PDF Generator Tool
Generates PDF reports for patient records using Pillow and ReportLab
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
import config
import utils

# PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  ReportLab not installed. Install with: pip install reportlab")

# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_patient_report_pdf(
    patient_id: str,
    clinician_id: str,
    output_filename: Optional[str] = None,
    include_sections: Optional[List[str]] = None
) -> Dict:
    """
    Generate PDF report for patient
    
    Args:
        patient_id: Patient ID
        clinician_id: Clinician requesting report
        output_filename: Custom filename (None = auto-generate)
        include_sections: List of sections to include (None = all)
        
    Returns:
        Dictionary with generation result and file path
    """
    try:
        if not REPORTLAB_AVAILABLE:
            return {
                "success": False,
                "error": "ReportLab library not installed. Run: pip install reportlab"
            }
        
        # Validate IDs
        if not utils.validate_patient_id(patient_id):
            return {
                "success": False,
                "error": "Invalid patient ID format"
            }
        
        if not utils.validate_clinician_id(clinician_id):
            return {
                "success": False,
                "error": "Invalid clinician ID format"
            }
        
        # Fetch patient data
        patient = utils.get_patient_by_id(patient_id)
        if not patient:
            return {
                "success": False,
                "error": f"Patient {patient_id} not found"
            }
        
        # Fetch clinician data
        clinician = utils.get_clinician_by_id(clinician_id)
        clinician_name = clinician.get("full_name") if clinician else "Unknown"
        
        # Generate filename
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"patient_report_{patient_id}_{timestamp}.pdf"
        
        output_path = config.DATA_DIR / output_filename
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Default sections if not specified
        if not include_sections:
            include_sections = ["header", "demographics", "vitals", "medical_history", "notes"]
        
        # === HEADER ===
        if "header" in include_sections:
            elements.append(Paragraph("PATIENT MEDICAL REPORT", title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            header_data = [
                ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["Requested By:", clinician_name],
                ["Clinician ID:", clinician_id]
            ]
            header_table = Table(header_data, colWidths=[2*inch, 4*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # === DEMOGRAPHICS ===
        if "demographics" in include_sections:
            elements.append(Paragraph("Patient Demographics", heading_style))
            
            demo_data = [
                ["Patient ID:", patient.get("patient_id")],
                ["Name:", patient.get("full_name")],
                ["Date of Birth:", patient.get("date_of_birth")],
                ["Gender:", patient.get("gender")],
                ["Blood Type:", patient.get("blood_type")],
                ["Phone:", patient.get("phone")],
                ["Email:", patient.get("email")]
            ]
            
            address = patient.get("address", {})
            if address:
                demo_data.append([
                    "Address:",
                    f"{address.get('street')}, {address.get('city')}, {address.get('state')} {address.get('zip')}"
                ])
            
            demo_table = Table(demo_data, colWidths=[2*inch, 4*inch])
            demo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0'))
            ]))
            elements.append(demo_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # === VITALS ===
        if "vitals" in include_sections:
            vitals = patient.get("vitals", {})
            if vitals:
                elements.append(Paragraph("Current Vital Signs", heading_style))
                
                vitals_data = [
                    ["Blood Pressure:", vitals.get("blood_pressure", "N/A")],
                    ["Heart Rate:", f"{vitals.get('heart_rate', 'N/A')} bpm"],
                    ["Temperature:", f"{vitals.get('temperature', 'N/A')}°F"],
                    ["Weight:", f"{vitals.get('weight_kg', 'N/A')} kg"],
                    ["Height:", f"{vitals.get('height_cm', 'N/A')} cm"]
                ]
                
                vitals_table = Table(vitals_data, colWidths=[2*inch, 4*inch])
                vitals_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0'))
                ]))
                elements.append(vitals_table)
                elements.append(Spacer(1, 0.3*inch))
        
        # === MEDICAL HISTORY ===
        if "medical_history" in include_sections:
            medical = patient.get("medical_history", {})
            
            elements.append(Paragraph("Medical History", heading_style))
            
            conditions = medical.get("conditions", [])
            medications = medical.get("medications", [])
            allergies = medical.get("allergies", [])
            
            history_data = [
                ["Conditions:", ", ".join(conditions) if conditions else "None reported"],
                ["Medications:", ", ".join(medications) if medications else "None"],
                ["Allergies:", ", ".join(allergies) if allergies else "None"]
            ]
            
            history_table = Table(history_data, colWidths=[2*inch, 4*inch])
            history_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0'))
            ]))
            elements.append(history_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # === CLINICAL NOTES ===
        if "notes" in include_sections:
            notes = patient.get("notes", [])
            if notes:
                elements.append(Paragraph("Recent Clinical Notes", heading_style))
                
                # Show last 5 notes
                recent_notes = notes[-5:] if len(notes) > 5 else notes
                
                for note in reversed(recent_notes):
                    note_text = f"""
                    <b>Date:</b> {note.get('date', 'Unknown')}<br/>
                    <b>Clinician:</b> {note.get('clinician_name', note.get('clinician', 'Unknown'))}<br/>
                    <b>Type:</b> {note.get('note_type', 'general').title()}<br/>
                    <b>Note:</b> {note.get('note', '')}
                    """
                    elements.append(Paragraph(note_text, styles['Normal']))
                    elements.append(Spacer(1, 0.2*inch))
        
        # === FOOTER ===
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "CONFIDENTIAL MEDICAL RECORD - HIPAA Protected Information",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patient.get("full_name"),
            "clinician_id": clinician_id,
            "clinician_name": clinician_name,
            "file_path": str(output_path),
            "filename": output_filename,
            "file_size_bytes": output_path.stat().st_size,
            "message": f"PDF report generated: {output_filename}"
        }
    
    except Exception as e:
        return utils.handle_error(e, "generate_patient_report_pdf")

# ============================================================================
# ADK TOOL WRAPPER
# ============================================================================

def pdf_generator_tool(
    patient_id: str,
    clinician_id: str,
    output_filename: Optional[str] = None
) -> Dict:
    """
    ADK-compatible tool wrapper for PDF generation
    
    Args:
        patient_id: Patient ID
        clinician_id: Clinician ID
        output_filename: Custom filename
        
    Returns:
        Generation result dictionary
    """
    return generate_patient_report_pdf(patient_id, clinician_id, output_filename)

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📑 PDF GENERATOR TOOL - TEST")
    print("="*60 + "\n")
    
    if not REPORTLAB_AVAILABLE:
        print("❌ ReportLab not installed!")
        print("   Install with: pip install reportlab")
        print("\n" + "="*60 + "\n")
        sys.exit(1)
    
    # Test 1: Generate full report
    print("Test 1: Generate complete patient report")
    print("-" * 60)
    result = pdf_generator_tool(
        patient_id="PT_0001",
        clinician_id="DR_0001"
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
        print(f"   Patient: {result.get('patient_name')}")
        print(f"   Generated by: {result.get('clinician_name')}")
        print(f"   File: {result.get('filename')}")
        print(f"   Size: {result.get('file_size_bytes')} bytes")
        print(f"   Path: {result.get('file_path')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 2: Generate with custom filename
    print("\n" + "-" * 60)
    print("\nTest 2: Generate with custom filename")
    print("-" * 60)
    result = pdf_generator_tool(
        patient_id="PT_0002",
        clinician_id="DR_0002",
        output_filename="custom_patient_report.pdf"
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 3: Invalid patient
    print("\n" + "-" * 60)
    print("\nTest 3: Attempt with invalid patient")
    print("-" * 60)
    result = pdf_generator_tool(
        patient_id="PT_9999",
        clinician_id="DR_0001"
    )
    
    if not result.get("success"):
        print(f"❌ {result.get('error')} (Expected)")
    
    print("\n" + "="*60)
    print("✅ PDF Generator Test Complete")
    print("="*60 + "\n")