"""
Memory Manager (patched)
- Stores expires_at as ISO8601 text
- Uses a threading.Lock to serialize DB access (safe for check_same_thread=False)
- Removes emoji characters from logs (ASCII-only messages)
- Avoids relying on sqlite3 default datetime adapters (no deprecation warnings)
"""

import sqlite3
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
import config
import utils

# ============================================================================
# MEMORY MANAGER CLASS
# ============================================================================

class MemoryManager:
    """
    Manages session memory with 12-hour auto-expiry
    Stores conversation context for natural language interactions
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize memory manager

        Args:
            db_path: Path to SQLite database (default: config.MEMORY_DB_PATH)
        """
        self.db_path = db_path or config.MEMORY_DB_PATH

        # Create database connection
        # Allow cross-thread usage but serialize access with a lock
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Thread-safety lock for DB operations
        self._db_lock = threading.Lock()

        # Create tables if they don't exist
        self._create_tables()

        # Clean up expired sessions on initialization
        self.cleanup_expired_sessions()

        utils.logger.info("Memory Manager initialized (DB: %s)", self.db_path)

    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self._db_lock:
            cursor = self.conn.cursor()

            # Main session memory table - store expires_at as TEXT (ISO8601)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_memory (
                    session_id TEXT PRIMARY KEY,
                    clinician_id TEXT,
                    last_patient_id TEXT,
                    last_action TEXT,
                    conversation_history TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT NOT NULL
                )
            """)

            # Index for fast expiry lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires 
                ON session_memory(expires_at)
            """)

            self.conn.commit()

        utils.logger.info("Memory tables created/verified")

    # ========================================================================
    # CORE MEMORY OPERATIONS
    # ========================================================================

    def remember(
        self,
        session_id: str,
        patient_id: Optional[str] = None,
        clinician_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> bool:
        """
        Store context in session memory
        """
        try:
            with self._db_lock:
                cursor = self.conn.cursor()

                # Calculate expiry (UTC ISO string)
                expires_at = (datetime.utcnow() + timedelta(hours=config.MEMORY_DURATION_HOURS)).isoformat()

                # Check if session already exists
                cursor.execute(
                    "SELECT conversation_history FROM session_memory WHERE session_id = ?",
                    (session_id,)
                )
                existing = cursor.fetchone()

                if existing:
                    # Update existing session
                    conversation_history = json.loads(existing['conversation_history'] or '[]')

                    # Add new action to history
                    if action:
                        conversation_history.append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'action': action,
                            'patient_id': patient_id,
                            'clinician_id': clinician_id
                        })

                        # Keep only last N actions
                        if len(conversation_history) > config.MAX_CONVERSATION_HISTORY:
                            conversation_history = conversation_history[-config.MAX_CONVERSATION_HISTORY:]

                    cursor.execute("""
                        UPDATE session_memory 
                        SET clinician_id = COALESCE(?, clinician_id),
                            last_patient_id = COALESCE(?, last_patient_id),
                            last_action = COALESCE(?, last_action),
                            conversation_history = ?,
                            expires_at = ?
                        WHERE session_id = ?
                    """, (
                        clinician_id,
                        patient_id,
                        action,
                        json.dumps(conversation_history),
                        expires_at,
                        session_id
                    ))
                else:
                    # Create new session
                    conversation_history = []
                    if action:
                        conversation_history.append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'action': action,
                            'patient_id': patient_id,
                            'clinician_id': clinician_id
                        })

                    cursor.execute("""
                        INSERT INTO session_memory 
                        (session_id, clinician_id, last_patient_id, last_action, 
                         conversation_history, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        clinician_id,
                        patient_id,
                        action,
                        json.dumps(conversation_history),
                        expires_at
                    ))

                self.conn.commit()

            utils.logger.info("Memory stored for session %s", session_id)
            return True

        except Exception as e:
            utils.logger.error("Failed to store memory: %s", e)
            return False

    def recall(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve context from session memory
        """
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                now_iso = datetime.utcnow().isoformat()

                cursor.execute("""
                    SELECT * FROM session_memory 
                    WHERE session_id = ? AND expires_at > ?
                """, (session_id, now_iso))

                row = cursor.fetchone()

            if not row:
                return None

            # Convert to dictionary
            memory = {
                'session_id': row['session_id'],
                'clinician_id': row['clinician_id'],
                'last_patient_id': row['last_patient_id'],
                'last_action': row['last_action'],
                'conversation_history': json.loads(row['conversation_history'] or '[]'),
                'created_at': row['created_at'],
                'expires_at': row['expires_at']
            }

            utils.logger.info("Memory recalled for session %s", session_id)
            return memory

        except Exception as e:
            utils.logger.error("Failed to recall memory: %s", e)
            return None

    def forget(self, session_id: str) -> bool:
        """
        Clear memory for a specific session
        """
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM session_memory WHERE session_id = ?", (session_id,))
                self.conn.commit()

            utils.logger.info("Session %s forgotten", session_id)
            return True

        except Exception as e:
            utils.logger.error("Failed to forget session: %s", e)
            return False

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def is_expired(self, session_id: str) -> bool:
        """Check if a session has expired"""
        memory = self.recall(session_id)
        return memory is None

    def get_last_patient(self, session_id: str) -> Optional[str]:
        """Get last accessed patient ID from session"""
        memory = self.recall(session_id)
        return memory['last_patient_id'] if memory else None

    def get_last_clinician(self, session_id: str) -> Optional[str]:
        """Get last clinician ID from session"""
        memory = self.recall(session_id)
        return memory['clinician_id'] if memory else None

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session"""
        memory = self.recall(session_id)
        return memory['conversation_history'] if memory else []

    # ========================================================================
    # MAINTENANCE
    # ========================================================================

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from database
        """
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                now_iso = datetime.utcnow().isoformat()

                cursor.execute("""
                    DELETE FROM session_memory 
                    WHERE expires_at < ?
                """, (now_iso,))

                deleted_count = cursor.rowcount
                self.conn.commit()

            if deleted_count > 0:
                utils.logger.info("Cleaned up %d expired sessions", deleted_count)

            return deleted_count

        except Exception as e:
            utils.logger.error("Failed to cleanup expired sessions: %s", e)
            return 0

    def get_active_sessions_count(self) -> int:
        """Get count of active (non-expired) sessions"""
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                now_iso = datetime.utcnow().isoformat()
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM session_memory 
                    WHERE expires_at > ?
                """, (now_iso,))

                row = cursor.fetchone()
            return row['count']

        except Exception as e:
            utils.logger.error("Failed to count sessions: %s", e)
            return 0

    def get_all_active_sessions(self) -> List[Dict]:
        """Get all active sessions (for admin view)"""
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                now_iso = datetime.utcnow().isoformat()
                cursor.execute("""
                    SELECT * FROM session_memory 
                    WHERE expires_at > ?
                    ORDER BY created_at DESC
                """, (now_iso,))

                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        'session_id': row['session_id'],
                        'clinician_id': row['clinician_id'],
                        'last_patient_id': row['last_patient_id'],
                        'created_at': row['created_at'],
                        'expires_at': row['expires_at'],
                        'actions_count': len(json.loads(row['conversation_history'] or '[]'))
                    })

            return sessions

        except Exception as e:
            utils.logger.error("Failed to get active sessions: %s", e)
            return []

    def clear_all_memory(self) -> bool:
        """
        Clear ALL memory (for admin use)
        WARNING: This deletes all session data!
        """
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM session_memory")
                self.conn.commit()

            utils.logger.warning("ALL memory cleared by admin")
            return True

        except Exception as e:
            utils.logger.error("Failed to clear all memory: %s", e)
            return False

    def get_statistics(self) -> Dict:
        """Get memory statistics"""
        try:
            with self._db_lock:
                cursor = self.conn.cursor()

                # Total sessions
                cursor.execute("SELECT COUNT(*) as count FROM session_memory")
                total = cursor.fetchone()['count']

                # Active sessions
                now_iso = datetime.utcnow().isoformat()
                cursor.execute("""
                    SELECT COUNT(*) as count FROM session_memory 
                    WHERE expires_at > ?
                """, (now_iso,))
                active = cursor.fetchone()['count']

            expired = total - active

            return {
                'total_sessions': total,
                'active_sessions': active,
                'expired_sessions': expired,
                'database_path': str(self.db_path),
                'memory_duration_hours': config.MEMORY_DURATION_HOURS
            }

        except Exception as e:
            utils.logger.error("Failed to get statistics: %s", e)
            return {}

    # ========================================================================
    # CONTEXT MANAGER SUPPORT
    # ========================================================================

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close database connection"""
        self.close()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            utils.logger.info("Memory Manager closed")

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_memory_manager_instance = None

def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager instance"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MEMORY MANAGER - TEST")
    print("="*60 + "\n")

    try:
        # Initialize memory manager
        print("Initializing Memory Manager...")
        memory = MemoryManager()
        print("Memory Manager initialized\n")

        # Test 1: Store memory
        print("Test 1: Store session memory")
        print("-" * 60)
        session_id = "TEST_SESSION_001"
        success = memory.remember(
            session_id=session_id,
            patient_id="PT_0001",
            clinician_id="DR_0001",
            action="Access patient record"
        )
        print(f"[OK]" if success else "[FAIL]", "Memory stored\n")

        # Test 2: Recall memory
        print("Test 2: Recall session memory")
        print("-" * 60)
        recalled = memory.recall(session_id)
        if recalled:
            print("[OK] Memory recalled:")
            print(f"   Patient: {recalled['last_patient_id']}")
            print(f"   Clinician: {recalled['clinician_id']}")
            print(f"   Last Action: {recalled['last_action']}")
            print(f"   Expires: {recalled['expires_at']}")
        else:
            print("[FAIL] Failed to recall memory")
        print()

        # Test 3: Update memory
        print("Test 3: Update session with new action")
        print("-" * 60)
        memory.remember(
            session_id=session_id,
            patient_id="PT_0002",
            action="Generate report"
        )
        print("[OK] Memory updated\n")

        # Test 4: Get conversation history
        print("Test 4: Get conversation history")
        print("-" * 60)
        history = memory.get_conversation_history(session_id)
        print(f"[OK] History has {len(history)} actions:")
        for i, action in enumerate(history, 1):
            print(f"   {i}. {action['action']} (Patient: {action['patient_id']})")
        print()

        # Test 5: Statistics
        print("Test 5: Memory statistics")
        print("-" * 60)
        stats = memory.get_statistics()
        print(f"[OK] Total Sessions: {stats.get('total_sessions')}")
        print(f"[OK] Active Sessions: {stats.get('active_sessions')}")
        print(f"[OK] Expired Sessions: {stats.get('expired_sessions')}")
        print(f"[OK] Memory Duration: {stats.get('memory_duration_hours')} hours")
        print()

        # Test 6: Cleanup
        print("Test 6: Cleanup expired sessions")
        print("-" * 60)
        cleaned = memory.cleanup_expired_sessions()
        print(f"[OK] Cleaned up {cleaned} expired sessions\n")

        # Test 7: Forget session
        print("Test 7: Forget session")
        print("-" * 60)
        memory.forget(session_id)
        print("[OK] Session forgotten\n")

        # Close
        memory.close()

        print("="*60)
        print("[OK] Memory Manager Test Complete")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[FAIL] Error during testing: {e}\n")
        raise
