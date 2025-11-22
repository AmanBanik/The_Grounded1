"""
Utility Functions for HIPAA-Compliant Agent System
Shared helper functions for logging, formatting, and validation
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import config

# ============================================================================
# LOGGING SETUP
# ============================================================================

### utils.py

def setup_logging():
    """Configure logging for the application"""
    # Create the log directory if it doesn't exist to prevent FileNotFoundError
    config.LOGS_DIR.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # FIX: Added encoding='utf-8' to support emojis in logs on Windows
            logging.FileHandler(config.ERROR_LOG, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()
# ============================================================================
# JSON FILE OPERATIONS
# ============================================================================

def load_json_file(filepath: Path) -> Any:
    """
    Safely load JSON file with error handling
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded JSON data or empty list/dict on error
    """
    try:
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filepath}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return []

def save_json_file(filepath: Path, data: Any, indent: int = 2) -> bool:
    """
    Safely save data to JSON file
    
    Args:
        filepath: Path to save file
        data: Data to save
        indent: JSON indentation level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error saving to {filepath}: {e}")
        return False

def append_to_json_array(filepath: Path, new_item: Dict) -> bool:
    """
    Append item to JSON array file
    
    Args:
        filepath: Path to JSON array file
        new_item: Item to append
        
    Returns:
        True if successful, False otherwise
    """
    try:
        data = load_json_file(filepath)
        if not isinstance(data, list):
            data = []
        
        data.append(new_item)
        return save_json_file(filepath, data)
    except Exception as e:
        logger.error(f"Error appending to {filepath}: {e}")
        return False

# ============================================================================
# AUDIT LOGGING
# ============================================================================

def log_to_audit_trail(
    clinician_id: str,
    patient_id: str,
    action: str,
    success: bool,
    details: Optional[Dict] = None,
    token_id: Optional[str] = None
) -> bool:
    """
    Log access attempt to audit trail
    
    Args:
        clinician_id: ID of clinician making request
        patient_id: ID of patient being accessed
        action: Action performed (fetch_record, append_record, etc.)
        success: Whether action succeeded
        details: Additional details about the action
        token_id: Session token ID
        
    Returns:
        True if logged successfully
    """
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "clinician_id": clinician_id,
        "patient_id": patient_id,
        "action": action,
        "success": success,
        "token_id": token_id,
        "details": details or {}
    }
    
    result = append_to_json_array(config.AUDIT_LOG, audit_entry)
    
    if result:
        logger.info(f"Audit log: {action} by {clinician_id} for {patient_id} - {'SUCCESS' if success else 'FAILED'}")
    else:
        logger.error(f"Failed to write audit log for {clinician_id}")
    
    return result

def log_violation(
    violation_type: str,
    description: str,
    context: Optional[Dict] = None
) -> bool:
    """
    Log policy violation
    
    Args:
        violation_type: Type of violation (sequence_error, missing_consent, etc.)
        description: Human-readable description
        context: Additional context about the violation
        
    Returns:
        True if logged successfully
    """
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {violation_type}: {description}\n"
    
    if context:
        log_entry += f"Context: {json.dumps(context, indent=2)}\n"
    
    log_entry += "-" * 80 + "\n"
    
    try:
        with open(config.VIOLATIONS_LOG, 'a') as f:
            f.write(log_entry)
        logger.warning(f"Policy violation logged: {violation_type}")
        return True
    except Exception as e:
        logger.error(f"Failed to log violation: {e}")
        return False

# ============================================================================
# DATA LOOKUP HELPERS
# ============================================================================

def find_by_id(data: List[Dict], id_field: str, id_value: str) -> Optional[Dict]:
    """
    Find item in list by ID field
    
    Args:
        data: List of dictionaries
        id_field: Name of ID field to search
        id_value: Value to search for
        
    Returns:
        Found item or None
    """
    for item in data:
        if item.get(id_field) == id_value:
            return item
    return None

def get_clinician_by_id(clinician_id: str) -> Optional[Dict]:
    """Get clinician record by ID"""
    clinicians = load_json_file(config.CLINICIANS_DB)
    return find_by_id(clinicians, "clinician_id", clinician_id)

def get_patient_by_id(patient_id: str) -> Optional[Dict]:
    """Get patient record by ID"""
    patients = load_json_file(config.PATIENTS_DB)
    return find_by_id(patients, "patient_id", patient_id)

