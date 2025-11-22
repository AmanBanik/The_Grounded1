"""
Filter Agent - THE STAR ⭐
Policy enforcement agent with AI-powered validation
Uses Gemini API to understand and enforce HIPAA policies
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import config
import utils

# Gemini API imports
try:
    import google.generativeai as genai
    
    genai.configure(api_key=config.GOOGLE_API_KEY)
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google GenAI not installed!")

# ============================================================================
# POLICY LOADING
# ============================================================================

def load_policies() -> Dict:
    """Load all policy files"""
    try:
        # Load structured JSON policies
        policies_json = utils.load_json_file(config.POLICIES_JSON)
        
        # Load SOP text
        sop_text = ""
        if config.HIPAA_SOP_FILE.exists():
            with open(config.HIPAA_SOP_FILE, 'r', encoding='utf-8') as f:
                sop_text = f.read()
        
        return {
            "structured": policies_json,
            "sop_text": sop_text,
            "loaded": True
        }
    except Exception as e:
        utils.logger.error(f"Failed to load policies: {e}")
        return {"loaded": False, "error": str(e)}

# ============================================================================
# FILTER AGENT CLASS
# ============================================================================

class FilterAgent:
    """
    AI-powered policy enforcement agent
    The STAR of the HIPAA compliance system
    """
    
    def __init__(self):
        """Initialize the Filter Agent"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenAI required for Filter Agent")
        
        # Load policies
        self.policies = load_policies()
        if not self.policies.get("loaded"):
            raise RuntimeError(f"Failed to load policies: {self.policies.get('error')}")
        
        # Create the Gemini-powered agent
        self.agent = self._create_agent()
        
        # Violation counters
        self.violation_count = 0
        self.retry_count = 0
        
        utils.logger.info("✅ Filter Agent initialized with AI-powered validation")
    
    def _create_agent(self):
        """Create the Gemini agent with policy understanding"""
        
        # Extract policy information
        structured = self.policies["structured"]
        sop_text = self.policies["sop_text"]
        
        # Build comprehensive instruction for the agent
        instruction = f"""You are a HIPAA Policy Enforcement Agent. Your job is to validate and enforce medical record access policies.

POLICY DOCUMENTS YOU MUST FOLLOW:

{sop_text}

STRUCTURED POLICIES:
{json.dumps(structured, indent=2)}

YOUR RESPONSIBILITIES:

1. PRE-EXECUTION VALIDATION:
   - Analyze planned tool call sequences
   - Check if they follow required sequences from policies
   - Detect prohibited actions (bulk access, skipped steps, etc.)
   - Validate all parameter formats (clinician_id, patient_id, etc.)
   - Check for consent violations

2. VIOLATION DETECTION:
   - Identify sequence violations (skipped or out-of-order steps)
   - Detect semantic violations (unauthorized intent, improper justification)
   - Recognize bulk access attempts
   - Flag missing audit logging
   - Identify consent scope violations

3. INTELLIGENT CORRECTION:
   - Analyze what went wrong
   - Generate corrected execution plan
   - Explain violations clearly in human terms
   - Suggest proper sequence to follow

4. DECISION MAKING:
   - Classify violation severity (warning, error, critical)
   - Decide if retry is allowed
   - Determine if user consent is required for retry
   - Evaluate emergency access justifications

OUTPUT FORMAT:
Always respond in JSON format with these fields:
{{
  "valid": true/false,
  "violation_type": "none" or type of violation,
  "severity": "none", "warning", "error", or "critical",
  "explanation": "Human-readable explanation",
  "corrected_sequence": [
      {{"tool": "tool_name", "params": {{"param1": "value1"}}}}
  ] or null,
  "allow_retry": true/false,
  "requires_user_consent": true/false,
  "recommendation": "What the user should do"
}}

IMPORTANT: "corrected_sequence" must be a list of OBJECTS with "tool" and "params" keys. Do NOT return a list of strings.

CRITICAL RULES:
- ALWAYS enforce the 4-step sequence: verify_credentials → check_consent → fetch_record → audit_log
- NEVER allow access without valid consent (except documented emergencies)
- ALWAYS require audit logging for every access attempt
- Be strict but helpful - explain violations clearly
- Consider context and intent, not just mechanical rule following
"""
        
        # Use native GenerativeModel for stability and speed
        agent = genai.GenerativeModel(
            model_name=config.FILTER_AGENT_MODEL,
            system_instruction=instruction,
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        
        return agent
    
    # ========================================================================
    # PRE-EXECUTION VALIDATION
    # ========================================================================
    
    def validate_planned_execution(
        self,
        planned_sequence: List[Dict],
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Validate a planned execution sequence before it runs
        """
        try:
            # Build validation query for the AI agent
            query = f"""
VALIDATION REQUEST:

Planned Execution Sequence:
{json.dumps(planned_sequence, indent=2)}

Context:
{json.dumps(context or {}, indent=2)}

TASK: Validate this planned execution against HIPAA policies.

Check for:
1. Required sequence compliance (verify → consent → fetch → log)
2. All required parameters present
3. Correct parameter formats
4. No prohibited actions (bulk access, skipped steps)
5. Consent scope compatibility
6. Semantic violations (unauthorized intent)

Respond ONLY with valid JSON in the required format.
"""
            
            # Get AI validation
            response = self.agent.generate_content(query)
            
            # Parse response
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            validation_result = json.loads(result_text)
            
            # Log validation failure
            if not validation_result.get("valid"):
                self.violation_count += 1
                utils.log_violation(
                    violation_type=validation_result.get("violation_type", "unknown"),
                    description=validation_result.get("explanation", "Unknown violation"),
                    context={
                        "planned_sequence": planned_sequence,
                        "severity": validation_result.get("severity")
                    }
                )
            
            return validation_result
            
        except json.JSONDecodeError as e:
            utils.logger.error(f"Failed to parse AI response: {e}")
            return {
                "valid": False,
                "violation_type": "validation_error",
                "severity": "error",
                "explanation": "Filter agent produced invalid response format",
                "allow_retry": False
            }
        except Exception as e:
            return utils.handle_error(e, "validate_planned_execution")
    
    # ========================================================================
    # POST-EXECUTION VALIDATION
    # ========================================================================
    
    def validate_execution_result(
        self,
        executed_sequence: List[Dict],
        results: List[Dict]
    ) -> Dict:
        """
        Validate execution results after tools have run
        """
        try:
            query = f"""
POST-EXECUTION VALIDATION:

Executed Sequence:
{json.dumps(executed_sequence, indent=2)}

Execution Results:
{json.dumps(results, indent=2)}

TASK: Validate that execution followed policy and all required steps succeeded.

Check for:
1. All required steps were executed
2. Steps executed in correct order
3. Audit logging was performed
4. No data leakage or unauthorized access
5. Results match consent scope

Respond ONLY with valid JSON in the required format.
"""
            
            response = self.agent.generate_content(query)
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            validation_result = json.loads(result_text)
            
            if not validation_result.get("valid"):
                utils.log_violation(
                    violation_type=validation_result.get("violation_type", "unknown"),
                    description=validation_result.get("explanation", "Unknown violation"),
                    context={
                        "executed_sequence": executed_sequence,
                        "results": results
                    }
                )
            
            return validation_result
            
        except Exception as e:
            return utils.handle_error(e, "validate_execution_result")
    
    # ========================================================================
    # INTELLIGENT CORRECTION
    # ========================================================================
    
    def generate_corrected_sequence(
        self,
        invalid_sequence: List[Dict],
        violation_info: Dict
    ) -> Optional[List[Dict]]:
        """
        Use AI to generate a corrected execution sequence
        """
        try:
            query = f"""
CORRECTION REQUEST:

Invalid Sequence:
{json.dumps(invalid_sequence, indent=2)}

Violation Details:
{json.dumps(violation_info, indent=2)}

TASK: Generate a corrected sequence that follows HIPAA policy.

Requirements:
1. Must follow required sequence: verify → consent → fetch → log
2. Must include all mandatory parameters
3. Must fix the identified violations
4. Must be executable

Respond with ONLY a JSON array of corrected tool calls, or null if cannot be corrected.
Format: [{{"tool": "tool_name", "params": {{"param1": "value1"}}}}]
"""
            
            response = self.agent.generate_content(query)
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            corrected = json.loads(result_text)
            
            return corrected if isinstance(corrected, list) else None
            
        except Exception as e:
            utils.logger.error(f"Failed to generate correction: {e}")
            return None
    
    # ========================================================================
    # RETRY HANDLING
    # ========================================================================
    
    def handle_retry(
        self,
        original_request: Dict,
        violation_info: Dict
    ) -> Dict:
        """
        Handle retry logic for policy violations
        """
        try:
            # Check if retry is allowed
            severity = violation_info.get("severity", "error")
            
            if severity == "critical":
                return {
                    "allow_retry": False,
                    "reason": "Critical violations cannot be retried. Requires admin review.",
                    "corrected_request": None
                }
            
            # Check retry count
            if self.retry_count >= config.FILTER_MAX_RETRIES:
                return {
                    "allow_retry": False,
                    "reason": f"Maximum retry attempts ({config.FILTER_MAX_RETRIES}) exceeded.",
                    "corrected_request": None
                }
            
            # Generate corrected sequence
            corrected = self.generate_corrected_sequence(
                invalid_sequence=original_request.get("sequence", []),
                violation_info=violation_info
            )
            
            if not corrected:
                return {
                    "allow_retry": False,
                    "reason": "Unable to generate valid correction.",
                    "corrected_request": None
                }
            
            # Increment retry counter
            self.retry_count += 1
            
            return {
                "allow_retry": True,
                "requires_user_consent": config.FILTER_REQUIRE_USER_CONSENT,
                "corrected_request": corrected,
                "explanation": violation_info.get("explanation"),
                "recommendation": violation_info.get("recommendation"),
                "retry_number": self.retry_count
            }
            
        except Exception as e:
            return utils.handle_error(e, "handle_retry")
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def reset_counters(self):
        """Reset violation and retry counters"""
        self.violation_count = 0
        self.retry_count = 0
    
    def get_statistics(self) -> Dict:
        """Get filter agent statistics"""
        return {
            "total_violations": self.violation_count,
            "total_retries": self.retry_count,
            "policies_loaded": self.policies.get("loaded", False)
        }
    
    def reload_policies(self) -> bool:
        """Reload policy files (for admin updates)"""
        try:
            self.policies = load_policies()
            if self.policies.get("loaded"):
                # Recreate agent with new policies
                self.agent = self._create_agent()
                utils.logger.info("✅ Policies reloaded successfully")
                return True
            return False
        except Exception as e:
            utils.logger.error(f"Failed to reload policies: {e}")
            return False

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global filter agent instance
_filter_agent_instance = None

def get_filter_agent() -> FilterAgent:
    """Get or create the global filter agent instance"""
    global _filter_agent_instance
    if _filter_agent_instance is None:
        _filter_agent_instance = FilterAgent()
    return _filter_agent_instance

def validate_sequence(planned_sequence: List[Dict], context: Optional[Dict] = None) -> Dict:
    """Convenience function to validate a sequence"""
    agent = get_filter_agent()
    return agent.validate_planned_execution(planned_sequence, context)

def validate_results(executed_sequence: List[Dict], results: List[Dict]) -> Dict:
    """Convenience function to validate execution results"""
    agent = get_filter_agent()
    return agent.validate_execution_result(executed_sequence, results)

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import time  # Import time for rate limiting
    
    print("\n" + "="*60)
    print("⭐ FILTER AGENT - THE STAR - TEST")
    print("="*60 + "\n")
    
    if not GEMINI_AVAILABLE:
        print("❌ Google GenAI not installed!")
        sys.exit(1)
    
    try:
        # Initialize filter agent
        print("Initializing Filter Agent...")
        filter_agent = FilterAgent()
        print(f"✅ Filter Agent initialized with {config.FILTER_AGENT_MODEL}\n")
        
        # Test 1: Valid sequence
        print("Test 1: Valid HIPAA-compliant sequence")
        print("-" * 60)
        valid_sequence = [
            {"tool": "verify_clinician_credentials", "params": {"clinician_id": "DR_0001"}},
            {"tool": "check_patient_consent_status", "params": {"patient_id": "PT_0001", "clinician_id": "DR_0001"}},
            {"tool": "fetch_patient_record", "params": {"patient_id": "PT_0001"}},
            # FIX: Use a token that matches the regex ^HIPAA_[A-Z0-9]+_\d{14}$
            {"tool": "log_access_to_audit_trail", "params": {
                "clinician_id": "DR_0001", 
                "patient_id": "PT_0001", 
                "action": "fetch_record", 
                "success": True, 
                "token_id": "HIPAA_TESTTOKEN_20251123120000"
            }}
        ]
        
        result = filter_agent.validate_planned_execution(valid_sequence)
        if result.get("valid"):
            print("✅ VALID - Sequence follows HIPAA policy")
        else:
            print(f"❌ INVALID - {result.get('explanation')}")
        
        # RATE LIMIT PAUSE
        print("\n⏳ Waiting 35s to respect API Rate Limit (Free Tier)...")
        time.sleep(35)
        
        # Test 2: Invalid sequence (skipped consent check)
        print("\n" + "-" * 60)
        print("\nTest 2: Invalid sequence (skipped consent check)")
        print("-" * 60)
        invalid_sequence = [
            {"tool": "verify_clinician_credentials", "params": {"clinician_id": "DR_0001"}},
            {"tool": "fetch_patient_record", "params": {"patient_id": "PT_0001"}},
        ]
        
        result = filter_agent.validate_planned_execution(invalid_sequence)
        if not result.get("valid"):
            print(f"✅ BLOCKED (Expected)")
            print(f"   Violation: {result.get('violation_type')}")
            print(f"   Severity: {result.get('severity')}")
            print(f"   Explanation: {result.get('explanation')}")
            print(f"   Allow Retry: {result.get('allow_retry')}")
        else:
             print("❌ FAILED TO BLOCK INVALID SEQUENCE")
        
        # RATE LIMIT PAUSE
        print("\n⏳ Waiting 35s to respect API Rate Limit (Free Tier)...")
        time.sleep(35)

        # Test 3: Out of order sequence
        print("\n" + "-" * 60)
        print("\nTest 3: Out-of-order sequence")
        print("-" * 60)
        out_of_order = [
            {"tool": "check_patient_consent_status", "params": {"patient_id": "PT_0001", "clinician_id": "DR_0001"}},
            {"tool": "verify_clinician_credentials", "params": {"clinician_id": "DR_0001"}},
            {"tool": "fetch_patient_record", "params": {"patient_id": "PT_0001"}},
        ]
        
        result = filter_agent.validate_planned_execution(out_of_order)
        if not result.get("valid"):
            print(f"✅ BLOCKED (Expected)")
            print(f"   Violation: {result.get('violation_type')}")
            print(f"   Explanation: {result.get('explanation')}")
        else:
             print("❌ FAILED TO BLOCK OUT-OF-ORDER SEQUENCE")
        
        # Test 4: Statistics
        print("\n" + "-" * 60)
        print("\nFilter Agent Statistics:")
        print("-" * 60)
        stats = filter_agent.get_statistics()
        print(f"✅ Total Violations Detected: {stats['total_violations']}")
        print(f"✅ Total Retries: {stats['total_retries']}")
        print(f"✅ Policies Loaded: {stats['policies_loaded']}")
        
        print("\n" + "="*60)
        print("✅ Filter Agent Test Complete")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}\n")
        raise