"""
Summary Service for AI Health Assistant.
Generates a concise patient summary for doctors (under 120 words).
WHY: doctors need a quick overview without reading the full chat transcript.
"""

from backend.services.ai_service import call_openai, get_ai_mode

SUMMARY_SYSTEM_PROMPT = """Generate a concise patient summary for a doctor (under 120 words).
Include: main complaint, duration, severity, key symptoms, risk level, age/gender/conditions/allergies.
Be factual and clinical. Do not include recommendations."""


def generate_summary(structured_data, risk_result, patient_profile=None, messages=None):
    """
    Generate a patient summary.
    Uses AI in openai mode, template in demo mode.
    
    Args:
        structured_data: dict of extracted symptom data
        risk_result: dict from risk_engine.assess_risk()
        patient_profile: dict with patient info
        messages: list of chat messages
    
    Returns:
        str: summary text (under 120 words)
    """
    mode = get_ai_mode()
    
    if mode == 'openai' and messages:
        conversation = '\n'.join([
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in messages
        ])
        
        prompt = f"""Patient info: {patient_profile or 'Unknown'}
Risk level: {risk_result.get('level', 'unknown')}
Risk score: {risk_result.get('score', 0)}
Risk reasons: {', '.join(risk_result.get('reasons', []))}
Red flags: {', '.join([rf['name'] for rf in risk_result.get('red_flags', [])])}

Conversation between Patient and AI Symptom Checker:
{conversation}

Generate a concise, well-structured clinical summary for the doctor. Include what the patient reported, how the dialogue progressed, symptoms duration, severity, and clinical risk."""
        
        result = call_openai(
            [{'role': 'user', 'content': prompt}],
            SUMMARY_SYSTEM_PROMPT
        )
        if result:
            return result.strip()
    
    # Demo mode / fallback: use template
    return _template_summary(structured_data, risk_result, patient_profile, messages)


def _template_summary(structured_data, risk_result, patient_profile, messages=None):
    """Generate a structured clinical summary of the patient-checker dialogue."""
    lines = []
    
    # 1. Patient Profile Header
    if patient_profile:
        age = patient_profile.get('age', '?')
        gender = patient_profile.get('gender', '?')
        pt_info = f"Patient: {age}y {gender}"
        
        conditions = patient_profile.get('chronic_conditions', '')
        if conditions and conditions.lower() not in ('none', 'nil', 'na', 'n/a', ''):
            pt_info += f" | History: {conditions}"
        
        allergies = patient_profile.get('allergies', '')
        if allergies and allergies.lower() not in ('none', 'nil', 'na', 'n/a', ''):
            pt_info += f" | Allergies: {allergies}"
        lines.append(pt_info + ".")
    
    # 2. Chief Complaint
    symptoms = structured_data.get('main_symptoms', [])
    if symptoms:
        lines.append(f"Chief Complaint: {', '.join(symptoms)}.")
    
    # 3. Patient Talk & Symptom Checker Dialogue Synthesis
    duration = structured_data.get('duration_days', 1)
    severity = (structured_data.get('severity') or 'mild').capitalize()
    worsening = "Getting worse" if structured_data.get('worsening') else "Stable / not worsening"
    temp = structured_data.get('temperature_f', 0)
    
    talk_summary = f"Symptom Checker Q&A: Duration: {duration} day(s); Severity: {severity}; Progression: {worsening}"
    if temp and float(temp) > 0:
        talk_summary += f"; Temperature: {temp}°F"
    
    other = structured_data.get('other_symptoms', [])
    if other:
        talk_summary += f"; Associated Symptoms: {', '.join(other)}"
    
    meds = structured_data.get('medicines_taken', [])
    if meds and any(m.lower() not in ('none', 'no', 'nothing') for m in meds):
        talk_summary += f"; Medications Taken: {', '.join(meds)}"
    
    lines.append(talk_summary + ".")
    
    # 4. Risk Assessment & Clinical Escalation Factors
    level = (risk_result.get('level') or 'low').upper()
    score = risk_result.get('score', 0)
    risk_line = f"Clinical Assessment: {level} Risk (Score: {score}/10)"
    
    reasons = risk_result.get('reasons', [])
    if reasons:
        risk_line += f" — Factors: {'; '.join(reasons[:3])}"
    
    lines.append(risk_line + ".")

    # Red flags
    red_flags = risk_result.get('red_flags', [])
    if red_flags:
        flag_names = [rf['name'] for rf in red_flags]
        lines.append(f"EMERGENCY RED FLAGS: {', '.join(flag_names)}.")

    # 5. Facial Health & Skincare Checkup Note
    category = (structured_data.get('category') or '').lower()
    all_symp_text = " ".join(symptoms + other).lower()
    if category in ('skin', 'facial_care') or any(k in all_symp_text for k in ('face', 'facial', 'skin', 'acne', 'pimple', 'dark spots', 'serum', 'pores', 'pigmentation', 'dullness')):
        lines.append("Facial & Skin Checkup Note: Evaluated for nutritional deficiencies (Vitamin D, B12, Zinc, Iron) and skin barrier integrity. Active topical serums and diagnostic checkup tests indicated.")

    return ' '.join(lines)
