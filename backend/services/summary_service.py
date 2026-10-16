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

Conversation:
{conversation}

Generate a summary under 120 words."""
        
        result = call_openai(
            [{'role': 'user', 'content': prompt}],
            SUMMARY_SYSTEM_PROMPT
        )
        if result:
            return result.strip()
    
    # Demo mode / fallback: use template
    return _template_summary(structured_data, risk_result, patient_profile)


def _template_summary(structured_data, risk_result, patient_profile):
    """Generate a summary using a template (for demo mode)."""
    parts = []
    
    # Patient info
    if patient_profile:
        age = patient_profile.get('age', '?')
        gender = patient_profile.get('gender', '?')
        parts.append(f"Patient: {age}y {gender}.")
        
        conditions = patient_profile.get('chronic_conditions', '')
        if conditions and conditions.lower() not in ('none', 'nil', 'na', 'n/a', ''):
            parts.append(f"Known conditions: {conditions}.")
        
        allergies = patient_profile.get('allergies', '')
        if allergies and allergies.lower() not in ('none', 'nil', 'na', 'n/a', ''):
            parts.append(f"Allergies: {allergies}.")
    
    # Main complaint
    symptoms = structured_data.get('main_symptoms', [])
    if symptoms:
        parts.append(f"Chief complaint: {', '.join(symptoms)}.")
    
    # Duration and severity
    duration = structured_data.get('duration_days', 0)
    severity = structured_data.get('severity', 'unknown')
    parts.append(f"Duration: {duration} day(s). Severity: {severity}.")
    
    # Worsening
    if structured_data.get('worsening'):
        parts.append("Symptoms reported as worsening.")
    
    # Temperature
    temp = structured_data.get('temperature_f', 0)
    if temp > 0:
        parts.append(f"Temperature: {temp}°F.")
    
    # Other symptoms
    other = structured_data.get('other_symptoms', [])
    if other:
        parts.append(f"Associated symptoms: {', '.join(other)}.")
    
    # Risk assessment
    level = risk_result.get('level', 'unknown').upper()
    score = risk_result.get('score', 0)
    parts.append(f"Risk assessment: {level} (score: {score}).")
    
    # Red flags
    red_flags = risk_result.get('red_flags', [])
    if red_flags:
        flag_names = [rf['name'] for rf in red_flags]
        parts.append(f"RED FLAGS: {', '.join(flag_names)}.")
    
    # Reasons
    reasons = risk_result.get('reasons', [])
    if reasons:
        parts.append(f"Factors: {'; '.join(reasons[:3])}.")
    
    return ' '.join(parts)
