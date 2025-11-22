"""
Token Generator Tool
Generates unique session tokens for tracking access requests
"""

import secrets
import string
from datetime import datetime
from typing import Dict
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
import config

# ============================================================================
# TOKEN GENERATION
# ============================================================================

def generate_session_token() -> str:
    """
    Generate a unique session token
    
    Format: HIPAA_<random_alphanumeric_32_chars>_<timestamp>
    
    Returns:
        Unique token string
    """
    # Generate random alphanumeric string
    alphabet = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(config.TOKEN_LENGTH))
    
    # Add timestamp for uniqueness and traceability
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Combine with prefix
    token = f"{config.TOKEN_PREFIX}_{random_part}_{timestamp}"
    
    return token

# ============================================================================
# TOOL FUNCTION (ADK Compatible)
# ============================================================================

def token_generator_tool() -> Dict:
    """
    Tool function to generate session token
    ADK-compatible function wrapper
    
    Returns:
        Dictionary with success status and token
    """
    try:
        token = generate_session_token()
        
        return {
            "success": True,
            "token": token,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "token_length": len(token),
                "prefix": config.TOKEN_PREFIX
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "token": None
        }

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎫 TOKEN GENERATOR TOOL - TEST")
    print("="*60 + "\n")
    
    # Generate 5 test tokens
    print("Generating 5 unique tokens:\n")
    for i in range(5):
        result = token_generator_tool()
        if result["success"]:
            print(f"{i+1}. ✅ {result['token']}")
        else:
            print(f"{i+1}. ❌ Error: {result['error']}")
    
    print("\n" + "="*60)
    print("✅ Token Generator Test Complete")
    print("="*60 + "\n")