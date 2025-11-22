"""
Record Appender Tool
Appends new entries to patient medical records
"""

import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
import config
import utils

# ============================================================================
# RECORD APPENDING
# ============================================================================

def append_to_patient_record(
    patient_id: str,
    clinician_id: str,
    note: str,
    note_type: str = "general"
) -> Dict:
    """
    Append a new note/entry to patient record
    
    Args:
        patient_id: Patient ID (format: PT_XXXX)
        clinician_id: Clinician ID making the entry
        note: Note content to append
        note_type: Type of note (general, diagnosis, treatment, prescription, etc.)
        
    Returns:
        Dictionary with append result
    """
    try:
        # Validate IDs
        if not utils.validate_patient_id(patient_id):
            return {
                "success": False,
                "error": "Invalid patient ID format. Expected format: PT_XXXX",
                "patient_id": patient_id
            }
        
        if not utils.validate_clinician_id(clinician_id):
            return {
                "success": False,
                "error": "Invalid clinician ID format. Expected format: DR_XXXX",
                "clinician_id": clinician_id
            }
        
        # Validate note content
        if not note or len(note.strip()) == 0:
            return {
                "success": False,
                "error": "Note content cannot be empty",
                "patient_id": patient_id
            }
        
        # Load patients database
        patients = utils.load_json_file(config.PATIENTS_DB)
        
        if not isinstance(patients, list):
            return {
                "success": False,
                "error": "Patient database is corrupted or empty"
            }
        
        # Find the patient
        patient_index = None
        for i, patient in enumerate(patients):
            if patient.get("patient_id") == patient_id:
                patient_index = i
                break
        
        if patient_index is None:
            return {
                "success": False,
                "error": f"Patient {patient_id} not found in database",
                "patient_id": patient_id
            }
        
        # Get clinician info for the note
        clinician = utils.get_clinician_by_id(clinician_id)
        clinician_name = clinician.get("full_name") if clinician else "Unknown"
        
        # Create new note entry
        new_note = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "clinician": clinician_id,
            "clinician_name": clinician_name,
            "note_type": note_type,
            "note": note.strip()
        }
        
        # Append to patient's notes
        if "notes" not in patients[patient_index]:
            patients[patient_index]["notes"] = []
        
        patients[patient_index]["notes"].append(new_note)
        
        # Update last_visit date
        patients[patient_index]["last_visit"] = datetime.now().strftime("%Y-%m-%d")
        
        # Save back to file
        save_success = utils.save_json_file(config.PATIENTS_DB, patients)
        
        if not save_success:
            return {
                "success": False,
                "error": "Failed to save updated record to database"
            }
        
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patients[patient_index].get("full_name"),
            "clinician_id": clinician_id,
            "clinician_name": clinician_name,
            "note_type": note_type,
            "note_date": new_note["date"],
            "message": f"Note added to {patients[patient_index].get('full_name')}'s record by {clinician_name}"
        }
    
    except Exception as e:
        return utils.handle_error(e, "append_to_patient_record")

# ============================================================================
# SPECIALIZED APPEND FUNCTIONS
# ============================================================================

def append_diagnosis(
    patient_id: str,
    clinician_id: str,
    diagnosis: str,
    icd_code: Optional[str] = None
) -> Dict:
    """
    Append a diagnosis to patient record
    
    Args:
        patient_id: Patient ID
        clinician_id: Clinician ID
        diagnosis: Diagnosis description
        icd_code: ICD diagnostic code (optional)
        
    Returns:
        Append result dictionary
    """
    note = f"DIAGNOSIS: {diagnosis}"
    if icd_code:
        note += f" (ICD: {icd_code})"
    
    return append_to_patient_record(patient_id, clinician_id, note, "diagnosis")

def append_prescription(
    patient_id: str,
    clinician_id: str,
    medication: str,
    dosage: str,
    instructions: str
) -> Dict:
    """
    Append a prescription to patient record
    
    Args:
        patient_id: Patient ID
        clinician_id: Clinician ID
        medication: Medication name
        dosage: Dosage information
        instructions: Usage instructions
        
    Returns:
        Append result dictionary
    """
    note = f"PRESCRIPTION: {medication} - {dosage}. Instructions: {instructions}"
    return append_to_patient_record(patient_id, clinician_id, note, "prescription")

