"""
Verify Credentials Tool
Verifies clinician credentials against the database
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
import config
import utils

# ============================================================================
# CREDENTIAL VERIFICATION
# ============================================================================

def verify_clinician_credentials(clinician_id: str) -> Dict:
    """
    Verify clinician credentials
    
    Args:
        clinician_id: Clinician ID to verify (format: DR_XXXX)
        
    Returns:
        Dictionary with verification result and clinician info
    """
    try:
        # Validate ID format
        if not utils.validate_clinician_id(clinician_id):
            return {
                "success": False,
                "verified": False,
                "error": "Invalid clinician ID format. Expected format: DR_XXXX",
                "clinician_id": clinician_id
            }
        
        # Load clinician database
        clinician = utils.get_clinician_by_id(clinician_id)
        
        # Check if clinician exists
        if not clinician:
            return {
                "success": True,
                "verified": False,
                "error": f"Clinician {clinician_id} not found in database",
                "clinician_id": clinician_id
            }
        
        # Check if clinician is active
        if not clinician.get("active", False):
            return {
                "success": True,
                "verified": False,
                "error": f"Clinician {clinician_id} is inactive",
                "clinician_id": clinician_id,
                "clinician_name": clinician.get("full_name")
            }
        
        # Credentials verified successfully
        return {
            "success": True,
            "verified": True,
            "clinician_id": clinician_id,
            "clinician_name": clinician.get("full_name"),
            "specialization": clinician.get("specialization"),
            "department": clinician.get("department"),
            "clearance_level": clinician.get("clearance_level"),
            "license_number": clinician.get("license_number"),
            "message": f"Credentials verified for {clinician.get('full_name')}"
        }
    
    except Exception as e:
        return utils.handle_error(e, "verify_clinician_credentials")

# ============================================================================
# ADK TOOL WRAPPER
# ============================================================================

def verify_credentials_tool(clinician_id: str) -> Dict:
    """
    ADK-compatible tool wrapper for credential verification
    
    Args:
        clinician_id: Clinician ID to verify
        
    Returns:
        Verification result dictionary
    """
    result = verify_clinician_credentials(clinician_id)
    
    # Log the verification attempt
    if config.AUDIT_ENABLED:
        utils.log_to_audit_trail(
            clinician_id=clinician_id,
            patient_id="N/A",
            action="verify_credentials",
            success=result.get("verified", False),
            details={
                "clinician_name": result.get("clinician_name", "Unknown"),
                "verification_result": "verified" if result.get("verified") else "failed"
            }
        )
    
    return result

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔐 VERIFY CREDENTIALS TOOL - TEST")
    print("="*60 + "\n")
    
    # Test cases
    test_cases = [
        ("DR_0001", "Valid clinician"),
        ("DR_0099", "Non-existent clinician"),
        ("INVALID_ID", "Invalid format"),
        ("DR_0002", "Another valid clinician"),
    ]
    
    for clinician_id, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Clinician ID: {clinician_id}")
        print("-" * 60)
        
        result = verify_credentials_tool(clinician_id)
        
        if result.get("verified"):
            print(f"✅ VERIFIED")
            print(f"   Name: {result.get('clinician_name')}")
            print(f"   Specialization: {result.get('specialization')}")
            print(f"   Department: {result.get('department')}")
            print(f"   Clearance Level: {result.get('clearance_level')}")
        else:
            print(f"❌ VERIFICATION FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    print("✅ Verify Credentials Test Complete")
    print("="*60 + "\n")