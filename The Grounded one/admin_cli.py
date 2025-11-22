
"""
Admin CLI Interface
Administrative tools for policy management and system maintenance
"""

import sys
import json
# import getpass  <-- Removed to prevent VS Code freezing
from pathlib import Path
from datetime import datetime

import config
import utils
from filter import get_filter_agent

# ============================================================================
# AUTHENTICATION
# ============================================================================

def authenticate():
    """Simple password authentication for admin access"""
    print("\n" + "="*60)
    print("ADMIN AUTHENTICATION REQUIRED")
    print("="*60 + "\n")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        # FIX: Using input() instead of getpass() to prevent terminal freezing
        password = input("Enter admin password: ").strip()
        
        if password == config.ADMIN_PASSWORD:
            print("\n✅ Authentication successful!\n")
            return True
        else:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                utils.print_error(f"Incorrect password. {remaining} attempts remaining.")
            else:
                utils.print_error("Authentication failed. Access denied.")
    
    return False

# ============================================================================
# ADMIN CLI CLASS
# ============================================================================

class AdminCLI:
    """Administrative command-line interface"""
    
    def __init__(self):
        """Initialize admin CLI"""
        self.running = True
        self.filter_agent = None
    
    def initialize(self):
        """Initialize admin tools"""
        try:
            print("Initializing admin tools...")
            # This is where the next error might happen (Importing the agent)
            self.filter_agent = get_filter_agent()
            print("✅ Admin tools initialized\n")
            return True
        except Exception as e:
            utils.print_error(f"Initialization failed: {e}")
            # If agent fails, we still want to keep CLI open for log viewing/data reset
            print("⚠️  Continuing with limited functionality (Agent features disabled)\n")
            return False
    
    def show_welcome(self):
        """Display admin welcome message"""
        print(config.ADMIN_WELCOME)
    
    def show_help(self):
        """Display admin help"""
        utils.print_header("ADMIN COMMANDS")
        
        print("""
POLICY MANAGEMENT:
  view-policies          - View current policy files
  edit-sop               - Edit HIPAA SOP file
  edit-policies          - Edit policies.json
  reload-policies        - Reload policies into Filter Agent
  backup-policies        - Backup current policies
  
AUDIT & LOGS:
  view-audit [limit]     - View audit trail (default: 20 records)
  view-violations        - View policy violations log
  export-audit <file>    - Export audit trail to file
  clear-logs             - Clear all log files (with confirmation)
  
DATA MANAGEMENT:
  regenerate-data        - Regenerate mock data
  view-clinicians        - List all clinicians
  view-patients          - List all patients
  view-consents          - List consent records
  
SYSTEM:
  stats                  - System statistics
  health-check           - Run system health check
  reset-counters         - Reset violation/retry counters
  
GENERAL:
  help                   - Show this help message
  clear                  - Clear screen
  exit/quit              - Exit admin mode
        """)
    
    # ========================================================================
    # POLICY MANAGEMENT
    # ========================================================================
    
    def view_policies(self):
        """View current policies"""
        utils.print_header("CURRENT POLICIES")
        
        # View SOP
        print("\n📋 HIPAA SOP (hipaa_SOP.txt):")
        print("-" * 60)
        if config.HIPAA_SOP_FILE.exists():
            with open(config.HIPAA_SOP_FILE, 'r') as f:
                content = f.read()
            print(content[:500] + "..." if len(content) > 500 else content)
            print(f"\n(Total length: {len(content)} characters)")
        else:
            print("⚠️  File not found")
        
        # View JSON policies
        print("\n📋 Structured Policies (policies.json):")
        print("-" * 60)
        if config.POLICIES_JSON.exists():
            policies = utils.load_json_file(config.POLICIES_JSON)
            print(json.dumps(policies, indent=2)[:500] + "...")
            print(f"\n(Total keys: {len(policies)})")
        else:
            print("⚠️  File not found")
        
        print()
    
    def edit_sop(self):
        """Edit HIPAA SOP file"""
        utils.print_header("EDIT HIPAA SOP")
        
        print("⚠️  This will open the SOP file in your default text editor.")
        print(f"File location: {config.HIPAA_SOP_FILE}\n")
        
        if not utils.get_yes_no_input("Continue?", default=False):
            print("Cancelled.\n")
            return
        
        # Backup first
        self._backup_file(config.HIPAA_SOP_FILE, "sop")
        
        # Open in editor
        import os
        try:
            if sys.platform.startswith('darwin'):  # macOS
                os.system(f'open -e "{config.HIPAA_SOP_FILE}"')
            elif sys.platform.startswith('linux'):  # Linux
                os.system(f'xdg-open "{config.HIPAA_SOP_FILE}"')
            elif sys.platform.startswith('win'):  # Windows
                os.system(f'notepad "{config.HIPAA_SOP_FILE}"')
            else:
                print(f"Please manually edit: {config.HIPAA_SOP_FILE}")
            
            print("\n✅ File opened for editing")
            print("⚠️  Remember to reload policies after editing!\n")
        except Exception as e:
            utils.print_error(f"Could not open editor: {e}")
    
    def edit_policies_json(self):
        """Edit policies.json"""
        utils.print_header("EDIT POLICIES.JSON")
        
        print("⚠️  This will open the policies file in your default text editor.")
        print(f"File location: {config.POLICIES_JSON}\n")
        
        if not utils.get_yes_no_input("Continue?", default=False):
            print("Cancelled.\n")
            return
        
        # Backup first
        self._backup_file(config.POLICIES_JSON, "policies")
        
        # Open in editor
        import os
        try:
            if sys.platform.startswith('darwin'):
                os.system(f'open -e "{config.POLICIES_JSON}"')
            elif sys.platform.startswith('linux'):
                os.system(f'xdg-open "{config.POLICIES_JSON}"')
            elif sys.platform.startswith('win'):
                os.system(f'notepad "{config.POLICIES_JSON}"')
            else:
                print(f"Please manually edit: {config.POLICIES_JSON}")
            
            print("\n✅ File opened for editing")
            print("⚠️  Remember to reload policies after editing!\n")
        except Exception as e:
            utils.print_error(f"Could not open editor: {e}")
    
    def reload_policies(self):
        """Reload policies into Filter Agent"""
        utils.print_header("RELOAD POLICIES")
        
        if not self.filter_agent:
            utils.print_error("Filter Agent not initialized. Cannot reload.")
            return

        print("This will reload policy files into the Filter Agent.")
        print("Any changes you made will take effect immediately.\n")
        
        if not utils.get_yes_no_input("Continue?", default=True):
            print("Cancelled.\n")
            return
        
        success = self.filter_agent.reload_policies()
        
        if success:
            utils.print_success("Policies reloaded successfully!")
        else:
            utils.print_error("Failed to reload policies. Check error logs.")
        print()
    
    def backup_policies(self):
        """Backup current policies"""
        utils.print_header("BACKUP POLICIES")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup SOP
        sop_backup = self._backup_file(config.HIPAA_SOP_FILE, f"sop_{timestamp}")
        
        # Backup JSON
        json_backup = self._backup_file(config.POLICIES_JSON, f"policies_{timestamp}")
        
        if sop_backup and json_backup:
            utils.print_success("Policies backed up successfully!")
            print(f"Backups created in: {config.POLICIES_DIR}\n")
        else:
            utils.print_error("Backup failed")
    
    def _backup_file(self, filepath: Path, backup_name: str) -> bool:
        """Create backup of a file"""
        try:
            if not filepath.exists():
                return False
            
            backup_path = filepath.parent / f"{backup_name}_backup{filepath.suffix}"
            
            with open(filepath, 'r') as src:
                content = src.read()
            
            with open(backup_path, 'w') as dst:
                dst.write(content)
            
            return True
        except Exception as e:
            utils.logger.error(f"Backup failed: {e}")
            return False
    
    # ========================================================================
    # AUDIT & LOGS
    # ========================================================================
    
    def view_audit(self, limit: int = 20):
        """View audit trail"""
        utils.print_header(f"AUDIT TRAIL (Last {limit} records)")
        
        try:
            from tools.audit_logger import get_audit_history
            
            history = get_audit_history(limit=limit)
            
            if history.get("success") and history.get("records"):
                for i, record in enumerate(history["records"], 1):
                    timestamp = utils.format_timestamp(record.get("timestamp"))
                    clinician = record.get("clinician_id")
                    patient = record.get("patient_id")
                    action = record.get("action")
                    success = "✅" if record.get("success") else "❌"
                    
                    print(f"{i:2}. {success} {timestamp}")
                    print(f"    {clinician} → {patient} | {action}")
                    
                    if record.get("details"):
                        print(f"    Details: {record['details']}")
                    print()
                
                print(f"Showing {history['count']} of {history['total_count']} total records\n")
            else:
                print("No audit records found.\n")
        
        except Exception as e:
            utils.print_error(f"Failed to load audit: {e}")
    
    def view_violations(self):
        """View violations log"""
        utils.print_header("POLICY VIOLATIONS LOG")
        
        if not config.VIOLATIONS_LOG.exists():
            print("No violations logged.\n")
            return
        
        try:
            with open(config.VIOLATIONS_LOG, 'r') as f:
                content = f.read()
            
            if content.strip():
                print(content)
            else:
                print("No violations logged.\n")
        
        except Exception as e:
            utils.print_error(f"Failed to read violations log: {e}")
    
    def export_audit(self, filename: str):
        """Export audit trail to file"""
        utils.print_header("EXPORT AUDIT TRAIL")
        
        try:
            audit_data = utils.load_json_file(config.AUDIT_LOG)
            
            export_path = config.DATA_DIR / filename
            
            with open(export_path, 'w') as f:
                json.dump(audit_data, f, indent=2)
            
            utils.print_success(f"Audit trail exported to: {export_path}")
            print(f"Total records: {len(audit_data)}\n")
        
        except Exception as e:
            utils.print_error(f"Export failed: {e}")
    
    def clear_logs(self):
        """Clear all log files"""
        utils.print_header("CLEAR LOGS")
        
        utils.print_warning("⚠️  WARNING: This will permanently delete all logs!")
        print("This includes:")
        print("  • Audit trail")
        print("  • Violations log")
        print("  • Error log\n")
        
        if not utils.get_yes_no_input("Are you sure?", default=False):
            print("Cancelled.\n")
            return
        
        # Backup first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Backup audit log
            if config.AUDIT_LOG.exists():
                backup_path = config.LOGS_DIR / f"audit_backup_{timestamp}.json"
                audit_data = utils.load_json_file(config.AUDIT_LOG)
                with open(backup_path, 'w') as f:
                    json.dump(audit_data, f, indent=2)
            
            # Clear logs
            with open(config.AUDIT_LOG, 'w') as f:
                json.dump([], f)
            
            with open(config.VIOLATIONS_LOG, 'w') as f:
                f.write("")
            
            with open(config.ERROR_LOG, 'w') as f:
                f.write("")
            
            utils.print_success("Logs cleared successfully!")
            print(f"Backup created: audit_backup_{timestamp}.json\n")
        
        except Exception as e:
            utils.print_error(f"Failed to clear logs: {e}")
    
    # ========================================================================
    # DATA MANAGEMENT
    # ========================================================================
    
    def regenerate_data(self):
        """Regenerate mock data"""
        utils.print_header("REGENERATE MOCK DATA")
        
        utils.print_warning("⚠️  This will overwrite existing data!")
        
        if not utils.get_yes_no_input("Continue?", default=False):
            print("Cancelled.\n")
            return
        
        try:
            from generate_mock_data import generate_all_data
            generate_all_data()
            utils.print_success("Mock data regenerated successfully!\n")
        except Exception as e:
            utils.print_error(f"Failed to regenerate data: {e}")
    
    def view_clinicians(self):
        """List all clinicians"""
        utils.print_header("CLINICIANS")
        
        clinicians = utils.load_json_file(config.CLINICIANS_DB)
        
        for clinician in clinicians:
            print(f"• {clinician['clinician_id']} - {clinician['full_name']}")
            print(f"  {clinician['specialization']} | {clinician['department']}")
            print(f"  Active: {clinician['active']}\n")
    
    def view_patients(self):
        """List all patients"""
        utils.print_header("PATIENTS")
        
        patients = utils.load_json_file(config.PATIENTS_DB)
        
        for patient in patients[:10]:  # Show first 10
            print(f"• {patient['patient_id']} - {patient['full_name']}")
            print(f"  DOB: {patient['date_of_birth']} | Blood Type: {patient['blood_type']}\n")
        
        print(f"(Showing 10 of {len(patients)} total patients)\n")
    
    def view_consents(self):
        """List consent records"""
        utils.print_header("CONSENT RECORDS")
        
        consents = utils.load_json_file(config.CONSENT_DB)
        
        for consent in consents[:10]:  # Show first 10
            status_icon = "✅" if consent['status'] == "active" else "❌"
            print(f"{status_icon} {consent['consent_id']}")
            print(f"   {consent['patient_id']} ↔ {consent['clinician_id']}")
            print(f"   Status: {consent['status']} | Scope: {consent['scope']}\n")
        
        print(f"(Showing 10 of {len(consents)} total records)\n")
    
    # ========================================================================
    # SYSTEM
    # ========================================================================
    
    def show_stats(self):
        """Show system statistics"""
        utils.print_header("SYSTEM STATISTICS")
        
        # Filter agent stats
        if self.filter_agent:
            filter_stats = self.filter_agent.get_statistics()
            print("Filter Agent:")
            print(f"  • Violations Detected: {filter_stats['total_violations']}")
            print(f"  • Retries Attempted: {filter_stats['total_retries']}")
            print(f"  • Policies Loaded: {filter_stats['policies_loaded']}")
        else:
            print("Filter Agent: Not Initialized")
        
        # Data stats
        print("\nData:")
        clinicians = utils.load_json_file(config.CLINICIANS_DB)
        patients = utils.load_json_file(config.PATIENTS_DB)
        consents = utils.load_json_file(config.CONSENT_DB)
        print(f"  • Clinicians: {len(clinicians)}")
        print(f"  • Patients: {len(patients)}")
        print(f"  • Consent Records: {len(consents)}")
        
        # Audit stats
        print("\nAudit Trail:")
        try:
            from tools.audit_logger import get_access_statistics
            audit_stats = get_access_statistics()
            
            if audit_stats.get("success"):
                print(f"  • Total Accesses: {audit_stats['total_accesses']}")
                print(f"  • Success Rate: {audit_stats['success_rate']}%")
            else:
                print("  • No data available")
        except:
            print("  • Unable to load")
        
        print()
    
    def health_check(self):
        """Run system health check"""
        utils.print_header("SYSTEM HEALTH CHECK")
        
        checks = []
        
        # Check data files
        checks.append(("Clinicians DB", config.CLINICIANS_DB.exists()))
        checks.append(("Patients DB", config.PATIENTS_DB.exists()))
        checks.append(("Consent DB", config.CONSENT_DB.exists()))
        
        # Check policy files
        checks.append(("HIPAA SOP", config.HIPAA_SOP_FILE.exists()))
        checks.append(("Policies JSON", config.POLICIES_JSON.exists()))
        
        # Check log files
        checks.append(("Audit Log", config.AUDIT_LOG.exists()))
        checks.append(("Violations Log", config.VIOLATIONS_LOG.exists()))
        
        # Display results
        for name, status in checks:
            icon = "✅" if status else "❌"
            print(f"{icon} {name}")
        
        all_ok = all(status for _, status in checks)
        
        print()
        if all_ok:
            utils.print_success("All systems operational!")
        else:
            utils.print_warning("Some issues detected")
        print()
    
    def reset_counters(self):
        """Reset filter agent counters"""
        utils.print_header("RESET COUNTERS")
        
        if self.filter_agent:
            self.filter_agent.reset_counters()
            utils.print_success("Filter agent counters reset!\n")
        else:
            utils.print_error("Filter agent not initialized.\n")
    
    # ========================================================================
    # MAIN LOOP
    # ========================================================================
    
    def run(self):
        """Main admin loop"""
        # Try to initialize, but continue even if it fails partially
        self.initialize()
        
        self.show_welcome()
        print('Type "help" for available commands\n')
        
        while self.running:
            try:
                user_input = input("admin> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Handle commands
                if command in ["exit", "quit"]:
                    print("\n👋 Exiting admin mode\n")
                    self.running = False
                
                elif command == "help":
                    self.show_help()
                
                elif command == "clear":
                    import os
                    os.system('clear' if os.name != 'nt' else 'cls')
                
                elif command == "view-policies":
                    self.view_policies()
                
                elif command == "edit-sop":
                    self.edit_sop()
                
                elif command == "edit-policies":
                    self.edit_policies_json()
                
                elif command == "reload-policies":
                    self.reload_policies()
                
                elif command == "backup-policies":
                    self.backup_policies()
                
                elif command == "view-audit":
                    limit = int(args[0]) if args else 20
                    self.view_audit(limit)
                
                elif command == "view-violations":
                    self.view_violations()
                
                elif command == "export-audit":
                    filename = args[0] if args else "audit_export.json"
                    self.export_audit(filename)
                
                elif command == "clear-logs":
                    self.clear_logs()
                
                elif command == "regenerate-data":
                    self.regenerate_data()
                
                elif command == "view-clinicians":
                    self.view_clinicians()
                
                elif command == "view-patients":
                    self.view_patients()
                
                elif command == "view-consents":
                    self.view_consents()
                
                elif command == "stats":
                    self.show_stats()
                
                elif command == "health-check":
                    self.health_check()
                
                elif command == "reset-counters":
                    self.reset_counters()
                
                else:
                    utils.print_error(f"Unknown command: {command}")
                    print('Type "help" for available commands\n')
            
            except KeyboardInterrupt:
                print("\n\nUse 'exit' or 'quit' to leave\n")
            
            except Exception as e:
                utils.print_error(f"Error: {e}")
                print()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for admin CLI"""
    
    # Authenticate
    if not authenticate():
        sys.exit(1)
    
    # Run admin CLI
    admin = AdminCLI()
    admin.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        sys.exit(1)

