"""
Report Summarizer Tool
Summarizes medical reports using Gemini API
THIS IS THE ONLY TOOL THAT USES THE GEMINI API
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
import config
import utils

# Gemini API imports
from google.generativeai.types import HarmCategory, HarmBlockThreshold # API filter blocks
try:
    from google.genai import types
    import google.generativeai as genai
    
    # Configure Gemini API
    genai.configure(api_key=config.GOOGLE_API_KEY)
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google GenAI not installed. Install with: pip install google-generativeai")

# ============================================================================
# REPORT SUMMARIZATION
# ============================================================================

def summarize_patient_report(
    patient_id: str,
    summary_type: str = "comprehensive",
    max_length: str = "medium"
) -> Dict:
    """
    Generate AI-powered summary of patient medical record
    
    Args:
        patient_id: Patient ID
        summary_type: Type of summary (comprehensive, vitals_only, history_only, recent_notes)
        max_length: Length of summary (short, medium, long)
        
    Returns:
        Dictionary with summary result
    """
    try:
        if not GEMINI_AVAILABLE:
            return {
                "success": False,
                "error": "Google GenAI library not installed. Run: pip install google-generativeai"
            }
        
        # Validate patient ID
        if not utils.validate_patient_id(patient_id):
            return {
                "success": False,
                "error": "Invalid patient ID format"
            }
        
        # Fetch patient data
        patient = utils.get_patient_by_id(patient_id)
        if not patient:
            return {
                "success": False,
                "error": f"Patient {patient_id} not found"
            }
        
        # Prepare data based on summary type
        if summary_type == "vitals_only":
            data_to_summarize = {
                "patient_name": patient.get("full_name"),
                "vitals": patient.get("vitals", {})
            }
            prompt_focus = "Focus on analyzing the vital signs and provide clinical insights."
        
        elif summary_type == "history_only":
            data_to_summarize = {
                "patient_name": patient.get("full_name"),
                "medical_history": patient.get("medical_history", {})
            }
            prompt_focus = "Focus on medical history, conditions, medications, and allergies."
        
        elif summary_type == "recent_notes":
            notes = patient.get("notes", [])
            recent_notes = notes[-5:] if len(notes) > 5 else notes
            data_to_summarize = {
                "patient_name": patient.get("full_name"),
                "recent_notes": recent_notes
            }
            prompt_focus = "Focus on summarizing recent clinical notes and treatment progression."
        
        else:  # comprehensive
            data_to_summarize = {
                "patient_name": patient.get("full_name"),
                "age": patient.get("date_of_birth"),
                "gender": patient.get("gender"),
                "blood_type": patient.get("blood_type"),
                "vitals": patient.get("vitals", {}),
                "medical_history": patient.get("medical_history", {}),
                "recent_notes": patient.get("notes", [])[-3:]
            }
            prompt_focus = "Provide a comprehensive overview of the patient's health status."
        
        # Set length parameters
        length_params = {
            "short": {"words": "100-150", "bullets": "3-5"},
            "medium": {"words": "200-300", "bullets": "5-7"},
            "long": {"words": "400-500", "bullets": "8-10"}
        }
        length_spec = length_params.get(max_length, length_params["medium"])
        
        # Construct prompt
        prompt = f"""You are a medical AI assistant helping to summarize patient records for healthcare professionals.

Patient Data:
{data_to_summarize}

Task: {prompt_focus}

Requirements:
1. Create a {max_length}-length summary ({length_spec['words']} words)
2. Use bullet points ({length_spec['bullets']} key points)
3. Highlight any concerning findings or trends
4. Use medical terminology appropriately
5. Be objective and factual
6. DO NOT make diagnoses or treatment recommendations
7. Note any missing or incomplete information

Format your response as:
**Summary:**
[Brief overview paragraph]

**Key Findings:**
• [Bullet point 1]
• [Bullet point 2]
• [etc.]