def get_consent_record(patient_id: str, clinician_id: str) -> Optional[Dict]:
    """Get consent record for specific patient-clinician pair"""
    consents = load_json_file(config.CONSENT_DB)
    
    for consent in consents:
        if (consent.get("patient_id") == patient_id and 
            consent.get("clinician_id") == clinician_id):
            return consent
    return None

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_id_format(id_string: str, expected_prefix: str) -> bool:
    """
    Validate ID format (PREFIX_NNNN)
    
    Args:
        id_string: ID to validate
        expected_prefix: Expected prefix (DR, PT, CNS, etc.)
        
    Returns:
        True if valid format
    """
    if not id_string:
        return False
    
    parts = id_string.split('_')
    if len(parts) != 2:
        return False
    
    prefix, number = parts
    return prefix == expected_prefix and number.isdigit()

def validate_clinician_id(clinician_id: str) -> bool:
    """Validate clinician ID format"""
    return validate_id_format(clinician_id, "DR")

def validate_patient_id(patient_id: str) -> bool:
    """Validate patient ID format"""
    return validate_id_format(patient_id, "PT")

def validate_token_format(token: str) -> bool:
    """Validate session token format"""
    if not token:
        return False
    return token.startswith(config.TOKEN_PREFIX) and len(token) > len(config.TOKEN_PREFIX)

# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_timestamp(timestamp: Optional[str] = None) -> str:
    """
    Format timestamp for display
    
    Args:
        timestamp: ISO format timestamp or None for current time
        
    Returns:
        Formatted timestamp string
    """
    if timestamp:
        dt = datetime.fromisoformat(timestamp)
    else:
        dt = datetime.now()
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_patient_summary(patient: Dict) -> str:
    """
    Format patient data for display
    
    Args:
        patient: Patient record dictionary
        
    Returns:
        Formatted string
    """
    summary = f"""
Patient ID: {patient.get('patient_id')}
Name: {patient.get('full_name')}
DOB: {patient.get('date_of_birth')}
Gender: {patient.get('gender')}
Blood Type: {patient.get('blood_type')}
Phone: {patient.get('phone')}
Last Visit: {patient.get('last_visit')}
    """
    return summary.strip()

def format_clinician_summary(clinician: Dict) -> str:
    """
    Format clinician data for display
    
    Args:
        clinician: Clinician record dictionary
        
    Returns:
        Formatted string
    """
    summary = f"""
Clinician ID: {clinician.get('clinician_id')}
Name: {clinician.get('full_name')}
Specialization: {clinician.get('specialization')}
Department: {clinician.get('department')}
License: {clinician.get('license_number')}
    """
    return summary.strip()

def format_operation_sequence(operations: List[str]) -> str:
    """
    Format list of operations as numbered sequence
    
    Args:
        operations: List of operation names
        
    Returns:
        Formatted string
    """
    return "\n".join([f"{i+1}. {op}" for i, op in enumerate(operations)])

# ============================================================================
# TERMINAL OUTPUT HELPERS
# ============================================================================

def print_header(text: str, width: int = 60):
    """Print formatted header"""
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width + "\n")

def print_subheader(text: str, width: int = 60):
    """Print formatted subheader"""
    print("\n" + "-" * width)
    print(text)
    print("-" * width)

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")

# ============================================================================
# CONSENT VALIDATION
# ============================================================================

def is_consent_valid(consent: Dict) -> bool:
    """
    Check if consent is currently valid
    
    Args:
        consent: Consent record dictionary
        
    Returns:
        True if consent is active and not expired
    """
    if consent.get("status") != "active":
        return False
    
    expiry_str = consent.get("expiry_date")
    if not expiry_str:
        return False
    
    try:
        expiry_date = datetime.fromisoformat(expiry_str)
        return expiry_date > datetime.now()
    except:
        return False

# ============================================================================
# USER INPUT HELPERS
# ============================================================================

def get_yes_no_input(prompt: str, default: bool = False) -> bool:
    """
    Get yes/no input from user
    
    Args:
        prompt: Question to ask
        default: Default value if user just presses enter
        
    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes']

def get_user_confirmation(action: str) -> bool:
    """
    Get user confirmation for an action
    
    Args:
        action: Action description
        
    Returns:
        True if user confirms
    """
    print_warning(f"About to: {action}")
    return get_yes_no_input("Do you want to proceed?", default=False)

# ============================================================================
# ERROR HANDLING
# ============================================================================

def handle_error(error: Exception, context: str = "") -> Dict:
    """
    Handle and log error, return structured error response
    
    Args:
        error: Exception object
        context: Context description
        
    Returns:
        Error response dictionary
    """
    error_msg = f"{context}: {str(error)}" if context else str(error)
    logger.error(error_msg, exc_info=True)
    
    return {
        "success": False,
        "error": error_msg,
        "error_type": type(error).__name__
    }

# ============================================================================
# INITIALIZATION
# ============================================================================

print("✅ Utils module loaded successfully.")