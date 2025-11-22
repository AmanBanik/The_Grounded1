# HIPAA Agent System – Technical Architecture White Paper

```
  _____ _                 _      
 / ____| |               | |     
| |    | | __ _ _   _  __| | ___
| |    | |/ _` | | | |/ _` |/ _ \
| |____| | (_| | |_| | (_| |  __/
 \_____|_|\__,_|\__,_|\__,_|\___|
                                   
        AI-Powered Documentation
```

---

## ⚠️ Documentation Metadata
**Original Draft:** Claude AI (Anthropic)  
**Refactoring & Updates:** Gemini (Google), Native Architecture version  
**Project:** HIPAA‑Compliant Medical Record Access System  
**Version:** 2.0 (Native Implementation)

---

## Table of Contents
1. System Overview  
2. File Dependency Map  
3. Configuration Distribution  
4. Data Generation & Storage  
5. Core Agent Logic  
6. Memory System Architecture  
7. Critical Safety Features  
8. API Key & Credentials Flow  
9. Critical Functions Reference  
10. Troubleshooting Guide

---

## 1. System Overview
### 1.1 Architecture Layers
The system uses a **Native Implementation** approach, avoiding heavy agent frameworks. This provides speed, full control, and predictable execution.

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Configuration (config.py)                      │
│ - API keys, paths, constants                            │
│ - Distributed to ALL components                         │
└──────────────────────────┬──────────────────────────────┘
                           │ imports config
┌──────────────────────────┴──────────────────────────────┐
│ Layer 2: Utilities & Helpers                            │
│ - utils.py (shared functions & logging)                 │
│ - memory_manager.py (SQLite session memory)             │
└──────────────────────────┬──────────────────────────────┘
                           │ imports utils, memory
┌──────────────────────────┴──────────────────────────────┐
│ Layer 3: Tool Agents (tools/*.py)                       │
│ - 8 deterministic tools                                 │
│ - 1 AI tool (Report Summarizer)                         │
└──────────────────────────┬──────────────────────────────┘
                           │ uses tools
┌──────────────────────────┴──────────────────────────────┐
│ Layer 4: Core Agents                                    │
│ - filter.py (Policy Engine – Gemini 2.5 Pro)            │
│ - root.py (Orchestrator – Gemini 2.0 Flash)             │
└──────────────────────────┬──────────────────────────────┘
                           │ coordinates
┌──────────────────────────┴──────────────────────────────┐
│ Layer 5: User Interfaces                                │
│ - main.py (User CLI)                                    │
│ - admin_cli.py (Admin Interface)                        │
└─────────────────────────────────────────────────────────┘
```

---

## 2. File Dependency Map
### 2.1 Full Import Tree
```
config.py (root)
    ↓
    ├─ utils.py
    │      ↓
    │      ├─ token_generator.py
    │      ├─ verify_credentials.py
    │      ├─ check_consent.py
    │      ├─ audit_logger.py
    │      ├─ fetch_record.py
    │      ├─ record_appender.py
    │      ├─ pdf_generator.py
    │      └─ report_summarizer.py (uses google.generativeai)
    │
    ├─ memory_manager.py
    │      ↓
    │      (uses utils + sqlite3)
    │
    ├─ filter.py (uses utils + generative AI)
    │
    ├─ root.py (imports filter, memory, tools, generative AI)
    │
    ├─ main.py (imports root, filter, utils)
    │
    └─ admin_cli.py (imports filter, utils)
```

### 2.2 Essential Libraries
| Library | Purpose | Used By |
|--------|----------|----------|
| google-generativeai | LLM inference | root, filter, summarizer |
| reportlab | PDF generation | pdf_generator.py |
| pillow | Image handling | pdf_generator.py |
| sqlite3 | Local DB | memory_manager.py |

---

## 3. Configuration Distribution
### 3.1 API Keys
`config.py` exposes a single key:
```python
GOOGLE_API_KEY = "your_api_key_here"
```
Imported across all AI-enabled modules.

### 3.2 Model Selection
```python
ROOT_AGENT_MODEL   = "gemini-2.0-flash"
FILTER_AGENT_MODEL = "gemini-2.5-pro"
TOOL_AGENT_MODEL   = "gemini-2.5-flash"
```

| Component | Needs | Model |
|----------|--------|--------|
| Filter Agent | Deep reasoning | 2.5 Pro |
| Root Agent | Low‑latency planning | 2.0 Flash |
| Summarizer | High context | 2.5 Flash |

---

## 4. Data Generation & Storage
### 4.1 Synthetic Data
Generated via:
```
python generate_mock_data.py
```
Output:
```
data/
├── clinicians.json
├── patients.json
└── consent_records.json
```

### 4.2 Logging
```
logs/
├── audit_trail.json
├── violations.log
└── errors.log
```

Audit logs are immutable.

---

## 5. Core Agent Logic
### 5.1 Root Agent (Orchestrator)
Steps:
1. Read query.
2. Send question + tool definitions to Gemini 2.0 Flash.
3. Receive JSON plan.
4. Forward plan to Filter Agent.
5. Execute validated steps.

### 5.2 Filter Agent (Policy Engine)
Steps:
1. Receive plan.
2. Load `hipaa_SOP.txt`.
3. Validate using Gemini 2.5 Pro.
4. Approve, correct, or block.

---

## 6. Memory System Architecture
### 6.1 SQLite Database
`memory_manager.py` manages a persistent memory system.

Schema:
```
CREATE TABLE session_memory (
    session_id TEXT PRIMARY KEY,
    clinician_id TEXT,
    last_patient_id TEXT,
    conversation_history TEXT,
    expires_at TIMESTAMP
);
```

Flow:
- **Recall:** Load past session data
- **Act:** Execute tools
- **Remember:** Save updated context

---

## 7. Critical Safety Features
### 7.1 Negative Test Capability
Execution stops automatically if consent is missing.

Example (root.py):
```
if tool == "check_patient_consent_status" and not result["consent_granted"]:
    print("STOP: Consent denied.")
    break
```

### 7.2 Self‑Correction
Filter Agent rewrites unsafe plans before execution.

---

## 8. API Key & Credentials Flow
Single source of truth:
```
config.py → filter.py, root.py, summarizer.py → genai.configure()
```

All AI integrations inherit the same key.

---

## 9. Critical Functions Reference
### 9.1 Data Functions (utils)
- load_json_file()
- save_json_file()
- append_to_json_array()
- get_patient_by_id()
- get_clinician_by_id()
- get_consent_record()

### 9.2 Logging Functions
- log_to_audit_trail()
- log_violation()
- logger.error()
- log_access_to_audit_trail() (tool)

### 9.3 Memory Functions
- remember()
- recall()
- forget()
- cleanup_expired_sessions()

### 9.4 Validation Functions (filter)
- validate_planned_execution()
- validate_execution_result()
- generate_corrected_sequence()
- handle_retry()

---

## 10. Troubleshooting Guide
### 10.1 API Key Issues
Check `config.py` and run:
```
python -c "import config; print(config.GOOGLE_API_KEY)"
```

### 10.2 Import Errors
Ensure you're in project root and run:
```
python -c "from tools.token_generator import token_generator_tool; print('OK')"
```

### 10.3 Database Locked
Delete `memory.db` and restart.

### 10.4 Missing Data
Run:
```
python generate_mock_data.py
```

---

End of White Paper.

