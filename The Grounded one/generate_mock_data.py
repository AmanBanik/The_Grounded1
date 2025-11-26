"""
Mock Data Generator for HIPAA-Compliant Agent System
Generates realistic simulated medical data for testing
ALL DATA IS FICTIONAL - No real patient information
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import config

# Set random seed for reproducibility
random.seed(config.RANDOM_SEED)

# ============================================================================
# REALISTIC MOCK DATA POOLS
# ============================================================================

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", 
    "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher",
    "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret",
    "Mark", "Sandra", "Donald", "Ashley", "Steven", "Kimberly", "Paul",
    "Emily", "Andrew", "Donna", "Joshua", "Michelle", "Kenneth", "Carol",
    "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa", "Edward"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
]

SPECIALIZATIONS = [
    "Cardiology", "Neurology", "Pediatrics", "Orthopedics", "Dermatology",
    "Psychiatry", "General Practice", "Emergency Medicine", "Radiology",
    "Anesthesiology", "Oncology", "Internal Medicine"
]

DEPARTMENTS = [
    "Emergency", "ICU", "Cardiology", "Neurology", "Pediatrics", "Surgery",
    "Radiology", "Laboratory", "Pharmacy", "Outpatient", "General Ward"
]

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

MEDICAL_CONDITIONS = [
    "Hypertension", "Type 2 Diabetes", "Asthma", "Arthritis", "Migraine",
    "Allergic Rhinitis", "GERD", "Hypothyroidism", "Anxiety Disorder",
    "Chronic Back Pain", "High Cholesterol", "Osteoporosis"
]

MEDICATIONS = [
    "Lisinopril", "Metformin", "Amlodipine", "Atorvastatin", "Omeprazole",
    "Levothyroxine", "Albuterol", "Metoprolol", "Losartan", "Gabapentin",
    "Sertraline", "Ibuprofen", "Acetaminophen", "Aspirin"
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_id(prefix, number):
    """Generate formatted ID with prefix"""
    return f"{prefix}_{number:04d}"

def random_date(start_days_ago, end_days_ago):
    """Generate random date within range"""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")

def random_phone():
    """Generate random phone number"""
    return f"+1-{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}"

# ============================================================================
# CLINICIAN DATA GENERATION
# ============================================================================

def generate_clinicians(num_clinicians):
    """Generate mock clinician credentials"""
    clinicians = []
    
    for i in range(num_clinicians):
        clinician_id = generate_id("DR", i + 1)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        clinician = {
            "clinician_id": clinician_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"Dr. {first_name} {last_name}",
            "specialization": random.choice(SPECIALIZATIONS),
            "department": random.choice(DEPARTMENTS),
            "license_number": f"MD{random.randint(100000, 999999)}",
            "email": f"{first_name.lower()}.{last_name.lower()}@hospital.com",
            "phone": random_phone(),
            "hire_date": random_date(3650, 365),  # Hired 1-10 years ago
            "active": True,
            "clearance_level": random.choice([2, 3, 4]),  # 2=Basic, 3=Standard, 4=Full
        }
        clinicians.append(clinician)
    
    return clinicians

# ============================================================================
# PATIENT DATA GENERATION
# ============================================================================

def generate_patients(num_patients):
    """Generate mock patient records"""
    patients = []
    
    for i in range(num_patients):
        patient_id = generate_id("PT", i + 1)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Generate medical history
        num_conditions = random.randint(0, 3)
        conditions = random.sample(MEDICAL_CONDITIONS, num_conditions) if num_conditions > 0 else []
        
        num_medications = random.randint(0, 4)
        medications = random.sample(MEDICATIONS, num_medications) if num_medications > 0 else []
        
        # Generate vital signs
        vitals = {
            "blood_pressure": f"{random.randint(90, 140)}/{random.randint(60, 90)}",
            "heart_rate": random.randint(60, 100),
            "temperature": round(random.uniform(97.0, 99.5), 1),
            "weight_kg": round(random.uniform(50, 120), 1),
            "height_cm": random.randint(150, 195)
        }
        
        patient = {
            "patient_id": patient_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "date_of_birth": random_date(29200, 6570),  # Age 18-80
            "gender": random.choice(["Male", "Female", "Other"]),
            "blood_type": random.choice(BLOOD_TYPES),
            "email": f"{first_name.lower()}.{last_name.lower()}@email.com",
            "phone": random_phone(),
            "address": {
                "street": f"{random.randint(1, 9999)} {random.choice(LAST_NAMES)} Street",
                "city": random.choice(["Springfield", "Riverside", "Fairview", "Madison", "Georgetown"]),
                "state": random.choice(["CA", "NY", "TX", "FL", "IL", "PA", "OH"]),
                "zip": f"{random.randint(10000, 99999)}"
            },
            "emergency_contact": {
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "relationship": random.choice(["Spouse", "Parent", "Sibling", "Child"]),
                "phone": random_phone()
            },
            "insurance": {
                "provider": random.choice(["BlueCross", "Aetna", "UnitedHealth", "Cigna", "Humana"]),
                "policy_number": f"INS{random.randint(100000000, 999999999)}",
                "group_number": f"GRP{random.randint(10000, 99999)}"
            },
            "medical_history": {
                "conditions": conditions,
                "medications": medications,
                "allergies": random.sample(["Penicillin", "Peanuts", "Latex", "Shellfish", "None"], 
                                        random.randint(0, 2))
            },
            "vitals": vitals,
            "last_visit": random_date(365, 0),  # Within last year
            "notes": [
                {
                    "date": random_date(180, 90),
                    "clinician": generate_id("DR", random.randint(1, 10)),
                    "note": f"Routine checkup. Patient reports feeling well. {random.choice(['Blood work ordered.', 'Follow-up in 6 months.', 'Medication adjusted.'])}"
                }
            ]
        }
        patients.append(patient)
    
    return patients

# ============================================================================
# CONSENT DATA GENERATION
# ============================================================================

def generate_consent_records(num_records, num_patients, num_clinicians):
    """Generate mock consent records"""
    consent_records = []
    
    # --- ADDED: 3 Guaranteed Negative Test Cases ---

    # Negative Test 1: Revoked Consent
    # (PT_0001 and DR_0002 will have a 'revoked' record)
    consent_records.append({
        "consent_id": "CNS_NEG_REVOKED",
        "patient_id": "PT_0001",
        "clinician_id": "DR_0002",
        "status": "revoked",
        "granted_date": random_date(730, 60),
        "expiry_date": random_date(30, 1),
        "scope": "full_access",
        "purpose": "Ongoing treatment"
    })

    # Negative Test 2: Expired Consent
    # (PT_0002 and DR_0003 will have an 'expired' record)
    consent_records.append({
        "consent_id": "CNS_NEG_EXPIRED",
        "patient_id": "PT_0002",
        "clinician_id": "DR_0003",
        "status": "expired",
        "granted_date": random_date(730, 400),
        "expiry_date": random_date(365, 30), # Expired between 1 month and 1 year ago
        "scope": "emergency_only",
        "purpose": "Emergency care"
    })

    # Negative Test 3: Future-Dated Consent (Not yet valid)
    # (PT_0003 and DR_0004 will have an 'active' record that starts in the future)
    future_start = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    future_end = (datetime.now() + timedelta(days=375)).strftime("%Y-%m-%d")
    consent_records.append({
        "consent_id": "CNS_NEG_FUTURE",
        "patient_id": "PT_0003",
        "clinician_id": "DR_0004",
        "status": "active", # Status is active, but dates are invalid for today
        "granted_date": future_start, 
        "expiry_date": future_end,
        "scope": "consultation_only",
        "purpose": "Consultation"
    })
    # --- END ADDED TEST CASES ---

    for i in range(num_records):
        patient_id = generate_id("PT", random.randint(1, num_patients))
        clinician_id = generate_id("DR", random.randint(1, num_clinicians))
        
        # 90% of consents are active, 10% expired/revoked
        status = random.choices(
            ["active", "expired", "revoked"],
            weights=[90, 7, 3]
        )[0]
        
        consent = {
            "consent_id": generate_id("CNS", i + 1),
            "patient_id": patient_id,
            "clinician_id": clinician_id,
            "status": status,
            "granted_date": random_date(730, 0),  # Within last 2 years
            "expiry_date": random_date(-30, -365) if status == "active" else random_date(30, 0),
            "scope": random.choice([
                "full_access",
                "emergency_only",
                "limited_access",
                "consultation_only"
            ]),
            "purpose": random.choice([
                "Ongoing treatment",
                "Consultation",
                "Emergency care",
                "Surgical procedure",
                "Diagnostic testing"
            ])
        }
        consent_records.append(consent)
    
    return consent_records

# ============================================================================
# MAIN DATA GENERATION
# ============================================================================

def generate_all_data():
    """Generate all mock data and save to files"""
    print("\n" + "="*60)
    print("🏥 GENERATING MOCK MEDICAL DATA")
    print("="*60 + "\n")
    
    # Generate clinicians
    print(f"👨‍⚕️  Generating {config.NUM_MOCK_CLINICIANS} clinicians...")
    clinicians = generate_clinicians(config.NUM_MOCK_CLINICIANS)
    
    # Generate patients
    print(f"🏥 Generating {config.NUM_MOCK_PATIENTS} patients...")
    patients = generate_patients(config.NUM_MOCK_PATIENTS)
    
    # Generate consent records
    print(f"✅ Generating {config.NUM_MOCK_CONSENT_RECORDS} consent records...")
    consents = generate_consent_records(
        config.NUM_MOCK_CONSENT_RECORDS,
        config.NUM_MOCK_PATIENTS,
        config.NUM_MOCK_CLINICIANS
    )
    
    # Save to files
    print("\n💾 Saving data to files...\n")
    
    with open(config.CLINICIANS_DB, 'w') as f:
        json.dump(clinicians, f, indent=2)
    print(f"   ✅ Saved: {config.CLINICIANS_DB}")
    
    with open(config.PATIENTS_DB, 'w') as f:
        json.dump(patients, f, indent=2)
    print(f"   ✅ Saved: {config.PATIENTS_DB}")
    
    with open(config.CONSENT_DB, 'w') as f:
        json.dump(consents, f, indent=2)
    print(f"   ✅ Saved: {config.CONSENT_DB}")
    
    # Initialize empty log files
    with open(config.AUDIT_LOG, 'w') as f:
        json.dump([], f)
    print(f"   ✅ Initialized: {config.AUDIT_LOG}")
    
    with open(config.VIOLATIONS_LOG, 'w') as f:
        f.write("")
    print(f"   ✅ Initialized: {config.VIOLATIONS_LOG}")
    
    with open(config.ERROR_LOG, 'w') as f:
        f.write("")
    print(f"   ✅ Initialized: {config.ERROR_LOG}")
    
    # Print summary
    print("\n" + "="*60)
    print("✅ DATA GENERATION COMPLETE!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   • {len(clinicians)} clinicians created")
    print(f"   • {len(patients)} patients created")
    print(f"   • {len(consents)} consent records created")
    print(f"\n📁 Data saved to: {config.DATA_DIR}")
    print(f"📁 Logs initialized in: {config.LOGS_DIR}\n")
    
    # Print sample data
    print("="*60)
    print("📋 SAMPLE DATA")
    print("="*60 + "\n")
    
    print("Sample Clinician:")
    print(json.dumps(clinicians[0], indent=2))
    
    print("\n" + "-"*60 + "\n")
    
    print("Sample Patient:")
    print(json.dumps(patients[0], indent=2))
    
    print("\n" + "-"*60 + "\n")
    
    print("Sample Consent:")
    print(json.dumps(consents[0], indent=2))
    
    print("\n" + "="*60 + "\n")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        generate_all_data()
        print("✅ Mock data generation successful!\n")
    except Exception as e:
        print(f"\n❌ Error generating mock data: {e}\n")
        raise
