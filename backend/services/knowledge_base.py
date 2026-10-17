"""
Knowledge Base Service for AI Health Assistant.
Loads and serves guidance and medicine information from JSON files.
WHY separate from risk_engine: guidance is display-only, not safety-critical.
"""

import json
import os

_KB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base')
_GUIDANCE = {}
_MEDICINES = {}


def _load_data():
    """Load guidance and medicine data from JSON files."""
    global _GUIDANCE, _MEDICINES
    
    try:
        with open(os.path.join(_KB_DIR, 'guidance.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
            _GUIDANCE = data.get('categories', {})
    except Exception as e:
        print(f'Warning: Could not load guidance.json: {e}')
    
    try:
        with open(os.path.join(_KB_DIR, 'medicines.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
            _MEDICINES = data.get('categories', {})
    except Exception as e:
        print(f'Warning: Could not load medicines.json: {e}')

_load_data()


def get_guidance(category):
    """
    Get home-care guidance for a symptom category.
    Returns the guidance dict or a general fallback.
    """
    category = (category or 'general').lower()
    return _GUIDANCE.get(category, _GUIDANCE.get('general', {
        'title': 'General Health Guidance',
        'home_care': ['Rest and stay hydrated', 'Monitor your symptoms', 'Get adequate sleep'],
        'watch_for': ['Symptoms getting worse', 'New symptoms appearing', 'Fever above 103°F'],
        'see_doctor_if': ['Symptoms persist beyond 3 days', 'You feel significantly worse']
    }))


def get_medicines(category):
    """
    Get OTC medicine information for a symptom category.
    Returns list of medicine dicts. NEVER returns prescription drugs.
    """
    category = (category or 'general').lower()
    cat_data = _MEDICINES.get(category, _MEDICINES.get('general', {}))
    if isinstance(cat_data, list):
        return cat_data
    return cat_data.get('medicines', [])


def get_medicines_from_db(conn, category=None):
    """Fetch medicines directly from database (Supabase/PostgreSQL/SQLite) with fallback."""
    try:
        from backend import db
        if category:
            rows = db.fetch_all(conn, "SELECT id, category, name, purpose, general_info, precautions, avoid_if, safety_note FROM medicines WHERE category = ?", (category.lower(),))
        else:
            rows = db.fetch_all(conn, "SELECT id, category, name, purpose, general_info, precautions, avoid_if, safety_note FROM medicines ORDER BY category, name")
        
        if rows:
            for r in rows:
                if isinstance(r.get('precautions'), str):
                    try:
                        r['precautions'] = json.loads(r['precautions'])
                    except Exception:
                        pass
                if isinstance(r.get('avoid_if'), str):
                    try:
                        r['avoid_if'] = json.loads(r['avoid_if'])
                    except Exception:
                        pass
            return rows
    except Exception as e:
        pass

    return get_medicines(category)



def get_specialization_for_category(category):
    """
    Suggest a doctor specialization based on symptom category.
    WHY: helps patients find the right type of doctor.
    Default is General Physician for unrecognised categories.
    """
    mapping = {
        'fever': 'General Physician',
        'cold_cough': 'General Physician',
        'headache': 'Neurologist',
        'sore_throat': 'ENT Specialist',
        'stomach': 'Gastroenterologist',
        'skin': 'Dermatologist',
        'bone_joint': 'Orthopedic',
        'heart': 'Cardiologist',
        'child': 'Pediatrician',
        'general': 'General Physician',
    }
    return mapping.get((category or '').lower(), 'General Physician')
