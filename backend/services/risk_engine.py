"""
Risk Assessment Engine for AI Health Assistant.
Determines risk level using a combination of:
1. Hard red-flag keyword matching (instant URGENT)
2. Score-based rules (thresholds from config)
3. AI opinion (can escalate but NEVER downgrade)

WHY deterministic rules + AI: the rules are a safety net. If a red flag
is detected, the result is URGENT regardless of what the AI says.
This makes the system safe even when the AI makes mistakes.
"""

import json
import os
import re
from backend.config import config

# --- Load red flags from knowledge base on module import ---
_RED_FLAGS = []
_KB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base')

def _load_red_flags():
    """Load red flag rules from JSON file. Called once at import time."""
    global _RED_FLAGS
    path = os.path.join(_KB_DIR, 'red_flags.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _RED_FLAGS = data.get('red_flags', [])
    except Exception as e:
        print(f'Warning: Could not load red_flags.json: {e}')
        _RED_FLAGS = []

_load_red_flags()


def check_red_flags(text):
    """
    Check raw symptom text against ALL red flag rules.
    Returns a list of matched red flags (each a dict with id, name, action).
    
    WHY check raw text: red flags must be caught BEFORE the AI processes
    anything. A patient typing 'chest pain' should see the Urgent screen
    immediately, without waiting for follow-up questions.
    
    Uses both keyword matching (fast, exact) and regex patterns (flexible).
    Case-insensitive for all checks.
    """
    if not text:
        return []
    
    text_lower = text.lower().strip()
    matched = []  # list of matched red flags
    
    for flag in _RED_FLAGS:
        is_matched = False
        
        # Check keywords (exact substring match)
        for keyword in flag.get('keywords', []):
            if keyword.lower() in text_lower:
                is_matched = True
                break
        
        # Check regex patterns if keywords didn't match
        if not is_matched:
            for pattern in flag.get('patterns', []):
                try:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        is_matched = True
                        break
                except re.error:
                    continue  # skip invalid regex
        
        if is_matched:
            matched.append({
                'id': flag['id'],
                'name': flag['name'],
                'action': flag['action'],
                'category': flag.get('category', 'unknown')
            })
    
    return matched


def calculate_risk_score(structured_data, patient_profile=None):
    """
    Calculate a numeric risk score from structured symptom data.
    
    Args:
        structured_data: dict with keys like duration_days, severity,
                        worsening, temperature_f, etc.
        patient_profile: dict with age, chronic_conditions, etc.
    
    Returns:
        tuple: (score, reasons) where reasons is a list of strings
               explaining each point added.
    
    Score thresholds (from config):
        0-2: Low risk
        3-5: Medium risk
        6+:  Urgent
    """
    score = 0
    reasons = []  # human-readable explanation for each point
    weights = config.RISK_WEIGHTS
    
    # --- Duration scoring ---
    duration = structured_data.get('duration_days', 0)
    try:
        duration = int(duration)
    except (ValueError, TypeError):
        duration = 0
    
    if duration > 7:
        score += weights['duration_7d']
        reasons.append(f'Symptoms lasting {duration} days (>7 days: +{weights["duration_7d"]})')
    elif duration > 3:
        score += weights['duration_3d']
        reasons.append(f'Symptoms lasting {duration} days (>3 days: +{weights["duration_3d"]})')
    
    # --- Severity scoring ---
    severity = (structured_data.get('severity', '') or '').lower()
    if severity == 'severe':
        score += weights['severity_severe']
        reasons.append(f'Severe symptoms (+{weights["severity_severe"]})')
    elif severity == 'moderate':
        score += weights['severity_moderate']
        reasons.append(f'Moderate symptoms (+{weights["severity_moderate"]})')
    
    # --- Worsening ---
    worsening = structured_data.get('worsening', False)
    if worsening is True or str(worsening).lower() in ('true', 'yes', '1'):
        score += weights['worsening']
        reasons.append(f'Symptoms are getting worse (+{weights["worsening"]})')
    
    # --- Temperature ---
    temp = structured_data.get('temperature_f', 0)
    try:
        temp = float(temp)
    except (ValueError, TypeError):
        temp = 0
    
    if temp >= 103:
        score += weights['temp_103']
        reasons.append(f'High fever: {temp}°F (≥103°F: +{weights["temp_103"]})')
    elif temp >= 101:
        score += weights['temp_101']
        reasons.append(f'Fever: {temp}°F (≥101°F: +{weights["temp_101"]})')
    
    # --- Associated / Multiple Symptoms Acuity ---
    other_symptoms = structured_data.get('other_symptoms', [])
    if isinstance(other_symptoms, list) and len(other_symptoms) >= 2:
        score += 1
        reasons.append(f'Multiple concurrent symptoms ({len(other_symptoms)} reported: +1)')

    # --- Age risk (from patient profile) ---
    if patient_profile:
        age = patient_profile.get('age', 0)
        try:
            age = int(age)
        except (ValueError, TypeError):
            age = 0
        
        if age > 0 and (age < 5 or age > 60):
            score += weights['age_risk']
            reasons.append(f'Age {age} is in a higher-risk group (+{weights["age_risk"]})')
        
        # Chronic conditions
        conditions = patient_profile.get('chronic_conditions', '') or ''
        if conditions and conditions.lower() not in ('none', 'nil', 'na', 'n/a', ''):
            score += weights['chronic']
            reasons.append(f'Has chronic conditions: {conditions} (+{weights["chronic"]})')
    
    return score, reasons


def determine_risk_level(score):
    """Convert a numeric score to a risk level string."""
    if score >= config.RISK_MEDIUM_MAX + 1:  # >= 6
        return 'urgent'
    elif score >= config.RISK_LOW_MAX + 1:   # >= 3
        return 'medium'
    return 'low'


def assess_risk(text, structured_data, patient_profile=None, ai_risk_level=None):
    """
    Full risk assessment combining all three methods.
    
    Args:
        text: raw symptom text from the patient
        structured_data: dict of extracted structured information
        patient_profile: dict with patient's profile (age, conditions)
        ai_risk_level: the AI's suggested risk level ('low'|'medium'|'urgent')
    
    Returns:
        dict: {
            level: 'low'|'medium'|'urgent',
            score: int,
            reasons: [str],
            red_flags: [dict],
            method: str  # which method determined the final level
        }
    
    Priority: red flags > max(rule score, AI opinion)
    The AI can ESCALATE but NEVER downgrade the risk level.
    """
    result = {
        'level': 'low',
        'score': 0,
        'reasons': [],
        'red_flags': [],
        'method': 'rules'
    }
    
    # Step 1: Check red flags FIRST (instant URGENT)
    red_flags = check_red_flags(text)
    if red_flags:
        result['level'] = 'urgent'
        result['red_flags'] = red_flags
        result['reasons'] = [f'Red flag detected: {rf["name"]}' for rf in red_flags]
        result['method'] = 'red_flags'
        result['score'] = 99  # Max score for red flags
        return result
    
    # Step 2: Calculate score from structured data
    score, reasons = calculate_risk_score(structured_data, patient_profile)
    rule_level = determine_risk_level(score)
    
    result['score'] = score
    result['reasons'] = reasons
    result['level'] = rule_level
    result['method'] = 'rules'
    
    # Step 3: Compare with AI opinion (AI can only ESCALATE)
    if ai_risk_level:
        level_order = {'low': 0, 'medium': 1, 'urgent': 2}
        ai_order = level_order.get(ai_risk_level.lower(), 0)
        rule_order = level_order.get(rule_level, 0)
        
        if ai_order > rule_order:
            result['level'] = ai_risk_level.lower()
            result['reasons'].append(f'AI assessment elevated risk to {ai_risk_level}')
            result['method'] = 'ai_escalated'
            if ai_order == 1 and result['score'] < 3:
                result['score'] = 3
            elif ai_order == 2 and result['score'] < 6:
                result['score'] = 6
    
    return result
