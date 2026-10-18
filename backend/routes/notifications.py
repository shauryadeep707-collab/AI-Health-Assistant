"""
Notifications and Knowledge Base retrieval routes for AI Health Assistant.
Provides endpoints for notifications, home-care guidance, medicine catalog,
side-effects Q&A, and direct online pharmacy links.
"""

from flask import Blueprint, request, jsonify, g
from backend.auth_utils import role_required
from backend.services.notification_service import get_user_notifications, mark_notification_read
from backend.services.knowledge_base import (
    get_guidance,
    get_medicines,
    get_medicines_from_db,
    search_medicines,
    ask_product_side_effects
)

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/api/notifications', methods=['GET'])
@role_required('patient', 'doctor', 'admin')
def list_notifications(user):
    """Fetch notifications for the logged-in user."""
    unread_only = request.args.get('unread') == 'true'
    notifications = get_user_notifications(g.db, user['id'], unread_only=unread_only)
    return jsonify({'ok': True, 'data': notifications})


@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@role_required('patient', 'doctor', 'admin')
def mark_read(user, notification_id):
    """Mark a notification as read."""
    mark_notification_read(g.db, notification_id, user['id'])
    return jsonify({'ok': True, 'data': {'message': 'Notification marked as read'}})


@notifications_bp.route('/api/guidance/<category>', methods=['GET'])
def fetch_guidance(category):
    """Fetch home-care guidance for low-risk scenarios."""
    guidance = get_guidance(category)
    return jsonify({'ok': True, 'data': guidance})


@notifications_bp.route('/api/medicines', methods=['GET'])
def fetch_all_medicines():
    """Fetch all controlled OTC medicines with side effects and buy links."""
    medicines = get_medicines_from_db(g.db)
    return jsonify({'ok': True, 'data': medicines, 'count': len(medicines)})


@notifications_bp.route('/api/medicines/search', methods=['GET'])
def search_medicine_catalog():
    """
    Search medicines by symptom, condition, brand, or active ingredient.
    Query params:
      - q: search keyword / question
      - category: optional category filter
    """
    q = request.args.get('q', '')
    cat = request.args.get('category', None)
    results = search_medicines(query=q, category=cat, conn=g.db)
    return jsonify({'ok': True, 'data': results, 'count': len(results)})


@notifications_bp.route('/api/medicines/ask', methods=['GET', 'POST'])
def ask_side_effects():
    """
    Ask AI / Medical Knowledge Assistant about product side effects,
    contraindications, safe dosage, and direct buy links.
    Accepts GET query params or POST JSON:
      - query / q: user question or concern (e.g. "What are the side effects of paracetamol?")
      - product_name / product: optional specific product name
    """
    if request.method == 'GET':
        query = (request.args.get('query') or request.args.get('q') or '').strip()
        product_name = (request.args.get('product_name') or request.args.get('product') or '').strip()
    else:
        body = request.get_json(silent=True) or {}
        query = (body.get('query') or body.get('q') or '').strip()
        product_name = (body.get('product_name') or body.get('product') or '').strip()

    if not query and not product_name:
        return jsonify({'ok': False, 'error': 'Please provide a question or product name'}), 400

    result = ask_product_side_effects(query=query, product_name=product_name, conn=g.db)
    return jsonify(result)


@notifications_bp.route('/api/facial/checkup', methods=['GET', 'POST'])
def facial_checkup():
    """
    AI Facial Skincare, Deficiency Checkup, and Serum Recommendation Advisor.
    Accepts GET query param 'concerns' / 'q' or POST JSON { 'concerns': '...' }.
    """
    if request.method == 'GET':
        concerns = (request.args.get('concerns') or request.args.get('q') or request.args.get('query') or '').strip()
    else:
        body = request.get_json(silent=True) or {}
        concerns = (body.get('concerns') or body.get('q') or body.get('query') or '').strip()

    if not concerns:
        return jsonify({'ok': False, 'error': 'Please provide your facial skin concerns or symptoms'}), 400

    from backend.services.knowledge_base import assess_facial_condition_and_recommend
    result = assess_facial_condition_and_recommend(concerns)
    return jsonify(result)


