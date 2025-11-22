"""
Template ~
Configuration file for HIPAA-Compliant Agent System
Contains all constants, paths, and API setup
"""

import os
from pathlib import Path

# ============================================================================
# API CONFIGURATION
# ============================================================================

# OPTION 1: Direct API Key (For local testing/Kaggle submission)
# Uncomment the line below and paste your key:
GOOGLE_API_KEY = "Add your API key here"

# OPTION 2: Environment Variable (More secure for production)
# Comment out the line above and uncomment the lines below:
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     raise ValueError(
#         "❌ GOOGLE_API_KEY not found!\n"
#         "Please set it in your terminal:\n"
#         "  export GOOGLE_API_KEY='your_api_key_here'\n"
#         "Or add it to your ~/.bashrc or ~/.zshrc for persistence."
#     )

# Validate key is set
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "paste_your_api_key_here":
    raise ValueError(
        "❌ Please set your GOOGLE_API_KEY in config.py!\n"
        "Replace 'paste_your_api_key_here' with your actual API key."
    )

# Set up environment for Google GenAI
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

print("✅ Gemini API key loaded successfully.")

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Model selection
ROOT_AGENT_MODEL = "gemini-2.0-flash"  # Fast orchestration
FILTER_AGENT_MODEL = "gemini-2.5-pro"  # Deep reasoning for policy validation
TOOL_AGENT_MODEL = "gemini-2.0-flash"  # For summarizer tool

# Retry configuration for API calls
RETRY_ATTEMPTS = 5
RETRY_EXP_BASE = 7
RETRY_INITIAL_DELAY = 1
RETRY_HTTP_CODES = [429, 500, 503, 504]

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Base project directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
POLICIES_DIR = PROJECT_ROOT / "policies"
LOGS_DIR = PROJECT_ROOT / "logs"
TOOLS_DIR = PROJECT_ROOT / "tools"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
POLICIES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
TOOLS_DIR.mkdir(exist_ok=True)

# Specific data files
CLINICIANS_DB = DATA_DIR / "clinicians.json"
PATIENTS_DB = DATA_DIR / "patients.json"
CONSENT_DB = DATA_DIR / "consent_records.json"

# Policy files
HIPAA_SOP_FILE = POLICIES_DIR / "hipaa_SOP.txt"
POLICIES_JSON = POLICIES_DIR / "policies.json"
POLICY_OVERRIDES_XLS = POLICIES_DIR / "policy_overrides.xlsx"

# Log files
AUDIT_LOG = LOGS_DIR / "audit_trail.json"
VIOLATIONS_LOG = LOGS_DIR / "violations.log"
ERROR_LOG = LOGS_DIR / "errors.log"

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Token settings
TOKEN_LENGTH = 32  # Length of unique session tokens
TOKEN_PREFIX = "HIPAA"  # Prefix for easy identification

# Filter agent settings
FILTER_MAX_RETRIES = 3  # Max retry attempts for policy violations
FILTER_REQUIRE_USER_CONSENT = True  # Ask user before retry

# Audit settings
AUDIT_ENABLED = True  # Always log to audit trail
LOG_FAILED_ATTEMPTS = True  # Log even failed access attempts

# ============================================================================
# ADMIN CONFIGURATION
# ============================================================================

# Admin password (In production, use proper authentication!)
# For this demo, simple password protection
ADMIN_PASSWORD = "hipaa_admin_2025"  # Change this!

# Admin capabilities
ADMIN_CAN_EDIT_POLICIES = True
ADMIN_CAN_VIEW_LOGS = True
ADMIN_CAN_RESET_DATA = True

# ============================================================================
# MOCK DATA SETTINGS
# ============================================================================

# Number of mock records to generate
NUM_MOCK_CLINICIANS = 10
NUM_MOCK_PATIENTS = 50
NUM_MOCK_CONSENT_RECORDS = 50

# Mock data generation seed (for reproducibility)
RANDOM_SEED = 42

# ============================================================================
# SYSTEM MESSAGES
# ============================================================================

WELCOME_MESSAGE = """
╔═══════════════════════════════════════════════════════════╗
║     HIPAA-Compliant Medical Records Access System         ║
║              Powered by Multi-Agent Architecture          ║
╚═══════════════════════════════════════════════════════════╝

⚕️  All access is monitored and logged for compliance.
🔒 Policy enforcement active via Filter Agent.
"""

ADMIN_WELCOME = """
╔═══════════════════════════════════════════════════════════╗
║                 ADMINISTRATOR MODE                         ║
║            Policy Management & Audit Access                ║
╚═══════════════════════════════════════════════════════════╝
"""

# ============================================================================
# VALIDATION RULES (Used by Filter Agent)
# ============================================================================

# Required sequence of operations for record access
REQUIRED_SEQUENCE = [
    "verify_clinician_credentials",
    "check_patient_consent_status",
    "fetch_patient_record",
    "log_access_to_audit_trail"
]

# Operations that must ALWAYS be logged
MUST_LOG_OPERATIONS = [
    "fetch_patient_record",
    "record_appender",
    "pdf_generator"
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_retry_config():
    """Returns retry configuration for Gemini API calls"""
    from google.genai import types
    
    return types.HttpRetryOptions(
        attempts=RETRY_ATTEMPTS,
        exp_base=RETRY_EXP_BASE,
        initial_delay=RETRY_INITIAL_DELAY,
        http_status_codes=RETRY_HTTP_CODES,
    )

def validate_setup():
    """Validates that all required files and directories exist"""
    issues = []
    
    # Check directories
    if not DATA_DIR.exists():
        issues.append(f"❌ Data directory missing: {DATA_DIR}")
    if not POLICIES_DIR.exists():
        issues.append(f"❌ Policies directory missing: {POLICIES_DIR}")
    if not LOGS_DIR.exists():
        issues.append(f"❌ Logs directory missing: {LOGS_DIR}")
    
    # Check mock data files (these will be created by generate_mock_data.py)
    if not CLINICIANS_DB.exists():
        issues.append(f"⚠️  Clinicians database not found: {CLINICIANS_DB}")
    if not PATIENTS_DB.exists():
        issues.append(f"⚠️  Patients database not found: {PATIENTS_DB}")
    if not CONSENT_DB.exists():
        issues.append(f"⚠️  Consent database not found: {CONSENT_DB}")
    
    # Check policy files (these will be created later)
    if not HIPAA_SOP_FILE.exists():
        issues.append(f"⚠️  HIPAA SOP file not found: {HIPAA_SOP_FILE}")
    if not POLICIES_JSON.exists():
        issues.append(f"⚠️  Policies JSON not found: {POLICIES_JSON}")
    
    if issues:
        print("\n".join(issues))
        if any("❌" in issue for issue in issues):
            raise RuntimeError("Critical setup issues found!")
        else:
            print("\n⚠️  Some files missing - run generate_mock_data.py first!")
    else:
        print("✅ All setup validated successfully!")

# ============================================================================
# INITIALIZATION
# ============================================================================

# ============================================================================
# MEMORY CONFIGURATION
# ============================================================================

# Memory settings
MEMORY_ENABLED = True
MEMORY_DURATION_HOURS = 12  # Sessions expire after 12 hours
MEMORY_DB_PATH = PROJECT_ROOT / "memory.db"

# What to remember
REMEMBER_LAST_PATIENT = True
REMEMBER_LAST_CLINICIAN = True
REMEMBER_CONVERSATION_HISTORY = True
MAX_CONVERSATION_HISTORY = 5  # Keep last 5 interactions

# ============================================================================
# INITIALIZATION
# ============================================================================

print("✅ Configuration loaded successfully.")
print(f"📁 Project root: {PROJECT_ROOT}")
print(f"🤖 Root Agent Model: {ROOT_AGENT_MODEL}")
print(f"🛡️  Filter Agent Model: {FILTER_AGENT_MODEL}")
print(f"💾 Memory Enabled: {MEMORY_ENABLED} ({MEMORY_DURATION_HOURS}h expiry)")