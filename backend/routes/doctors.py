"""
Doctor Routes for AI Health Assistant.
Handles nearby doctor search and availability toggle.
"""

import math
from flask import Blueprint, request, jsonify, g
from backend.auth_utils import role_required
from backend import db as database

doctors_bp = Blueprint('doctors', __name__)


def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance in km between two lat/lng points.
    WHY Haversine: gives accurate distances on Earth's curved surface,
    which is needed for finding nearby doctors.
    """
    R = 6371  # Earth's radius in km
    
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


CATEGORY_SPECIALTIES = {
    'fever': ['General Physician', 'Pediatrician', 'Internal Medicine'],
    'cold_cough': ['Pulmonologist', 'ENT Specialist', 'General Physician'],
    'headache': ['Neurologist', 'General Physician'],
    'sore_throat': ['ENT Specialist', 'General Physician'],
    'stomach': ['Gastroenterologist', 'General Physician'],
    'cardiac': ['Cardiologist', 'General Physician'],
    'skin': ['Dermatologist', 'General Physician'],
    'general': ['General Physician']
}


@doctors_bp.route('/api/doctors/nearby', methods=['GET'])
@role_required('patient')
def nearby_doctors(user):
    """Find nearby doctors.
    Query params: lat, lng, radius_km (default 50), specialization (optional),
    category (optional - matches condition to relevant medical specialty),
    include_offline (optional - if true, returns both online and offline doctors).
    Only returns verified (is_verified=1) doctors.
    """
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
    except (ValueError, TypeError):
        lat, lng = 0, 0
    
    radius_km = float(request.args.get('radius_km', 50))
    specialization = request.args.get('specialization', '').strip()
    category = request.args.get('category', '').strip().lower()
    city = request.args.get('city', '').strip()
    include_offline = request.args.get('include_offline', '').lower() in ('true', '1', 'yes')
    
    # Build query
    sql = """
        SELECT u.id, u.name, u.email, d.specialization, d.clinic_name, d.address,
               d.city, d.lat, d.lng, d.fee, d.experience_years, d.is_available,
               d.available_days, d.available_from, d.available_to, d.medical_degree
        FROM users u
        JOIN doctor_profiles d ON u.id = d.user_id
        WHERE u.role = 'doctor' AND u.is_verified = 1
    """
    params = []
    
    if not include_offline:
        sql += ' AND d.is_available = 1'
    
    if specialization:
        sql += ' AND d.specialization = ?'
        params.append(specialization)
    elif category and category in CATEGORY_SPECIALTIES:
        # Match condition to relevant medical specialties
        specs = CATEGORY_SPECIALTIES[category]
        placeholders = ','.join(['?' for _ in specs])
        sql += f' AND d.specialization IN ({placeholders})'
        params.extend(specs)
    
    if city:
        sql += ' AND LOWER(d.city) = LOWER(?)'
        params.append(city)
    
    doctors = database.fetch_all(g.db, sql, params)
    
    # If category filter was too strict and returned 0 doctors, fall back to all verified doctors
    if len(doctors) == 0 and category:
        fallback_sql = """
            SELECT u.id, u.name, u.email, d.specialization, d.clinic_name, d.address,
                   d.city, d.lat, d.lng, d.fee, d.experience_years, d.is_available,
                   d.available_days, d.available_from, d.available_to, d.medical_degree
            FROM users u
            JOIN doctor_profiles d ON u.id = d.user_id
            WHERE u.role = 'doctor' AND u.is_verified = 1
        """
        fallback_params = []
        if not include_offline:
            fallback_sql += ' AND d.is_available = 1'
        doctors = database.fetch_all(g.db, fallback_sql, fallback_params)
    
    # Calculate distances and filter by radius
    results = []
    for doc in doctors:
        doc_lat = doc.get('lat', 0) or 0
        doc_lng = doc.get('lng', 0) or 0
        
        if lat != 0 and lng != 0 and doc_lat != 0 and doc_lng != 0:
            distance = haversine_distance(lat, lng, doc_lat, doc_lng)
            if distance > radius_km:
                continue
            doc['distance_km'] = round(distance, 1)
        else:
            doc['distance_km'] = None  # Unknown distance (no location)
        
        results.append(doc)
    
    # Sort: Condition-matched specialists first, online available first, then nearest distance
    target_specs = CATEGORY_SPECIALTIES.get(category, []) if category else []
    results.sort(key=lambda d: (
        0 if (target_specs and d.get('specialization') in target_specs) else 1,
        0 if d.get('is_available') == 1 else 1,
        d.get('distance_km') if d.get('distance_km') is not None else 9999
    ))
    
    return jsonify({'ok': True, 'data': results})


@doctors_bp.route('/api/doctor/availability', methods=['PUT'])
@role_required('doctor')
def toggle_availability(user):
    """Toggle doctor's availability status."""
    data = request.get_json() or {}
    is_available = 1 if data.get('is_available', True) else 0
    
    database.execute(
        g.db,
        'UPDATE doctor_profiles SET is_available = ? WHERE user_id = ?',
        (is_available, user['id'])
    )
    
    return jsonify({'ok': True, 'data': {'is_available': bool(is_available)}})