**Clinical Notes:**
[Any important observations or concerns]
"""

        # Create Gemini model
        model = genai.GenerativeModel(
            model_name=config.TOOL_AGENT_MODEL,
            generation_config={
                "temperature": 0.3,  # Lower temperature for factual summaries
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1000,
            }
        )
        
        # Define safety settings to prevent blocking on medical content
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Generate summary with safety settings
        # response = model.generate_content(
        #     prompt,
        #     request_options={"retry": config.get_retry_config()}
        # )
        
        response = model.generate_content(
            prompt,
            safety_settings=safety_settings
        )
        
        # Extract summary text with error handling for blocked responses
        try:
            summary_text = response.text
        except ValueError as e:
            # Handle cases where the model blocked the response
            error_msg = f"AI summarization blocked by safety filters. Block reason: {response.prompt_feedback.block_reason}"
            utils.logger.warning(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
            
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patient.get("full_name"),
            "summary_type": summary_type,
            "length": max_length,
            "summary": summary_text,
            "model_used": config.TOOL_AGENT_MODEL,
            "message": f"Summary generated for {patient.get('full_name')}"
        }
    
    except Exception as e:
        return utils.handle_error(e, "summarize_patient_report")

# ============================================================================
# SPECIALIZED SUMMARIZATION FUNCTIONS
# ============================================================================

def summarize_for_handoff(patient_id: str) -> Dict:
    """
    Generate handoff summary for shift changes
    Quick summary focusing on current status and action items
    """
    return summarize_patient_report(
        patient_id=patient_id,
        summary_type="comprehensive",
        max_length="short"
    )

def summarize_for_consultation(patient_id: str) -> Dict:
    """
    Generate detailed summary for specialist consultation
    Comprehensive summary with full context
    """
    return summarize_patient_report(
        patient_id=patient_id,
        summary_type="comprehensive",
        max_length="long"
    )

def summarize_recent_visits(patient_id: str) -> Dict:
    """
    Summarize recent clinical notes and treatment progression
    """
    return summarize_patient_report(
        patient_id=patient_id,
        summary_type="recent_notes",
        max_length="medium"
    )

# ============================================================================
# ADK TOOL WRAPPER
# ============================================================================

def report_summarizer_tool(
    patient_id: str,
    summary_type: str = "comprehensive",
    max_length: str = "medium"
) -> Dict:
    """
    ADK-compatible tool wrapper for report summarization
    
    Args:
        patient_id: Patient ID
        summary_type: Type of summary
        max_length: Length of summary
        
    Returns:
        Summarization result dictionary
    """
    return summarize_patient_report(patient_id, summary_type, max_length)

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 REPORT SUMMARIZER TOOL - TEST")
    print("="*60 + "\n")
    
    if not GEMINI_AVAILABLE:
        print("❌ Google GenAI not installed!")
        print("   Install with: pip install google-generativeai")
        print("\n" + "="*60 + "\n")
        sys.exit(1)
    
    # Test 1: Comprehensive summary (medium length)
    print("Test 1: Comprehensive summary (medium)")
    print("-" * 60)
    result = report_summarizer_tool(
        patient_id="PT_0001",
        summary_type="comprehensive",
        max_length="medium"
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
        print(f"   Summary Type: {result.get('summary_type')}")
        print(f"   Length: {result.get('length')}")
        print(f"   Model: {result.get('model_used')}")
        print(f"\n{result.get('summary')}\n")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 2: Vitals only summary
    print("\n" + "-" * 60)
    print("\nTest 2: Vitals-only summary (short)")
    print("-" * 60)
    result = report_summarizer_tool(
        patient_id="PT_0001",
        summary_type="vitals_only",
        max_length="short"
    )
    
    if result.get("success"):
        print(f"✅ Summary generated")
        print(f"\n{result.get('summary')}\n")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 3: Handoff summary
    print("\n" + "-" * 60)
    print("\nTest 3: Handoff summary (quick overview)")
    print("-" * 60)
    result = summarize_for_handoff("PT_0001")
    
    if result.get("success"):
        print(f"✅ Handoff summary generated")
        print(f"\n{result.get('summary')}\n")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 4: Recent notes summary
    print("\n" + "-" * 60)
    print("\nTest 4: Recent notes summary")
    print("-" * 60)
    result = summarize_recent_visits("PT_0001")
    
    if result.get("success"):
        print(f"✅ Recent notes summarized")
        print(f"\n{result.get('summary')}\n")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Test 5: Invalid patient
    print("\n" + "-" * 60)
    print("\nTest 5: Attempt with invalid patient")
    print("-" * 60)
    result = report_summarizer_tool("PT_9999")
    
    if not result.get("success"):
        print(f"❌ {result.get('error')} (Expected)")
    
    print("\n" + "="*60)
    print("✅ Report Summarizer Test Complete")
    print("="*60 + "\n")
