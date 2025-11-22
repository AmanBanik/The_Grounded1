"""
Tools Package
Medical record access tool agents
"""

# This file makes 'tools' a Python package
# All tool agents are located in this directory

__version__ = "1.0.0"
__author__ = "HIPAA Agent System"

# Tool agents available:
# - token_generator: Generate unique session tokens
# - verify_credentials: Verify clinician authorization
# - check_consent: Check patient consent status
# - fetch_record: Fetch patient medical records
# - audit_logger: Log all access attempts
# - record_appender: Append notes to patient records
# - pdf_generator: Generate PDF reports
# - report_summarizer: AI-powered report summarization