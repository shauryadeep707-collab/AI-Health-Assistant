"""
Assessment Routes for AI Health Assistant.
Handles the symptom check workflow: create assessment, send messages,
get AI follow-ups, and complete with risk assessment.
"""

import json
import uuid
from flask import Blueprint, request, jsonify, g
from backend.auth_utils import role_required, check_ai_limit, record_ai_usage
from backend import db as database
from backend.services.ai_service import process_message, detect_category, extract_structured_data_demo
from backend.services.risk_engine import assess_risk, check_red_flags
from backend.services.summary_service import generate_summary
from backend.services.notification_service import create_notification

assessments_bp = Blueprint('assessments', __name__)


@assessments_bp.route('/api/assessments', methods=['POST'])
@role_required('patient')
def create_assessment(user):
    """Create a new symptom assessment session."""
    data = request.get_json() or {}
    client_id = data.get('client_id', str(uuid.uuid4()))
    
    # Check for existing assessment with same client_id (idempotent)
    existing = database.fetch_one(g.db, 'SELECT id FROM assessments WHERE client_id = ?', (client_id,))
    if existing:
        return jsonify({'ok': True, 'data': {'id': existing['id'], 'client_id': client_id}})
    
    assessment_id = database.insert(
        g.db,
        'INSERT INTO assessments (client_id, patient_id, status) VALUES (?, ?, ?)',
        (client_id, user['id'], 'in_progress')
    )
    
    return jsonify({'ok': True, 'data': {'id': assessment_id, 'client_id': client_id}}), 201


@assessments_bp.route('/api/assessments/<int:assessment_id>/message', methods=['POST'])
@role_required('patient')
def send_message(user, assessment_id):
    """Send a message in the symptom chat and get AI response."""
    # Verify assessment belongs to this patient
    assessment = database.fetch_one(
        g.db,
        'SELECT * FROM assessments WHERE id = ? AND patient_id = ?',
        (assessment_id, user['id'])
    )
    if not assessment:
        return jsonify({'ok': False, 'error': 'Assessment not found'}), 404
    
    if assessment['status'] == 'completed':
        return jsonify({'ok': False, 'error': 'Assessment already completed'}), 400
    
    data = request.get_json() or {}
    content = (data.get('content', '') or '').strip()
    client_id = data.get('client_id', str(uuid.uuid4()))
    
    if not content:
        return jsonify({'ok': False, 'error': 'Message cannot be empty'}), 400
    
    # Check for red flags IMMEDIATELY on the raw text
    red_flags = check_red_flags(content)
    if red_flags:
        # Save the message
        database.insert(
            g.db,
            'INSERT INTO messages (client_id, assessment_id, role, content) VALUES (?, ?, ?, ?)',
            (client_id, assessment_id, 'user', content)
        )
        
        # Immediately complete with URGENT
        structured = {
            'main_symptoms': [content],
            'category': 'general',
            'duration_days': 0,
            'severity': 'severe',
            'worsening': True,
            'temperature_f': 0,
            'other_symptoms': [],
            'medicines_taken': [],
            'notes': 'Red flag detected in initial text'
        }
        
        risk_result = {
            'level': 'urgent',
            'score': 99,
            'reasons': [f'Red flag: {rf["name"]}' for rf in red_flags],
            'red_flags': red_flags,
            'method': 'red_flags'
        }
        
        # Get patient profile for summary
        profile = database.fetch_one(g.db, 'SELECT * FROM patient_profiles WHERE user_id = ?', (user['id'],))
        summary = generate_summary(structured, risk_result, profile)
        
        # Update assessment
        database.execute(
            g.db,
            """UPDATE assessments SET status = 'completed', category = ?, structured_json = ?,
               risk_level = ?, risk_score = ?, risk_reasons = ?, summary = ?,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            ('general', json.dumps(structured), 'urgent', 99,
             json.dumps(risk_result['reasons']), summary, assessment_id)
        )
        
        return jsonify({
            'ok': True,
            'data': {
                'type': 'urgent',
                'assessment_id': assessment_id,
                'risk': risk_result,
                'red_flags': red_flags,
            }
        })
    
    # Save user message (idempotent via client_id)
    existing_msg = database.fetch_one(g.db, 'SELECT id FROM messages WHERE client_id = ?', (client_id,))
    if not existing_msg:
        database.insert(
            g.db,
            'INSERT INTO messages (client_id, assessment_id, role, content) VALUES (?, ?, ?, ?)',
            (client_id, assessment_id, 'user', content)
        )
    
    # Get all messages for this assessment
    messages = database.fetch_all(
        g.db,
        'SELECT role, content FROM messages WHERE assessment_id = ? ORDER BY created_at',
        (assessment_id,)
    )
    
    # Get patient profile
    profile = database.fetch_one(g.db, 'SELECT * FROM patient_profiles WHERE user_id = ?', (user['id'],))
    
    # Check AI rate limit
    ai_limited = not check_ai_limit(user['id'])
    if not ai_limited:
        record_ai_usage(user['id'])
    
    # Process with AI service
    result = process_message(messages, profile)
    
    if result['type'] == 'followup':
        # Save AI response as a message
        ai_client_id = str(uuid.uuid4())
        database.insert(
            g.db,
            'INSERT INTO messages (client_id, assessment_id, role, content) VALUES (?, ?, ?, ?)',
            (ai_client_id, assessment_id, 'assistant', result['question'])
        )
        
        return jsonify({
            'ok': True,
            'data': {
                'type': 'followup',
                'message': result['question'],
                'chips': result.get('chips', []),
                'progress': result.get('progress', ''),
            }
        })
    
    elif result['type'] == 'complete':
        structured = result['structured_data']
        category = structured.get('category', detect_category(content))
        
        # Run risk assessment
        ai_risk = structured.get('ai_risk_level')
        all_text = ' '.join([m['content'] for m in messages if m['role'] == 'user'])
        risk_result = assess_risk(all_text, structured, profile, ai_risk)
        
        # Generate summary
        summary = generate_summary(structured, risk_result, profile, messages)
        
        # Update assessment with results
        database.execute(
            g.db,
            """UPDATE assessments SET status = 'completed', category = ?, structured_json = ?,
               risk_level = ?, risk_score = ?, risk_reasons = ?, summary = ?,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (category, json.dumps(structured), risk_result['level'], risk_result['score'],
             json.dumps(risk_result['reasons']), summary, assessment_id)
        )
        
        # Save completion message
        complete_msg = f"Assessment complete. Risk level: {risk_result['level'].upper()}"
        database.insert(
            g.db,
            'INSERT INTO messages (client_id, assessment_id, role, content) VALUES (?, ?, ?, ?)',
            (str(uuid.uuid4()), assessment_id, 'system', complete_msg)
        )
        
        return jsonify({
            'ok': True,
            'data': {
                'type': 'complete',
                'assessment_id': assessment_id,
                'risk': risk_result,
                'category': category,
                'structured_data': structured,
                'summary': summary,
            }
        })
    
    return jsonify({'ok': False, 'error': 'Unexpected AI response'}), 500


