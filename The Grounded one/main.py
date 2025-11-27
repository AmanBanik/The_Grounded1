"""
Main CLI Interface
Entry point for HIPAA-Compliant Medical Record Access System
"""

import sys
import argparse
from pathlib import Path
import json

import config
import utils
from root import get_root_agent
from filter import get_filter_agent

# ============================================================================
# CLI INTERFACE
# ============================================================================

class HIPAACli:
    """Command-line interface for HIPAA system"""
    
    def __init__(self):
        """Initialize CLI"""
        self.root_agent = None
        self.filter_agent = None
        self.running = True
    
    def initialize(self):
        """Initialize agents"""
        try:
            utils.print_header("INITIALIZING SYSTEM")
            
            print("Loading configuration...")
            config.validate_setup()
            
            print("Initializing Filter Agent...")
            self.filter_agent = get_filter_agent()
            
            print("Initializing Root Agent...")
            self.root_agent = get_root_agent()
            
            print("\n✅ System initialized successfully!\n")
            return True
            
        except Exception as e:
            utils.print_error(f"Initialization failed: {e}")
            return False
    
    def show_welcome(self):
        """Display welcome message"""
        print(config.WELCOME_MESSAGE)
    
    def show_help(self):
        """Display help information"""
        utils.print_header("AVAILABLE COMMANDS")
        
        print("""
USER COMMANDS:
  access <patient_id> <clinician_id>  - Access patient record
  append <patient_id> <clinician_id>  - Append note to patient record
  report <patient_id> <clinician_id>  - Generate PDF report
  summarize <patient_id>              - Generate AI summary
  
  query <natural_language_query>      - Natural language request
  
SYSTEM COMMANDS:
  help      - Show this help message
  stats     - Show system statistics
  history   - Show recent access history
  clear     - Clear screen
  exit/quit - Exit the application

EXAMPLES:
  access PT_0001 DR_0001
  query "I need to check John Doe's blood pressure for Dr. Smith"
  append PT_0001 DR_0001
  report PT_0002 DR_0003
  summarize PT_0001
        """)
    
    def show_stats(self):
        """Display system statistics"""
        utils.print_header("SYSTEM STATISTICS")
        
        # Filter agent stats
        filter_stats = self.filter_agent.get_statistics()
        print("Filter Agent:")
        print(f"  • Violations Detected: {filter_stats['total_violations']}")
        print(f"  • Total Retries: {filter_stats['total_retries']}")
        print(f"  • Policies Loaded: {filter_stats['policies_loaded']}")
        
        # Audit stats (if available)
        print("\nAudit Trail:")
        try:
            from tools.audit_logger import get_access_statistics
            audit_stats = get_access_statistics()
            
            if audit_stats.get("success"):
                print(f"  • Total Accesses: {audit_stats['total_accesses']}")
                print(f"  • Successful: {audit_stats['successful_accesses']}")
                print(f"  • Failed: {audit_stats['failed_accesses']}")
                print(f"  • Success Rate: {audit_stats['success_rate']}%")
            else:
                print("  • No audit data available")
        except Exception as e:
            print(f"  • Error loading audit stats: {e}")
        
        print()
    
    def show_history(self, limit: int = 10):
        """Show recent access history"""
        utils.print_header(f"RECENT ACCESS HISTORY (Last {limit})")
        
        try:
            from tools.audit_logger import get_audit_history
            
            history = get_audit_history(limit=limit)
            
            if history.get("success") and history.get("records"):
                for record in history["records"]:
                    timestamp = utils.format_timestamp(record.get("timestamp"))
                    clinician = record.get("clinician_id")
                    patient = record.get("patient_id")
                    action = record.get("action")
                    success = "✅" if record.get("success") else "❌"
                    
                    print(f"{success} {timestamp} | {clinician} → {patient} | {action}")
                
                print(f"\nShowing {history['count']} of {history['total_count']} total records\n")
            else:
                print("No access history found.\n")
                
        except Exception as e:
            utils.print_error(f"Failed to load history: {e}")
    
    # ========================================================================
    # COMMAND HANDLERS
    # ========================================================================
    
    def handle_access(self, args: list):
        """Handle access record command"""
        if len(args) < 2:
            utils.print_error("Usage: access <patient_id> <clinician_id>")
            return
        
        patient_id = args[0]
        clinician_id = args[1]
        
        query = f"Access medical record for patient {patient_id}"
        
        # Pass explicit IDs to help the agent
        result = self.root_agent.process_request(
            user_query=query,
            patient_id=patient_id,
            clinician_id=clinician_id
        )
        
        self._display_result(result)
    
    def handle_append(self, args: list):
        """Handle append note command"""
        if len(args) < 2:
            utils.print_error("Usage: append <patient_id> <clinician_id>")
            return
        
        patient_id = args[0]
        clinician_id = args[1]
        
        # Get note content from user
        print("\nEnter note content (press Enter twice to finish):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line and lines:  # Empty line and we have content
                break
            if not line and not lines: # Empty line at start
                continue
            lines.append(line)
        
        note = "\n".join(lines).strip()
        
        if not note:
            utils.print_error("Note cannot be empty")
            return
        
        query = f"Append note to patient {patient_id}'s record: {note}"
        
        result = self.root_agent.process_request(
            user_query=query,
            patient_id=patient_id,
            clinician_id=clinician_id,
            context={"note": note, "action": "append"}
        )
        
        self._display_result(result)
    
    def handle_report(self, args: list):
        """Handle generate report command"""
        if len(args) < 2:
            utils.print_error("Usage: report <patient_id> <clinician_id>")
            return
        
        patient_id = args[0]
        clinician_id = args[1]
        
        query = f"Generate PDF report for patient {patient_id}"
        
        result = self.root_agent.process_request(
            user_query=query,
            patient_id=patient_id,
            clinician_id=clinician_id,
            context={"action": "generate_report"}
        )
        
        self._display_result(result)
    
    def handle_summarize(self, args: list):
        """Handle summarize record command"""
        if len(args) < 1:
            utils.print_error("Usage: summarize <patient_id>")
            return
        
        patient_id = args[0]
        
        # Ask for clinician ID
        clinician_id = input("Enter your clinician ID (DR_XXXX): ").strip()
        
        if not clinician_id:
            utils.print_error("Clinician ID required")
            return
        
        query = f"Generate AI summary for patient {patient_id}"
        
        result = self.root_agent.process_request(
            user_query=query,
            patient_id=patient_id,
            clinician_id=clinician_id,
            context={"action": "summarize"}
        )
        
        self._display_result(result)
    
    def handle_query(self, args: list):
        """Handle natural language query"""
        if not args:
            utils.print_error("Usage: query <natural_language_request>")
            return
        
        query = " ".join(args)
        
        print(f"\n🤖 Processing natural language query: {query}\n")
        
        result = self.root_agent.process_request(user_query=query)
        
        self._display_result(result)
    
    def _display_result(self, result: dict):
        """Display execution result and tool output"""
        print("\n" + "="*60)
        print("EXECUTION RESULT")
        print("="*60 + "\n")
        
        if result.get("success"):
            utils.print_success("Request completed successfully!")
            
            # --- DISPLAY TOOL OUTPUT ---
            # The 'data' key holds the return value from the last tool in the sequence
            tool_output = result.get("data")
            
            if tool_output and isinstance(tool_output, dict):
                # Check for specific tool output keys based on your tool definitions
                
                # 1. Report Summarizer Output
                if 'summary' in tool_output:
                    print("\n" + "-"*40)
                    print("📄 PATIENT SUMMARY")
                    print("-"*40)
                    print(tool_output['summary'].strip())
                    print("-"*40)
                    
                # 2. PDF Generator Output
                elif 'pdf_path' in tool_output:
                     print(f"\n📄 Report generated successfully: {tool_output['pdf_path']}")

                # 3. Patient Record Access Output (if it returns data)
                elif 'patient_id' in tool_output and 'full_name' in tool_output:
                     print(f"\n👤 Patient Record Accessed: {tool_output['full_name']} ({tool_output['patient_id']})")
                     # Optional: Print a snippet if you want
                     # print(json.dumps(tool_output, indent=2))
                     
                # 4. General Message Fallback
                elif 'message' in tool_output:
                     print(f"\nℹ️  Tool Output: {tool_output['message']}")

            # --- END TOOL OUTPUT DISPLAY ---

        else:
            utils.print_error(f"Request failed: {result.get('error', 'Unknown error')}")
        
        print(f"\n📋 Session Token: {result.get('session_token', 'N/A')}")
        
        # Show violation info if present
        if result.get("violation_info"):
            violation = result["violation_info"]
            utils.print_warning(f"Policy Violation: {violation.get('violation_type')}")
            print(f"  Severity: {violation.get('severity')}")
            print(f"  Explanation: {violation.get('explanation')}")
        
        # Show executed steps
        if result.get("executed_sequence"):
            print(f"\n📝 Executed Steps:")
            for i, step in enumerate(result["executed_sequence"], 1):
                print(f"  {i}. {step.get('tool', 'Unknown')}")
        
        print()
    
    # ========================================================================
    # MAIN LOOP
    # ========================================================================
    
    def run(self):
        """Main interactive loop"""
        if not self.initialize():
            return
        
        self.show_welcome()
        print('Type "help" for available commands\n')
        
        while self.running:
            try:
                # Get user input
                user_input = input("hipaa> ").strip()
                
                if not user_input:
                    continue
                
                # Parse command
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1].split() if len(parts) > 1 else []
                
                # Handle commands
                if command in ["exit", "quit"]:
                    print("\n👋 Goodbye!\n")
                    self.running = False
                
                elif command == "help":
                    self.show_help()
                
                elif command == "stats":
                    self.show_stats()
                
                elif command == "history":
                    self.show_history()
                
                elif command == "clear":
                    import os
                    os.system('clear' if os.name != 'nt' else 'cls')
                
                elif command == "access":
                    self.handle_access(args)
                
                elif command == "append":
                    self.handle_append(args)
                
                elif command == "report":
                    self.handle_report(args)
                
                elif command == "summarize":
                    self.handle_summarize(args)
                
                elif command == "query":
                    self.handle_query(args)
                
                else:
                    utils.print_error(f"Unknown command: {command}")
                    print('Type "help" for available commands\n')
            
            except KeyboardInterrupt:
                print("\n\nUse 'exit' or 'quit' to leave\n")
            
            except Exception as e:
                utils.print_error(f"Error: {e}")
                print()

# ============================================================================
# COMMAND-LINE ARGUMENTS
# ============================================================================

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="HIPAA-Compliant Medical Record Access System"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Run in interactive mode (default)"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Execute a single query and exit"
    )
    
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Generate mock data and exit"
    )
    
    return parser.parse_args()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    args = parse_args()
    
    # Handle one-off commands
    if args.generate_data:
        print("Generating mock data...")
        try:
            from generate_mock_data import generate_all_data
            generate_all_data()
        except ImportError:
            print("❌ Error: generate_mock_data.py not found")
        return
    
    if args.query:
        # Single query mode
        cli = HIPAACli()
        if cli.initialize():
            result = cli.root_agent.process_request(args.query)
            cli._display_result(result)
        return
    
    # Interactive mode
    cli = HIPAACli()
    cli.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        sys.exit(1)
