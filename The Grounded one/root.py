"""
Root Orchestrator Agent
The brain that coordinates all tools and works with Filter Agent
Uses Gemini API for natural language understanding and workflow orchestration
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import re

import config
import utils
from filter import get_filter_agent
from memory_manager import get_memory_manager

# Import all tool functions
sys.path.append(str(config.TOOLS_DIR))
from tools.token_generator import token_generator_tool
from tools.verify_credentials import verify_credentials_tool
from tools.check_consent import check_consent_tool
from tools.fetch_record import fetch_record_tool
from tools.audit_logger import audit_logger_tool
from tools.record_appender import record_appender_tool
from tools.pdf_generator import pdf_generator_tool
from tools.report_summarizer import report_summarizer_tool

# Gemini API imports
try:
    import google.generativeai as genai
    genai.configure(api_key=config.GOOGLE_API_KEY)
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google GenAI not installed!")

# ============================================================================
# ROOT AGENT CLASS
# ============================================================================

class RootAgent:
    """
    Root orchestrator agent - The Brain
    Coordinates all tools and enforces HIPAA compliance via Filter Agent
    """
    
    def __init__(self):
        """Initialize the Root Agent"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenAI required for Root Agent")
        
        # Get filter agent instance
        self.filter_agent = get_filter_agent()
        
        # Get memory manager instance (if enabled)
        if config.MEMORY_ENABLED:
            self.memory_manager = get_memory_manager()
            utils.logger.info("💾 Memory Manager enabled (12-hour sessions)")
        else:
            self.memory_manager = None
            utils.logger.info("⚠️  Memory Manager disabled")
        
        # Create tool registry
        self.tools = self._register_tools()
        
        # Create the Gemini-powered orchestrator
        self.agent = self._create_agent()
        
        # Session state
        self.current_session_token = None
        self.execution_history = []
        
        utils.logger.info("✅ Root Agent initialized")
    
    def _register_tools(self) -> Dict:
        """Register all available tools using POLICY-COMPLIANT names"""
        # FIX: Keys now match the long names in policies.json
        return {
            "token_generator": token_generator_tool,
            "verify_clinician_credentials": verify_credentials_tool,
            "check_patient_consent_status": check_consent_tool,
            "fetch_patient_record": fetch_record_tool,
            "log_access_to_audit_trail": audit_logger_tool,
            "record_appender": record_appender_tool,
            "pdf_generator": pdf_generator_tool,
            "report_summarizer": report_summarizer_tool
        }
    
    def _create_agent(self):
        """Create the Gemini agent for orchestration"""
        
        # FIX: Updated tool names in instructions to match Policy/SOP
        instruction = f"""You are a Root Orchestrator Agent for a HIPAA-compliant medical record system.

YOUR ROLE:
You coordinate access to patient medical records by calling specialized tools in the correct sequence.

AVAILABLE TOOLS:
1. token_generator() - Generate unique session token
2. verify_clinician_credentials(clinician_id) - Verify clinician authorization
3. check_patient_consent_status(patient_id, clinician_id) - Check patient consent
4. fetch_patient_record(patient_id) - Fetch patient medical record
5. log_access_to_audit_trail(clinician_id, patient_id, action, success, token_id) - Log access
6. record_appender(patient_id, clinician_id, note) - Append to record
7. pdf_generator(patient_id, clinician_id) - Generate PDF report
8. report_summarizer(patient_id, summary_type) - Summarize record

CRITICAL HIPAA SEQUENCE (ALWAYS FOLLOW):
For accessing records:
1. Generate session token
2. Verify clinician credentials (verify_clinician_credentials)
3. Check patient consent (check_patient_consent_status)
4. Fetch patient record (fetch_patient_record)
5. Log to audit trail (log_access_to_audit_trail) - MUST include token_id

IMPORTANT RULES:
- NEVER skip credential verification
- NEVER skip consent checking
- ALWAYS log to audit trail
- Extract clinician_id and patient_id from user's natural language request
- Handle errors gracefully

OUTPUT FORMAT:
You must output ONLY a JSON array of tool calls. Do not output markdown or conversational text.
Format:
[
  {{"tool": "verify_clinician_credentials", "params": {{"clinician_id": "DR_XXXX"}}}},
  {{"tool": "check_patient_consent_status", "params": {{"patient_id": "PT_XXXX", "clinician_id": "DR_XXXX"}}}},
  ...
]
"""
        
        # Use native GenerativeModel
        agent = genai.GenerativeModel(
            model_name=config.ROOT_AGENT_MODEL,
            system_instruction=instruction,
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        
        return agent
    
    # ========================================================================
    # MAIN EXECUTION FLOW
    # ========================================================================
    
    def process_request(
        self,
        user_query: str,
        clinician_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process a user request with HIPAA compliance
        """
        try:
            utils.print_header("PROCESSING REQUEST")
            print(f"Query: {user_query}\n")
            
            # 1. Generate session token (Always first)
            token_result = token_generator_tool()
            if not token_result.get("success"):
                return self._error_response("Failed to generate session token")
            
            self.current_session_token = token_result["token"]
            print(f"🎫 Session Token: {self.current_session_token}\n")
            
            # 2. Context Recall
            if self.memory_manager and (not patient_id or not clinician_id):
                recalled = self.memory_manager.recall(self.current_session_token)
                if recalled:
                    if not patient_id and recalled.get('last_patient_id'):
                        patient_id = recalled['last_patient_id']
                        print(f"💾 Recalled from memory: Patient {patient_id}")
                    if not clinician_id and recalled.get('clinician_id'):
                        clinician_id = recalled['clinician_id']
                        print(f"💾 Recalled from memory: Clinician {clinician_id}")
            
            # 3. Agent Planning
            utils.print_subheader("PLANNING EXECUTION")
            print("Root Agent analyzing request...\n")
            
            planning_prompt = f"""
User Request: {user_query}

Context:
- Clinician ID: {clinician_id or 'Not provided - extract from query'}
- Patient ID: {patient_id or 'Not provided - extract from query'}
- Session Token: {self.current_session_token}

TASK: Plan the tool call sequence to fulfill this request following HIPAA policy.
Provide your plan as a JSON array of tool calls.
"""
            
            # Call Gemini
            response = self.agent.generate_content(planning_prompt)
            plan_text = response.text.strip()
            
            # Clean markdown if present
            if plan_text.startswith("```json"):
                plan_text = plan_text.replace("```json", "").replace("```", "").strip()
            
            try:
                planned_sequence = json.loads(plan_text)
            except json.JSONDecodeError:
                utils.logger.error(f"Invalid JSON from Root Agent: {plan_text}")
                return self._error_response("Agent failed to generate a valid plan")
            
            print(f"📋 Planned Sequence:")
            for i, step in enumerate(planned_sequence, 1):
                print(f"   {i}. {step['tool']}({', '.join(f'{k}={v}' for k, v in step.get('params', {}).items())})")
            print()
            
            # 4. Policy Validation (The Filter Agent)
            utils.print_subheader("POLICY VALIDATION")
            print("Checking compliance with HIPAA policies...\n")
            
            request_context = {
                "user_query": user_query,
                "clinician_id": clinician_id,
                "patient_id": patient_id,
                "session_token": self.current_session_token,
                **(context or {})
            }

            validation = self.filter_agent.validate_planned_execution(
                planned_sequence=planned_sequence,
                context=request_context
            )
            
            if not validation.get("valid"):
                print(f"❌ POLICY VIOLATION DETECTED")
                print(f"   Type: {validation.get('violation_type')}")
                print(f"   Severity: {validation.get('severity')}")
                print(f"   Explanation: {validation.get('explanation')}\n")
                
                # Handle retry
                if validation.get("allow_retry"):
                    return self._handle_retry(
                        original_plan=planned_sequence,
                        validation=validation,
                        context=request_context
                    )
                else:
                    return self._error_response(
                        f"Policy violation: {validation.get('explanation')}",
                        violation_info=validation
                    )
            
            print("✅ Policy validation passed\n")
            
            # 5. Execution
            utils.print_subheader("EXECUTING SEQUENCE")
            execution_results = self._execute_sequence(planned_sequence)
            
            # 6. Post-Execution Validation
            utils.print_subheader("POST-EXECUTION VALIDATION")
            post_validation = self.filter_agent.validate_execution_result(
                executed_sequence=planned_sequence,
                results=execution_results
            )
            
            if not post_validation.get("valid"):
                print(f"⚠️  Post-execution issue: {post_validation.get('explanation')}\n")
            else:
                print("✅ Post-execution validation passed\n")
            
            # 7. Memory Update
            if self.memory_manager and patient_id and clinician_id:
                self.memory_manager.remember(
                    session_id=self.current_session_token,
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    action=user_query
                )
            
            return self._format_response(
                planned_sequence=planned_sequence,
                execution_results=execution_results,
                validation=post_validation
            )
            
        except Exception as e:
            return utils.handle_error(e, "process_request")
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _execute_sequence(self, sequence: List[Dict]) -> List[Dict]:
        """Execute a sequence of tool calls with Stop-On-Failure logic"""
        results = []
        
        for i, step in enumerate(sequence, 1):
            tool_name = step.get("tool")
            params = step.get("params", {})
            
            print(f"Step {i}: {tool_name}...")
            
            tool_func = self.tools.get(tool_name)
            
            if not tool_func:
                result = {"success": False, "error": f"Tool '{tool_name}' not found"}
            else:
                try:
                    # Special handling for audit logs
                    if tool_name == "log_access_to_audit_trail" and "token_id" not in params:
                        params["token_id"] = self.current_session_token
                    
                    # Loose matching for test tokens
                    if tool_name == "log_access_to_audit_trail" and params.get("token_id") in ["SESSION_TOKEN", "TOKEN"]:
                        params["token_id"] = self.current_session_token

                    result = tool_func(**params)
                except Exception as e:
                    result = {"success": False, "error": str(e)}
            
            results.append(result)
            
            if result.get("success"):
                print(f"   ✅ Success")
                # Specialized logic: Check specific tool outcomes that define "success" differently
                if tool_name == "check_patient_consent_status" and not result.get("consent_granted", True):
                     print("   🛑 STOP: Consent denied. Aborting sequence.")
                     break
            else:
                print(f"   ❌ Failed: {result.get('error')}")
                print("   🛑 STOP: Critical step failed. Aborting sequence.")
                break
            
            print()
        
        return results
    
    def _handle_retry(self, original_plan: List[Dict], validation: Dict, context: Dict) -> Dict:
        """Handle retry after policy violation"""
        print(f"🔄 Retry is possible. Attempting auto-correction...\n")
        
        if config.FILTER_REQUIRE_USER_CONSENT:
            consent = utils.get_user_confirmation(
                f"Violation detected: {validation.get('violation_type')}. Retry with corrected sequence?"
            )
            if not consent:
                return self._error_response("User declined retry", violation_info=validation)
        
        corrected = validation.get("corrected_sequence")
        if not corrected:
             # Fallback to asking filter agent for help if it didn't provide one
             retry_info = self.filter_agent.handle_retry(
                original_request={"sequence": original_plan, "context": context},
                violation_info=validation
            )
             corrected = retry_info.get("corrected_request")

        if not corrected:
            return self._error_response("Unable to generate corrected sequence")
            
        print("✅ Executing corrected sequence...\n")
        execution_results = self._execute_sequence(corrected)
        
        return self._format_response(
            planned_sequence=corrected,
            execution_results=execution_results,
            validation={"valid": True, "retry": True}
        )

    def _format_response(self, planned_sequence, execution_results, validation):
        all_success = all(r.get("success", False) for r in execution_results)
        return {
            "success": all_success and validation.get("valid", True),
            "session_token": self.current_session_token,
            "executed_sequence": planned_sequence,
            "results": execution_results,
            "validation": validation,
            "message": "Request completed" if all_success else "Request completed with errors"
        }

    def _error_response(self, error_message, violation_info=None):
        return {
            "success": False,
            "error": error_message,
            "violation_info": violation_info,
            "session_token": self.current_session_token
        }

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_root_agent_instance = None

def get_root_agent():
    global _root_agent_instance
    if _root_agent_instance is None:
        _root_agent_instance = RootAgent()
    return _root_agent_instance

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧠 ROOT ORCHESTRATOR AGENT - TEST")
    print("="*60 + "\n")
    
    if not GEMINI_AVAILABLE:
        print("❌ Google GenAI not installed!")
        sys.exit(1)
    
    try:
        root = RootAgent()
        # Note: This test might hit 429 Rate Limit if run immediately after filter.py
        # Please wait 60 seconds if you just ran other tests!
        result = root.process_request(
            user_query="I need to access patient PT_0001's medical record",
            clinician_id="DR_0001"
        )
        
        if result.get("success"):
            print("✅ Request completed successfully")
        else:
            print(f"❌ Request failed: {result.get('error')}")
            if result.get('violation_info'):
                 print(f"   Violation: {result['violation_info'].get('explanation')}")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}\n")