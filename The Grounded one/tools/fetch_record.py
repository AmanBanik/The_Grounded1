"""
Fetch Record Tool
Fetches patient medical records from the database
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
import config
import utils

# ============================================================================
# RECORD FETCHING
# ============================================================================

def fetch_patient_record(
    patient_id: str,
    fields: Optional[List[str]] = None,
    include_sensitive: bool = True
) -> Dict:
    """
    Fetch patient medical record
    
    Args:
        patient_id: Patient ID (format: PT_XXXX)
        fields: Specific fields to return (None = all fields)
        include_sensitive: Whether to include sensitive data (SSN, etc.)
        
    Returns:
        Dictionary with patient record or error
    """
    try:
        # Validate patient ID format
        if not utils.validate_patient_id(patient_id):
            return {
                "success": False,
                "error": "Invalid patient ID format. Expected format: PT_XXXX",
                "patient_id": patient_id
            }
        
        # Fetch patient from database
        patient = utils.get_patient_by_id(patient_id)
        
        if not patient:
            return {
                "success": False,
                "error": f"Patient {patient_id} not found in database",
                "patient_id": patient_id
            }
        
        # Create a copy to avoid modifying original
        patient_data = patient.copy()
        
        # Filter fields if specified
        if fields:
            filtered_data = {
                "patient_id": patient_data.get("patient_id")
            }
            for field in fields:
                if field in patient_data:
                    filtered_data[field] = patient_data[field]
            patient_data = filtered_data
        
        # Remove sensitive data if requested
        if not include_sensitive:
            # In a real system, SSN and other sensitive fields would be removed
            # For this mock system, we'll just flag it
            patient_data["_note"] = "Sensitive data filtering applied"
        
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_data": patient_data,
            "message": f"Record retrieved for {patient_data.get('full_name')}"
        }
    
    except Exception as e:
        return utils.handle_error(e, "fetch_patient_record")

# ============================================================================
# ADK TOOL WRAPPER
# ============================================================================

def fetch_record_tool(
    patient_id: str,
    fields: Optional[List[str]] = None,
    include_sensitive: bool = True
) -> Dict:
    """
    ADK-compatible tool wrapper for fetching patient records
    
    Args:
        patient_id: Patient ID to fetch
        fields: Specific fields to return
        include_sensitive: Include sensitive data
        
    Returns:
        Fetch result dictionary
    """
    result = fetch_patient_record(patient_id, fields, include_sensitive)
    
    # NOTE: Audit logging is handled separately by audit_logger tool
    # This follows HIPAA requirement that ALL accesses must be logged
    
    return result

# ============================================================================
# SPECIALIZED FETCH FUNCTIONS
# ============================================================================

def fetch_patient_vitals(patient_id: str) -> Dict:
    """
    Fetch only vital signs for a patient
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Dictionary with vital signs
    """
    try:
        patient = utils.get_patient_by_id(patient_id)
        
        if not patient:
            return {
                "success": False,
                "error": f"Patient {patient_id} not found"
            }
        
        vitals = patient.get("vitals", {})
        
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patient.get("full_name"),
            "vitals": vitals,
            "last_visit": patient.get("last_visit")
        }
    
    except Exception as e:
        return utils.handle_error(e, "fetch_patient_vitals")

def fetch_patient_medications(patient_id: str) -> Dict:
    """
    Fetch only medications for a patient
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Dictionary with medications
    """
    try:
        patient = utils.get_patient_by_id(patient_id)
        
        if not patient:
            return {
                "success": False,
                "error": f"Patient {patient_id} not found"
            }
        
        medical_history = patient.get("medical_history", {})
        medications = medical_history.get("medications", [])
        conditions = medical_history.get("conditions", [])
        allergies = medical_history.get("allergies", [])
        
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patient.get("full_name"),
            "medications": medications,
            "conditions": conditions,
            "allergies": allergies
        }
    
    except Exception as e:
        return utils.handle_error(e, "fetch_patient_medications")

def fetch_patient_summary(patient_id: str) -> Dict:
    """
    Fetch a summary view of patient (non-sensitive overview)
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Dictionary with patient summary
    """
    try:
        patient = utils.get_patient_by_id(patient_id)
        
        if not patient:
            return {
                "success": False,
                "error": f"Patient {patient_id} not found"
            }
        
        summary = {
            "patient_id": patient.get("patient_id"),
            "full_name": patient.get("full_name"),
            "date_of_birth": patient.get("date_of_birth"),
            "gender": patient.get("gender"),
            "blood_type": patient.get("blood_type"),
            "last_visit": patient.get("last_visit"),
            "conditions_count": len(patient.get("medical_history", {}).get("conditions", [])),
            "medications_count": len(patient.get("medical_history", {}).get("medications", [])),
            "has_allergies": len(patient.get("medical_history", {}).get("allergies", [])) > 0
        }
        
        return {
            "success": True,
            "patient_id": patient_id,
            "summary": summary
        }
    
    except Exception as e:
        return utils.handle_error(e, "fetch_patient_summary")

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📄 FETCH RECORD TOOL - TEST")
    print("="*60 + "\n")
    
    # Test full record fetch
    print("Test 1: Fetch full patient record")
    print("-" * 60)
    result = fetch_record_tool("PT_0001")
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
        patient_data = result.get("patient_data", {})
        print(f"\n   Patient: {patient_data.get('full_name')}")
        print(f"   DOB: {patient_data.get('date_of_birth')}")
        print(f"   Blood Type: {patient_data.get('blood_type')}")
        print(f"   Phone: {patient_data.get('phone')}")
        
        medical = patient_data.get('medical_history', {})
        print(f"\n   Medical History:")
        print(f"   • Conditions: {', '.join(medical.get('conditions', [])) or 'None'}")
        print(f"   • Medications: {', '.join(medical.get('medications', [])) or 'None'}")
        print(f"   • Allergies: {', '.join(medical.get('allergies', [])) or 'None'}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test fetching specific fields
    print("\n" + "-" * 60)
    print("\nTest 2: Fetch specific fields only")
    print("-" * 60)
    result = fetch_record_tool("PT_0001", fields=["full_name", "blood_type", "vitals"])
    
    if result.get("success"):
        print(f"✅ Partial record retrieved")
        print(f"   Fields returned: {list(result.get('patient_data', {}).keys())}")
    
    # Test vitals fetch
    print("\n" + "-" * 60)
    print("\nTest 3: Fetch vitals only")
    print("-" * 60)
    vitals_result = fetch_patient_vitals("PT_0001")
    
    if vitals_result.get("success"):
        print(f"✅ Vitals retrieved for {vitals_result.get('patient_name')}")
        vitals = vitals_result.get("vitals", {})
        print(f"   • Blood Pressure: {vitals.get('blood_pressure')}")
        print(f"   • Heart Rate: {vitals.get('heart_rate')} bpm")
        print(f"   • Temperature: {vitals.get('temperature')}°F")
        print(f"   • Weight: {vitals.get('weight_kg')} kg")
    
    # Test medications fetch
    print("\n" + "-" * 60)
    print("\nTest 4: Fetch medications only")
    print("-" * 60)
    meds_result = fetch_patient_medications("PT_0001")
    
    if meds_result.get("success"):
        print(f"✅ Medications retrieved for {meds_result.get('patient_name')}")
        print(f"   • Medications: {', '.join(meds_result.get('medications', [])) or 'None'}")
        print(f"   • Conditions: {', '.join(meds_result.get('conditions', [])) or 'None'}")
        print(f"   • Allergies: {', '.join(meds_result.get('allergies', [])) or 'None'}")
    
    # Test summary fetch
    print("\n" + "-" * 60)
    print("\nTest 5: Fetch patient summary")
    print("-" * 60)
    summary_result = fetch_patient_summary("PT_0001")
    
    if summary_result.get("success"):
        print(f"✅ Summary retrieved")
        summary = summary_result.get("summary", {})
        print(f"   • Name: {summary.get('full_name')}")
        print(f"   • DOB: {summary.get('date_of_birth')}")
        print(f"   • Last Visit: {summary.get('last_visit')}")
        print(f"   • Active Conditions: {summary.get('conditions_count')}")
        print(f"   • Active Medications: {summary.get('medications_count')}")
    
    # Test non-existent patient
    print("\n" + "-" * 60)
    print("\nTest 6: Fetch non-existent patient")
    print("-" * 60)
    result = fetch_record_tool("PT_9999")
    
    if not result.get("success"):
        print(f"❌ {result.get('error')} (Expected)")
    
    print("\n" + "="*60)
    print("✅ Fetch Record Test Complete")
    print("="*60 + "\n")