def append_lab_results(
    patient_id: str,
    clinician_id: str,
    test_name: str,
    results: str
) -> Dict:
    """
    Append lab results to patient record
    
    Args:
        patient_id: Patient ID
        clinician_id: Clinician ID
        test_name: Name of the test
        results: Test results
        
    Returns:
        Append result dictionary
    """
    note = f"LAB RESULTS: {test_name} - {results}"
    return append_to_patient_record(patient_id, clinician_id, note, "lab_results")

# ============================================================================
# ADK TOOL WRAPPER
# ============================================================================

def record_appender_tool(
    patient_id: str,
    clinician_id: str,
    note: str,
    note_type: str = "general"
) -> Dict:
    """
    ADK-compatible tool wrapper for appending to records
    
    Args:
        patient_id: Patient ID
        clinician_id: Clinician ID
        note: Note to append
        note_type: Type of note
        
    Returns:
        Append result dictionary
    """
    result = append_to_patient_record(patient_id, clinician_id, note, note_type)
    
    # NOTE: Audit logging is handled separately by audit_logger tool
    # This follows HIPAA requirement that ALL modifications must be logged
    
    return result

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("➕ RECORD APPENDER TOOL - TEST")
    print("="*60 + "\n")
    
    # Test 1: Append general note
    print("Test 1: Append general note")
    print("-" * 60)
    result = record_appender_tool(
        patient_id="PT_0001",
        clinician_id="DR_0001",
        note="Patient reports improved mobility after physical therapy. Continue current treatment plan.",
        note_type="general"
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
        print(f"   Note Type: {result.get('note_type')}")
        print(f"   Date: {result.get('note_date')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 2: Append diagnosis
    print("\n" + "-" * 60)
    print("\nTest 2: Append diagnosis")
    print("-" * 60)
    result = append_diagnosis(
        patient_id="PT_0001",
        clinician_id="DR_0001",
        diagnosis="Type 2 Diabetes Mellitus",
        icd_code="E11.9"
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 3: Append prescription
    print("\n" + "-" * 60)
    print("\nTest 3: Append prescription")
    print("-" * 60)
    result = append_prescription(
        patient_id="PT_0001",
        clinician_id="DR_0001",
        medication="Metformin",
        dosage="500mg twice daily",
        instructions="Take with meals. Monitor blood sugar levels daily."
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 4: Append lab results
    print("\n" + "-" * 60)
    print("\nTest 4: Append lab results")
    print("-" * 60)
    result = append_lab_results(
        patient_id="PT_0001",
        clinician_id="DR_0001",
        test_name="HbA1c",
        results="6.8% (within acceptable range for diabetic patient)"
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 5: Invalid patient ID
    print("\n" + "-" * 60)
    print("\nTest 5: Attempt with invalid patient ID")
    print("-" * 60)
    result = record_appender_tool(
        patient_id="INVALID_ID",
        clinician_id="DR_0001",
        note="This should fail"
    )
    
    if not result.get("success"):
        print(f"❌ {result.get('error')} (Expected)")
    
    # Test 6: Empty note
    print("\n" + "-" * 60)
    print("\nTest 6: Attempt with empty note")
    print("-" * 60)
    result = record_appender_tool(
        patient_id="PT_0001",
        clinician_id="DR_0001",
        note="   "
    )
    
    if not result.get("success"):
        print(f"❌ {result.get('error')} (Expected)")
    
    # Show updated record
    print("\n" + "-" * 60)
    print("\nVerifying updates - Fetching patient record:")
    print("-" * 60)
    patient = utils.get_patient_by_id("PT_0001")
    if patient:
        notes = patient.get("notes", [])
        print(f"✅ Patient now has {len(notes)} notes")
        print(f"\nMost recent notes:")
        for note in notes[-3:]:  # Show last 3 notes
            print(f"\n   • Date: {note.get('date')}")
            print(f"     Type: {note.get('note_type', 'general')}")
            print(f"     By: {note.get('clinician_name', 'Unknown')}")
            print(f"     Note: {note.get('note')[:80]}...")
    
    print("\n" + "="*60)
    print("✅ Record Appender Test Complete")
    print("="*60 + "\n")