@assessments_bp.route('/api/assessments/<int:assessment_id>', methods=['GET'])
@role_required('patient', 'doctor')
def get_assessment(user, assessment_id):
    """Get a single assessment with messages."""
    assessment = database.fetch_one(g.db, 'SELECT * FROM assessments WHERE id = ?', (assessment_id,))
    if not assessment:
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    
    # Access control: patient can see their own, doctor can see if they have a consultation
    if user['role'] == 'patient' and assessment['patient_id'] != user['id']:
        return jsonify({'ok': False, 'error': 'Access denied'}), 403
    
    if user['role'] == 'doctor':
        consultation = database.fetch_one(
            g.db,
            'SELECT id FROM consultations WHERE assessment_id = ? AND doctor_id = ?',
            (assessment_id, user['id'])
        )
        if not consultation:
            return jsonify({'ok': False, 'error': 'Access denied'}), 403
    
    messages = database.fetch_all(
        g.db,
        'SELECT role, content, created_at FROM messages WHERE assessment_id = ? ORDER BY created_at',
        (assessment_id,)
    )
    
    # Parse JSON fields
    result = dict(assessment)
    try:
        result['structured_json'] = json.loads(result.get('structured_json') or '{}')
    except (json.JSONDecodeError, TypeError):
        result['structured_json'] = {}
    try:
        result['risk_reasons'] = json.loads(result.get('risk_reasons') or '[]')
    except (json.JSONDecodeError, TypeError):
        result['risk_reasons'] = []
    
    result['messages'] = messages
    
    return jsonify({'ok': True, 'data': result})


@assessments_bp.route('/api/assessments', methods=['GET'])
@role_required('patient')
def list_assessments(user):
    """List all assessments for the current patient."""
    assessments = database.fetch_all(
        g.db,
        'SELECT id, client_id, status, category, risk_level, risk_score, created_at FROM assessments WHERE patient_id = ? ORDER BY created_at DESC',
        (user['id'],)
    )
    return jsonify({'ok': True, 'data': assessments})


@assessments_bp.route('/api/assessments/<int:assessment_id>/alert', methods=['POST'])
@role_required('patient')
def trigger_assessment_alert(user, assessment_id):
    """
    Patient triggers high-risk notification / emergency alert.
    Dispatches in-app notification to patient and alerts on-call verified doctors.
    """
    assessment = database.fetch_one(
        g.db,
        'SELECT * FROM assessments WHERE id = ? AND patient_id = ?',
        (assessment_id, user['id'])
    )
    if not assessment:
        return jsonify({'ok': False, 'error': 'Assessment not found'}), 404

    risk_lvl = (assessment.get('risk_level') or 'medium').upper()
    category = (assessment.get('category') or 'general').replace('_', ' ').title()

    # 1. Create patient notification (with link to result)
    create_notification(
        g.db,
        user_id=user['id'],
        text=f"🚨 High-Risk Health Alert Activated: Your {category} assessment ({risk_lvl} Risk) is registered for emergency doctor monitoring.",
        link=f"/pages/result.html?id={assessment_id}"
    )

    # 2. Dispatch high-risk alert to verified doctors (including on-call/offline)
    doctors = database.fetch_all(
        g.db,
        "SELECT u.id, u.name FROM users u WHERE u.role = 'doctor' AND u.is_verified = 1 LIMIT 5"
    )
    for doc in doctors:
        create_notification(
            g.db,
            user_id=doc['id'],
            text=f"🚨 HIGH-RISK EMERGENCY ALERT: Patient {user['name']} reported {risk_lvl} risk {category} symptoms. Immediate review required.",
            link=f"/pages/doctor-consultations.html"
        )

    return jsonify({
        'ok': True,
        'data': {
            'message': 'High-risk alert activated. You and on-call doctors have been notified.',
            'alert_active': True,
            'notified_doctors_count': len(doctors)
        }
    })
