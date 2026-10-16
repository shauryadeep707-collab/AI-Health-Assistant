"""
Unit tests for the Risk Engine.
Verifies all 12+ scenarios:
1. Every red-flag emergency category
2. Hindi / Hinglish emergency phrases
3. Score threshold progression (Low, Medium, Urgent)
4. AI cannot downgrade deterministic rule levels
5. Edge cases: empty text, whitespace, case insensitivity, etc.
"""

import pytest
from backend.services.risk_engine import (
    check_red_flags,
    calculate_risk_score,
    determine_risk_level,
    assess_risk
)

# --- Red Flags & Emergency Tests ---

def test_chest_pain_english():
    flags = check_red_flags("I am experiencing severe chest pain and pressure.")
    assert len(flags) > 0
    assert any(f['id'] == 'chest_pain' for f in flags)

def test_chest_pain_hindi_hinglish():
    # Hinglish red flag test (Section 17 D)
    flags = check_red_flags("mujhe bahut tej seene mein dard ho raha hai")
    assert len(flags) > 0
    assert any(f['id'] == 'chest_pain' for f in flags)

def test_breathing_difficulty_english():
    flags = check_red_flags("I have trouble breathing and feeling breathless.")
    assert len(flags) > 0
    assert any(f['id'] == 'breathing_difficulty' for f in flags)

def test_breathing_difficulty_hindi():
    flags = check_red_flags("saans lene mein takleef ho rahi hai aur dum ghut raha hai")
    assert len(flags) > 0
    assert any(f['id'] == 'breathing_difficulty' for f in flags)

def test_unconsciousness_fainting():
    flags = check_red_flags("The patient passed out and was unconscious.")
    assert len(flags) > 0
    assert any(f['id'] == 'unconscious' for f in flags)

def test_seizure_daura():
    flags = check_red_flags("patient ko mirgi ka daura pada hai")
    assert len(flags) > 0
    assert any(f['id'] == 'seizure' for f in flags)

def test_stroke_signs_lakwa():
    flags = check_red_flags("face drooping and slurred speech observed")
    assert len(flags) > 0
    assert any(f['id'] == 'stroke_signs' for f in flags)

def test_severe_bleeding():
    flags = check_red_flags("deep cut and won't stop bleeding")
    assert len(flags) > 0
    assert any(f['id'] == 'severe_bleeding' for f in flags)

def test_vomiting_blood_khoon_ki_ulti():
    flags = check_red_flags("patient ko khoon ki ulti hui")
    assert len(flags) > 0
    assert any(f['id'] == 'vomiting_blood' for f in flags)

def test_allergic_reaction_anaphylaxis():
    flags = check_red_flags("severe allergic reaction with throat swelling")
    assert len(flags) > 0
    assert any(f['id'] == 'allergic_reaction' for f in flags)

def test_suicidal_crisis():
    flags = check_red_flags("I am having suicidal thoughts and want to end my life")
    assert len(flags) > 0
    assert any(f['id'] == 'suicidal' for f in flags)

def test_high_fever_with_confusion():
    flags = check_red_flags("fever with stiff neck and delirium")
    assert len(flags) > 0
    assert any(f['id'] == 'high_fever_severe' for f in flags)

def test_infant_fever():
    flags = check_red_flags("my 2 month old newborn baby fever is burning up")
    assert len(flags) > 0
    assert any(f['id'] == 'infant_fever' for f in flags)

def test_pregnancy_bleeding():
    flags = check_red_flags("bleeding in pregnancy since this morning")
    assert len(flags) > 0
    assert any(f['id'] == 'pregnancy_bleeding' for f in flags)

# --- Score Calculation & Thresholds ---

def test_score_mild_case():
    # Mild symptoms, 1 day, no worsening -> Score 0 -> Low
    data = {'duration_days': 1, 'severity': 'mild', 'worsening': False, 'temperature_f': 98.6}
    score, reasons = calculate_risk_score(data)
    assert score == 0
    assert determine_risk_level(score) == 'low'

def test_score_medium_threshold():
    # Duration > 3 days (+1), moderate (+1), worsening (+2) -> Score 4 -> Medium (3-5)
    data = {'duration_days': 4, 'severity': 'moderate', 'worsening': True, 'temperature_f': 99.5}
    score, reasons = calculate_risk_score(data)
    assert score == 4
    assert determine_risk_level(score) == 'medium'

def test_score_urgent_threshold():
    # Duration > 7 days (+2), severe (+2), worsening (+2), temp 103.5 (+3) -> Score 9 -> Urgent (>=6)
    data = {'duration_days': 8, 'severity': 'severe', 'worsening': True, 'temperature_f': 103.5}
    score, reasons = calculate_risk_score(data)
    assert score >= 6
    assert determine_risk_level(score) == 'urgent'

def test_profile_risk_factors():
    # Age < 5 (+1) and chronic condition (+1)
    data = {'duration_days': 2, 'severity': 'mild'}
    profile = {'age': 3, 'chronic_conditions': 'Asthma'}
    score, reasons = calculate_risk_score(data, profile)
    assert score == 2  # age_risk(1) + chronic(1)

# --- Safe Escalation Rule: AI Cannot Downgrade ---

def test_ai_cannot_downgrade_urgent():
    # Deterministic rules score Urgent (score >= 6)
    # AI says 'low' -> Result MUST remain 'urgent'
    data = {'duration_days': 8, 'severity': 'severe', 'worsening': True, 'temperature_f': 104}
    res = assess_risk("regular cough text", data, ai_risk_level='low')
    assert res['level'] == 'urgent'

def test_ai_cannot_downgrade_red_flag():
    # Red flag exists -> AI says 'low' -> Result MUST remain 'urgent'
    data = {'duration_days': 1, 'severity': 'mild'}
    res = assess_risk("I have chest pain and pressure", data, ai_risk_level='low')
    assert res['level'] == 'urgent'
    assert len(res['red_flags']) > 0

def test_ai_can_escalate():
    # Rules say 'low' (score 1)
    # AI says 'medium' -> Result escalates to 'medium'
    data = {'duration_days': 1, 'severity': 'mild'}
    res = assess_risk("mild cold", data, ai_risk_level='medium')
    assert res['level'] == 'medium'
    assert res['method'] == 'ai_escalated'

# --- Edge Cases ---

def test_empty_and_whitespace_input():
    assert check_red_flags("") == []
    assert check_red_flags("   ") == []
    assert check_red_flags(None) == []

def test_mixed_case_red_flag():
    flags = check_red_flags("ChEsT pAiN aNd ShOrTnEsS oF bReAtH")
    assert len(flags) >= 1
