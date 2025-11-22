"""
Audit Logger Tool
Logs all access attempts to the audit trail for HIPAA compliance
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
# AUDIT LOGGING
# ============================================================================

def log_access_to_audit_trail(
    clinician_id: str,
    patient_id: str,
    action: str,
    success: bool,
    token_id: Optional[str] = None,
    details: Optional[Dict] = None
) -> Dict:
    """
    Log access attempt to audit trail
    
    Args:
        clinician_id: ID of clinician making request
        patient_id: ID of patient being accessed
        action: Action performed (fetch_record, append_record, etc.)
        success: Whether action succeeded
        token_id: Session token ID
        details: Additional details about the action
        
    Returns:
        Dictionary with logging result
    """
    try:
        # Validate inputs
        if not clinician_id or not patient_id or not action:
            return {
                "success": False,
                "logged": False,
                "error": "Missing required parameters: clinician_id, patient_id, or action"
            }
        
        # Get clinician and patient names for better audit readability
        clinician = utils.get_clinician_by_id(clinician_id)
        patient = utils.get_patient_by_id(patient_id)
        
        clinician_name = clinician.get("full_name") if clinician else "Unknown"
        patient_name = patient.get("full_name") if patient else "Unknown"
        
        # Enhanced details
        enhanced_details = details or {}
        enhanced_details.update({
            "clinician_name": clinician_name,
            "patient_name": patient_name,
            "action_timestamp": datetime.now().isoformat()
        })
        
        # Log to audit trail
        logged = utils.log_to_audit_trail(
            clinician_id=clinician_id,
            patient_id=patient_id,
            action=action,
            success=success,
            token_id=token_id,
            details=enhanced_details
        )
        
        if not logged:
            return {
                "success": False,
                "logged": False,
                "error": "Failed to write to audit trail file"
            }
        
        return {
            "success": True,
            "logged": True,
            "clinician_id": clinician_id,
            "patient_id": patient_id,
            "action": action,
            "action_success": success,
            "token_id": token_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Access logged: {action} by {clinician_name} for {patient_name}"
        }
    
    except Exception as e:
        return utils.handle_error(e, "log_access_to_audit_trail")

# ============================================================================
# ADK TOOL WRAPPER
# ============================================================================

def audit_logger_tool(
    clinician_id: str,
    patient_id: str,
    action: str,
    success: bool,
    token_id: Optional[str] = None,
    details: Optional[Dict] = None
) -> Dict:
    """
    ADK-compatible tool wrapper for audit logging
    
    Args:
        clinician_id: Clinician ID
        patient_id: Patient ID
        action: Action performed
        success: Whether action succeeded
        token_id: Session token
        details: Additional details
        
    Returns:
        Logging result dictionary
    """
    return log_access_to_audit_trail(
        clinician_id=clinician_id,
        patient_id=patient_id,
        action=action,
        success=success,
        token_id=token_id,
        details=details
    )

# ============================================================================
# AUDIT TRAIL QUERY FUNCTIONS
# ============================================================================

def get_audit_history(
    clinician_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 10
) -> Dict:
    """
    Retrieve audit history with optional filtering
    
    Args:
        clinician_id: Filter by clinician (optional)
        patient_id: Filter by patient (optional)
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with audit records
    """
    try:
        audit_data = utils.load_json_file(config.AUDIT_LOG)
        
        if not isinstance(audit_data, list):
            audit_data = []
        
        # Filter if needed
        filtered = audit_data
        if clinician_id:
            filtered = [r for r in filtered if r.get("clinician_id") == clinician_id]
        if patient_id:
            filtered = [r for r in filtered if r.get("patient_id") == patient_id]
        
        # Sort by timestamp (most recent first) and limit
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        filtered = filtered[:limit]
        
        return {
            "success": True,
            "records": filtered,
            "count": len(filtered),
            "total_count": len(audit_data)
        }
    
    except Exception as e:
        return utils.handle_error(e, "get_audit_history")

def get_access_statistics() -> Dict:
    """
    Get statistics about access attempts
    
    Returns:
        Dictionary with statistics
    """
    try:
        audit_data = utils.load_json_file(config.AUDIT_LOG)
        
        if not isinstance(audit_data, list):
            audit_data = []
        
        total_accesses = len(audit_data)
        successful_accesses = len([r for r in audit_data if r.get("success")])
        failed_accesses = total_accesses - successful_accesses
        
        # Count by action type
        action_counts = {}
        for record in audit_data:
            action = record.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Most active clinicians
        clinician_counts = {}
        for record in audit_data:
            clinician_id = record.get("clinician_id", "unknown")
            clinician_counts[clinician_id] = clinician_counts.get(clinician_id, 0) + 1
        
        return {
            "success": True,
            "total_accesses": total_accesses,
            "successful_accesses": successful_accesses,
            "failed_accesses": failed_accesses,
            "success_rate": round(successful_accesses / total_accesses * 100, 2) if total_accesses > 0 else 0,
            "action_counts": action_counts,
            "top_clinicians": dict(sorted(clinician_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    except Exception as e:
        return utils.handle_error(e, "get_access_statistics")

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📝 AUDIT LOGGER TOOL - TEST")
    print("="*60 + "\n")
    
    # Test logging various access attempts
    test_logs = [
        {
            "clinician_id": "DR_0001",
            "patient_id": "PT_0001",
            "action": "fetch_record",
            "success": True,
            "token_id": "HIPAA_TEST123_20240101",
            "details": {"reason": "Routine checkup"}
        },
        {
            "clinician_id": "DR_0002",
            "patient_id": "PT_0002",
            "action": "fetch_record",
            "success": False,
            "token_id": "HIPAA_TEST456_20240101",
            "details": {"reason": "No consent", "error": "Consent expired"}
        },
        {
            "clinician_id": "DR_0001",
            "patient_id": "PT_0003",
            "action": "append_record",
            "success": True,
            "token_id": "HIPAA_TEST789_20240101",
            "details": {"note": "Updated medication list"}
        },
    ]
    
    print("Logging test access attempts:\n")
    for i, log_data in enumerate(test_logs, 1):
        print(f"Test {i}:")
        result = audit_logger_tool(**log_data)
        
        if result.get("logged"):
            print(f"   ✅ {result.get('message')}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
        print()
    
    # Test audit history retrieval
    print("-" * 60)
    print("\nRetrieving audit history:")
    history = get_audit_history(limit=5)
    
    if history.get("success"):
        print(f"✅ Retrieved {history.get('count')} records (of {history.get('total_count')} total)")
        for record in history.get("records", [])[:3]:
            print(f"\n   • {record.get('action')} by {record.get('clinician_id')}")
            print(f"     Patient: {record.get('patient_id')}")
            print(f"     Success: {record.get('success')}")
            print(f"     Time: {record.get('timestamp')}")
    
    # Test statistics
    print("\n" + "-" * 60)
    print("\nAccess Statistics:")
    stats = get_access_statistics()
    
    if stats.get("success"):
        print(f"✅ Total Accesses: {stats.get('total_accesses')}")
        print(f"   Successful: {stats.get('successful_accesses')}")
        print(f"   Failed: {stats.get('failed_accesses')}")
        print(f"   Success Rate: {stats.get('success_rate')}%")
    
    print("\n" + "="*60)
    print("✅ Audit Logger Test Complete")
    print("="*60 + "\n")