@notifications_bp.route('/api/system/storage-info', methods=['GET'])
def system_storage_info():
    """
    Returns database architecture and metrics:
    - Local Laptop Storage: All 77 medicines, facial serums, and lab tests (0 MB on Supabase/Postgres).
    - Cloud Database: Number of patients joined, visitor logs, doctor profiles, and consultation counts.
    """
    from backend.config import config
    from backend import db as database
    
    patient_count = 0
    doctor_count = 0
    consultation_count = 0
    recent_patients = []
    doctor_stats = []
    
    try:
        p_row = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM users WHERE role = 'patient'")
        patient_count = p_row['count'] if p_row else 0
        
        d_row = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM users WHERE role = 'doctor'")
        doctor_count = d_row['count'] if d_row else 0
        
        c_row = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM consultations")
        consultation_count = c_row['count'] if c_row else 0
        
        recent_patients = database.fetch_all(
            g.db,
            "SELECT id, name, email, created_at FROM users WHERE role = 'patient' ORDER BY created_at DESC LIMIT 5"
        )
        
        doctor_stats = database.fetch_all(
            g.db,
            """SELECT u.id, u.name, u.email, d.specialization, d.clinic_name,
                      (SELECT COUNT(*) FROM consultations c WHERE c.doctor_id = u.id) as consulted_patients_count
               FROM users u
               LEFT JOIN doctor_profiles d ON u.id = d.user_id
               WHERE u.role = 'doctor'
               ORDER BY consulted_patients_count DESC, u.name ASC"""
        )
    except Exception as e:
        print(f"Metrics query note: {e}")

    from backend.services.knowledge_base import get_medicines_from_db
    local_medicines = get_medicines_from_db()

    return jsonify({
        'ok': True,
        'data': {
            'architecture': {
                'local_laptop_database': {
                    'engine': 'Local SQLite & Local JSON',
                    'file_path': config.SQLITE_PATH,
                    'stored_data': 'All 77+ OTC Medicines, Facial Serums, Skincare Actives, Side Effects, Safe Dosages, and Online Pharmacy Buy Links',
                    'total_medicines_and_products': len(local_medicines),
                    'cloud_memory_used': '0 MB (Stored exclusively on your system/laptop)'
                },
                'cloud_database': {
                    'engine': 'Supabase / Cloud PostgreSQL' if config.DATABASE_URL else 'Local SQLite (Cloud Ready)',
                    'dedicated_purpose': 'Stores new patients joining, website visitor logs, doctor profiles, and doctor consultation counts',
                    'total_patients_joined': patient_count,
                    'total_doctors_uploaded': doctor_count,
                    'total_consultations_conducted': consultation_count
                }
            },
            'recent_patients': recent_patients,
            'doctor_consultations': doctor_stats
        }
    })


@notifications_bp.route('/api/ai/suggest', methods=['GET', 'POST'])
def ai_suggest_and_autocorrect():
    """
    AI Auto-Correction & Autocomplete Suggestions Endpoint.
    Accepts GET query param 'q' or POST JSON { 'q': '...' }.
    Returns:
      - original: query text
      - corrected: spell-checked text
      - has_correction: True if typos were detected and corrected
      - fixes: list of exact typo replacements
      - autocompletions: list of smart phrase completion suggestions
    """
    if request.method == 'GET':
        q = (request.args.get('q') or request.args.get('query') or '').strip()
    else:
        body = request.get_json(silent=True) or {}
        q = (body.get('q') or body.get('query') or '').strip()

    from backend.services.autocomplete_service import get_clinical_suggestions
    result = get_clinical_suggestions(q)
    return jsonify(result)


@notifications_bp.route('/api/medicines/<category>', methods=['GET'])
def fetch_medicines(category):
    """Fetch controlled OTC medicine info for specific symptom category."""
    medicines = get_medicines_from_db(g.db, category)
    return jsonify({'ok': True, 'data': medicines, 'category': category, 'count': len(medicines)})
