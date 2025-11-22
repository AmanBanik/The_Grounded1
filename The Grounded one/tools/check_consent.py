"""
Check Consent Tool
Checks patient consent status for clinician access
"""

import sys
from pathlib import Path
from typing import Dict
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
import config
import utils

# ============================================================================
# CONSENT CHECKING
# ============================================================================

def check_patient_consent_status(patient_id: str, clinician_id: str) -> Dict:
    """
    Check if patient has given consent for clinician access
    
    Args:
        patient_id: Patient ID (format: PT_XXXX)
        clinician_id: Clinician ID (format: DR_XXXX)
        
    Returns:
        Dictionary with consent status and details
    """
    try:
        # Validate ID formats
        if not utils.validate_patient_id(patient_id):
            return {
                "success": False,
                "consent_granted": False,
                "error": "Invalid patient ID format. Expected format: PT_XXXX",
                "patient_id": patient_id,
                "clinician_id": clinician_id
            }
        
        if not utils.validate_clinician_id(clinician_id):
            return {
                "success": False,
                "consent_granted": False,
                "error": "Invalid clinician ID format. Expected format: DR_XXXX",
                "patient_id": patient_id,
                "clinician_id": clinician_id
            }
        
        # Check if patient exists
        patient = utils.get_patient_by_id(patient_id)
        if not patient:
            return {
                "success": True,
                "consent_granted": False,
                "error": f"Patient {patient_id} not found in database",
                "patient_id": patient_id,
                "clinician_id": clinician_id
            }
        
        # Check if clinician exists
        clinician = utils.get_clinician_by_id(clinician_id)
        if not clinician:
            return {
                "success": True,
                "consent_granted": False,
                "error": f"Clinician {clinician_id} not found in database",
                "patient_id": patient_id,
                "clinician_id": clinician_id
            }
        
        # Get consent record
        consent = utils.get_consent_record(patient_id, clinician_id)
        
        if not consent:
            return {
                "success": True,
                "consent_granted": False,
                "error": f"No consent record found for patient {patient_id} and clinician {clinician_id}",
                "patient_id": patient_id,
                "patient_name": patient.get("full_name"),
                "clinician_id": clinician_id,
                "clinician_name": clinician.get("full_name"),
                "recommendation": "Patient must grant consent before access"
            }
        
        # Check if consent is valid (active and not expired)
        is_valid = utils.is_consent_valid(consent)
        
        if not is_valid:
            status = consent.get("status", "unknown")
            expiry = consent.get("expiry_date", "unknown")
            
            return {
                "success": True,
                "consent_granted": False,
                "error": f"Consent is {status} or expired (expiry: {expiry})",
                "patient_id": patient_id,
                "patient_name": patient.get("full_name"),
                "clinician_id": clinician_id,
                "clinician_name": clinician.get("full_name"),
                "consent_id": consent.get("consent_id"),
                "consent_status": status,
                "expiry_date": expiry,
                "recommendation": "Patient must renew consent"
            }
        
        # Consent is valid!
        return {
            "success": True,
            "consent_granted": True,
            "patient_id": patient_id,
            "patient_name": patient.get("full_name"),
            "clinician_id": clinician_id,
            "clinician_name": clinician.get("full_name"),
            "consent_id": consent.get("consent_id"),
            "consent_status": consent.get("status"),
            "granted_date": consent.get("granted_date"),
            "expiry_date": consent.get("expiry_date"),
            "scope": consent.get("scope"),
            "purpose": consent.get("purpose"),
            "message": f"Consent granted: {consent.get('scope')} access for {consent.get('purpose')}"
        }
    
    except Exception as e:
        return utils.handle_error(e, "check_patient_consent_status")

# ============================================================================
# ADK TOOL WRAPPER
# ============================================================================

def check_consent_tool(patient_id: str, clinician_id: str) -> Dict:
    """
    ADK-compatible tool wrapper for consent checking
    
    Args:
        patient_id: Patient ID to check
        clinician_id: Clinician ID requesting access
        
    Returns:
        Consent check result dictionary
    """
    result = check_patient_consent_status(patient_id, clinician_id)
    
    # Log the consent check
    if config.AUDIT_ENABLED:
        utils.log_to_audit_trail(
            clinician_id=clinician_id,
            patient_id=patient_id,
            action="check_consent",
            success=result.get("consent_granted", False),
            details={
                "consent_status": result.get("consent_status", "not_found"),
                "consent_id": result.get("consent_id", "N/A"),
                "scope": result.get("scope", "N/A")
            }
        )
    
    return result

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("✅ CHECK CONSENT TOOL - TEST")
    print("="*60 + "\n")
    
    # Test cases
    test_cases = [
        ("PT_0001", "DR_0001", "Valid consent"),
        ("PT_0001", "DR_0099", "No consent record"),
        ("PT_9999", "DR_0001", "Patient not found"),
        ("INVALID", "DR_0001", "Invalid patient ID"),
        ("PT_0002", "DR_0002", "Another valid case"),
    ]
    
    for patient_id, clinician_id, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Patient: {patient_id}, Clinician: {clinician_id}")
        print("-" * 60)
        
        result = check_consent_tool(patient_id, clinician_id)
        
        if result.get("consent_granted"):
            print(f"✅ CONSENT GRANTED")
            print(f"   Patient: {result.get('patient_name')}")
            print(f"   Clinician: {result.get('clinician_name')}")
            print(f"   Consent ID: {result.get('consent_id')}")
            print(f"   Scope: {result.get('scope')}")
            print(f"   Purpose: {result.get('purpose')}")
            print(f"   Expires: {result.get('expiry_date')}")
        else:
            print(f"❌ CONSENT DENIED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            if result.get('recommendation'):
                print(f"   Recommendation: {result.get('recommendation')}")
    
    print("\n" + "="*60)
    print("✅ Check Consent Test Complete")
    print("="*60 + "\n")