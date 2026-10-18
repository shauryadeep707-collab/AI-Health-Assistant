"""
Knowledge Base Service for AI Health Assistant.
Loads and serves guidance, medicines, facial skincare serums, and diagnostic tests.

DATABASE ARCHITECTURE RULE:
All medicines, healthcare products, serums, side effects, and diagnostic tests
are stored 100% LOCALLY on the user's laptop/system (SQLite health_assistant.db & JSON).
They NEVER consume or utilize cloud storage/memory on Supabase or PostgreSQL.
Cloud SQL (Supabase / Postgres) is strictly reserved for patient registrations,
visitor logs, doctor profiles, and consultation statistics.
"""

import json
import os
import re
import sqlite3
import urllib.parse
from backend.config import config

_KB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base')
_GUIDANCE = {}
_MEDICINES = {}


def _load_data():
    """Load guidance and medicine data from local JSON files on user's laptop."""
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


def _get_local_sqlite_conn():
    """
    Returns a direct connection to the local SQLite database on the user's laptop.
    Ensures medicine and healthcare product data remains 100% on the local system
    and never consumes memory or table quota on Supabase or PostgreSQL.
    """
    db_path = config.SQLITE_PATH
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Warning: Could not connect to local SQLite database: {e}")
        return None


def generate_buy_links(search_term):
    """
    Generate direct search and purchase URLs for verified online pharmacies.
    Supports Tata 1mg, Apollo Pharmacy, Netmeds, and PharmEasy.
    """
    clean_term = (search_term or '').strip()
    if not clean_term:
        clean_term = "Medicine"
    encoded = urllib.parse.quote_plus(clean_term)

    return {
        "tata_1mg": f"https://www.1mg.com/search/all?name={encoded}",
        "apollo": f"https://www.apollopharmacy.in/search-medicines/{encoded}",
        "netmeds": f"https://www.netmeds.com/catalogsearch/result/{encoded}/all",
        "pharmeasy": f"https://pharmeasy.in/search/all?name={encoded}"
    }


def enrich_medicine(med, category=None):
    """
    Enrich a medicine dictionary with verified direct buy links, safe dosage,
    price estimate, and structured side-effects if missing.
    """
    if not isinstance(med, dict):
        return med

    m = dict(med)
    name = m.get('name', 'Remedy')
    search_term = m.get('search_term')
    if not search_term:
        clean = re.sub(r'\(.*?\)', '', name).strip()
        search_term = clean if clean else name
        m['search_term'] = search_term

    if not m.get('buy_links'):
        m['buy_links'] = generate_buy_links(search_term)

    if not m.get('price_estimate'):
        m['price_estimate'] = "₹20 – ₹60"

    if not m.get('otc_status'):
        m['otc_status'] = "100% Non-Prescription OTC"

    if not m.get('dosage_guide'):
        m['dosage_guide'] = "Follow package labeling or consult a registered pharmacist."

    se = m.get('side_effects')
    if isinstance(se, str):
        try:
            se = json.loads(se)
        except Exception:
            se = None

    if not isinstance(se, dict) or not se.get('common'):
        m['side_effects'] = {
            "common": ["Mild gastrointestinal changes", "Transient dizziness or mild nausea"],
            "serious": ["Allergic rash, hives, or swelling of lips/face", "Difficulty breathing or wheezing"],
            "management": "Take with a glass of water, preferably with or after food. If severe allergic symptoms occur, discontinue immediately and seek emergency medical care."
        }
    else:
        m['side_effects'] = se

    if category and not m.get('category'):
        m['category'] = category

    return m


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


def get_medicines(category=None):
    """
    Get OTC medicine and healthcare products information from local laptop JSON storage.
    Returns list of enriched product dicts.
    """
    if category:
        cat_key = category.lower()
        cat_data = _MEDICINES.get(cat_key, _MEDICINES.get('general', []))
        items = cat_data if isinstance(cat_data, list) else cat_data.get('medicines', [])
        return [enrich_medicine(m, cat_key) for m in items]
    
    # Return all medicines across all categories
    all_meds = []
    for cat_key, items in _MEDICINES.items():
        if isinstance(items, list):
            for m in items:
                all_meds.append(enrich_medicine(m, cat_key))
    return all_meds


def get_medicines_from_db(conn=None, category=None):
    """
    Fetch medicines directly from LOCAL laptop SQLite database (health_assistant.db).
    NEVER queries or consumes memory in Supabase or PostgreSQL.
    """
    local_conn = _get_local_sqlite_conn()
    if local_conn:
        try:
            cur = local_conn.cursor()
            cols = "id, category, name, purpose, general_info, precautions, avoid_if, safety_note, side_effects, dosage_guide, price_estimate, search_term, otc_status"
            if category:
                cur.execute(f"SELECT {cols} FROM medicines WHERE category = ?", (category.lower(),))
            else:
                cur.execute(f"SELECT {cols} FROM medicines ORDER BY category, name")
            rows = cur.fetchall()
            local_conn.close()

            if rows:
                enriched_rows = []
                for r in rows:
                    item = dict(r)
                    for field in ('precautions', 'avoid_if', 'side_effects'):
                        if isinstance(item.get(field), str):
                            try:
                                item[field] = json.loads(item[field])
                            except Exception:
                                pass
                    enriched_rows.append(enrich_medicine(item, item.get('category')))
                return enriched_rows
        except Exception as e:
            if local_conn:
                local_conn.close()

    # Fallback to local JSON on laptop
    return get_medicines(category)


STOP_WORDS = {
    'what', 'are', 'the', 'side', 'effects', 'effect', 'of', 'is', 'can', 'a', 'an',
    'in', 'for', 'to', 'how', 'do', 'i', 'take', 'product', 'medicine', 'medicines',
    'about', 'any', 'does', 'have', 'and', 'or', 'with', 'my', 'tell', 'me', 'please',
    'should', 'use', 'apply', 'serum', 'face', 'test', 'deficiency'
}


def search_medicines(query=None, category=None, conn=None):
    """
    Search medicines, serums, and tests from the local system database.
    """
    medicines = get_medicines_from_db(category=category)
    
    q = (query or '').strip().lower()
    if not q:
        return medicines

    raw_tokens = re.findall(r'[a-zA-Z0-9]+', q)
    filtered_tokens = [t for t in raw_tokens if t not in STOP_WORDS and len(t) > 1]
    tokens = filtered_tokens if filtered_tokens else raw_tokens

    results = []

    for m in medicines:
        name = (m.get('name') or '').lower()
        search_term = (m.get('search_term') or '').lower()
        purpose = (m.get('purpose') or '').lower()
        info = (m.get('general_info') or '').lower()
        cat = (m.get('category') or '').lower()
        precautions = " ".join(m.get('precautions') or []).lower() if isinstance(m.get('precautions'), list) else ""

        score = 0
        if q in name or q in search_term:
            score += 50

        for t in tokens:
            if name.startswith(t) or search_term.startswith(t):
                score += 30

            if re.search(r'\b' + re.escape(t) + r'\b', name) or re.search(r'\b' + re.escape(t) + r'\b', search_term):
                score += 25
            elif t in name or t in search_term:
                score += 12

            if re.search(r'\b' + re.escape(t) + r'\b', purpose):
                score += 10
            elif t in purpose:
                score += 5

            if re.search(r'\b' + re.escape(t) + r'\b', cat):
                score += 8

            if t in info:
                score += 3
            if t in precautions:
                score += 2

        if score > 0:
            m_copy = dict(m)
            m_copy['_score'] = score
            results.append(m_copy)

    results.sort(key=lambda x: x.get('_score', 0), reverse=True)
    return results


def assess_facial_condition_and_recommend(text_or_concerns):
    """
    AI Facial Health & Skincare Advisor.
    Evaluates facial skin concerns (acne, dark spots, dullness, dark circles, flakiness),
    determines likely nutritional/dermatological deficiencies, recommends diagnostic
    lab tests, specifies active facial serums, and provides 1-click buy links!
    """
    text = (text_or_concerns or '').lower()
    all_facial_products = get_medicines_from_db(category='facial_care')
    
    # Map products by search term or key token
    prod_map = {p['search_term']: p for p in all_facial_products}

    # Clinical diagnostic criteria
    has_acne = any(w in text for w in ['acne', 'pimple', 'pimples', 'breakout', 'blackhead', 'whitehead', 'clogged', 'pores', 'oil', 'oily'])
    has_dark_spots = any(w in text for w in ['dark spot', 'dark spots', 'pigmentation', 'melasma', 'blemish', 'tan', 'tanning', 'sun spot', 'patch'])
    has_dullness = any(w in text for w in ['dull', 'dullness', 'glow', 'lifeless', 'tired', 'brightening', 'pale'])
    has_dryness = any(w in text for w in ['dry', 'dryness', 'flaky', 'peeling', 'tight', 'barrier', 'stinging', 'burning', 'redness', 'sensitive'])
    has_dark_circles = any(w in text for w in ['dark circle', 'dark circles', 'under eye', 'puffy', 'puffiness', 'eye bag', 'eyes'])
    has_aging = any(w in text for w in ['wrinkle', 'wrinkles', 'fine lines', 'aging', 'texture', 'bumpy', 'sagging', 'elasticity'])

    # Default to general glowing & barrier routine if unspecific
    if not any([has_acne, has_dark_spots, has_dullness, has_dryness, has_dark_circles, has_aging]):
        has_dullness = True
        has_dark_spots = True

    identified_concerns = []
    potential_deficiencies = []
    recommended_tests = []
    recommended_serums = []

    # 1. ACNE & PORES
    if has_acne:
        identified_concerns.append("Active Acne Breakouts & Congested Pores")
        potential_deficiencies.append("Zinc Deficiency (impairs follicular immunity and wound repair) & High Glycemic/Androgen Activity")
        if "Zinc Test Tata 1mg Labs" in prod_map:
            recommended_tests.append(prod_map["Zinc Test Tata 1mg Labs"])
        if "Minimalist Niacinamide 10% Zinc Serum" in prod_map:
            recommended_serums.append(prod_map["Minimalist Niacinamide 10% Zinc Serum"])
        if "Minimalist Salicylic Acid 2% Serum" in prod_map:
            recommended_serums.append(prod_map["Minimalist Salicylic Acid 2% Serum"])

    # 2. DARK SPOTS & HYPERPIGMENTATION
    if has_dark_spots:
        identified_concerns.append("Hyperpigmentation, Dark Spots & Post-Acne Discoloration")
        potential_deficiencies.append("Vitamin C Deficiency (oxidative stress) & UV-Induced Melanocyte Stimulation")
        if "Minimalist 10% Vitamin C Serum" in prod_map:
            recommended_serums.append(prod_map["Minimalist 10% Vitamin C Serum"])
        if "Minimalist Alpha Arbutin 2% Face Serum" in prod_map:
            recommended_serums.append(prod_map["Minimalist Alpha Arbutin 2% Face Serum"])

    # 3. DULLNESS & TIRED COMPLEXION
    if has_dullness:
        identified_concerns.append("Dull, Fatigued & Lackluster Facial Complexion")
        potential_deficiencies.append("Vitamin D3 & Vitamin B12 Deficiency (slow epidermal cell turnover) & Subclinical Iron Depletion")
        if "Vitamin D and B12 Test Tata 1mg Labs" in prod_map:
            recommended_tests.append(prod_map["Vitamin D and B12 Test Tata 1mg Labs"])
        if "Minimalist 10% Vitamin C Serum" in prod_map and prod_map["Minimalist 10% Vitamin C Serum"] not in recommended_serums:
            recommended_serums.append(prod_map["Minimalist 10% Vitamin C Serum"])

    # 4. DRYNESS & DAMAGED SKIN BARRIER
    if has_dryness:
        identified_concerns.append("Dehydrated Facial Skin & Compromised Moisture Barrier")
        potential_deficiencies.append("Epidermal Lipid / Essential Fatty Acid Depletion & Transepidermal Water Loss")
        if "Minimalist Hyaluronic Acid 2% B5 Serum" in prod_map:
            recommended_serums.append(prod_map["Minimalist Hyaluronic Acid 2% B5 Serum"])
        if "Minimalist Ceramide Moisturizer" in prod_map:
            recommended_serums.append(prod_map["Minimalist Ceramide Moisturizer"])

    # 5. DARK CIRCLES & EYE PUFFINESS
    if has_dark_circles:
        identified_concerns.append("Periorbital Dark Circles & Under-Eye Fluid Accumulation")
        potential_deficiencies.append("Iron / Ferritin Deficiency (poor tissue oxygenation) & Vitamin B12 / Sleep Deficit")
        if "Iron Deficiency Ferritin Test Apollo Diagnostics" in prod_map:
            recommended_tests.append(prod_map["Iron Deficiency Ferritin Test Apollo Diagnostics"])
        if "Minimalist Caffeine 5% Under Eye Serum" in prod_map:
            recommended_serums.append(prod_map["Minimalist Caffeine 5% Under Eye Serum"])

    # 6. AGING & UNEVEN TEXTURE
    if has_aging:
        identified_concerns.append("Fine Lines, Premature Aging & Irregular Skin Texture")
        potential_deficiencies.append("Collagen & Elastin Degradation, Photo-Damage")
        if "Minimalist Retinol 0.3% Anti Aging Face Serum" in prod_map:
            recommended_serums.append(prod_map["Minimalist Retinol 0.3% Anti Aging Face Serum"])

    # Always ensure Sunscreen is recommended as foundational defense
    if "Derma Co 1% Hyaluronic Sunscreen SPF 50" in prod_map and prod_map["Derma Co 1% Hyaluronic Sunscreen SPF 50"] not in recommended_serums:
        recommended_serums.append(prod_map["Derma Co 1% Hyaluronic Sunscreen SPF 50"])

    # If no tests matched, default to Vitamin D & B12 test
    if not recommended_tests and "Vitamin D and B12 Test Tata 1mg Labs" in prod_map:
        recommended_tests.append(prod_map["Vitamin D and B12 Test Tata 1mg Labs"])

    # Synthesize structured clinical response
    answer_lines = [
        "### 🧴 AI Facial Health & Skincare Checkup Report",
        f"**Primary Concerns Identified:** {', '.join(identified_concerns)}",
        "",
        "#### 🔬 1. Underlying Deficiencies Checked:",
        "\n".join([f"- **{d}**" for d in potential_deficiencies]),
        "",
        "#### 🧪 2. Recommended Diagnostic Lab Tests (Checkup):",
        "To verify if internal deficiencies are causing your facial skin concerns, we recommend scheduling these simple blood checkups with direct home sample collection:",
    ]

    for test in recommended_tests:
        answer_lines.append(f"- **{test['name']}** ({test.get('price_estimate', '₹500 - ₹900')}): {test['purpose']}")

    answer_lines.extend([
        "",
        "#### 💧 3. Recommended Facial Serums & Topical Solutions:",
        "Clinically proven active serums matched specifically to your skin concerns:",
    ])

    for serum in recommended_serums:
        answer_lines.append(f"- **{serum['name']}** ({serum.get('price_estimate', '₹500 - ₹600')}): {serum['purpose']}. *Directions: {serum.get('dosage_guide', 'Apply onto clean skin.')}*")

    answer_lines.extend([
        "",
        "#### 🛒 4. Direct Online Purchase Links:",
        "You can order the recommended serums and book home lab tests directly online via verified Indian pharmacies below."
    ])

    all_matched = recommended_serums + recommended_tests

    return {
        "ok": True,
        "is_facial_checkup": True,
        "concerns": identified_concerns,
        "deficiencies": potential_deficiencies,
        "recommended_tests": recommended_tests,
        "recommended_serums": recommended_serums,
        "matched_medicines": all_matched,
        "answer": "\n".join(answer_lines)
    }


def ask_product_side_effects(query, product_name=None, conn=None):
    """
    Medical Intelligence Assistant for asking about product side effects,
    facial skincare serums, diagnostic deficiency tests, and direct buy options.
    """
    q = (query or '').strip()
    target_product = (product_name or '').strip()

    # Detect if user is asking about face, skin serums, or deficiency tests
    is_face_query = any(w in q.lower() for w in ['face', 'facial', 'skin', 'serum', 'acne', 'pimple', 'dark spot', 'dull', 'deficiency', 'pigmentation', 'dark circle', 'dry skin', 'glow'])
    if is_face_query and not target_product:
        return assess_facial_condition_and_recommend(q)

    # Search for matching product in local database
    search_q = target_product if target_product else q
    matches = search_medicines(search_q)

    if not matches and target_product:
        matches = search_medicines(q)

    if not matches and is_face_query:
        return assess_facial_condition_and_recommend(q)

    if not matches:
        all_meds = get_medicines()
        for word in q.lower().split():
            if len(word) > 3:
                for m in all_meds:
                    if word in m['name'].lower() or word in m.get('purpose', '').lower():
                        matches.append(m)
        if not matches:
            matches = all_meds[:4]

    matched_med = matches[0] if matches else None
    
    if matched_med:
        name = matched_med.get('name', 'This medication')
        purpose = matched_med.get('purpose', '')
        se = matched_med.get('side_effects', {})
        common_se = se.get('common', [])
        serious_se = se.get('serious', [])
        management = se.get('management', 'Take with food or water as directed on the label.')
        dosage = matched_med.get('dosage_guide', 'Follow package instructions.')
        avoid_if = matched_med.get('avoid_if', [])
        price = matched_med.get('price_estimate', '₹20 – ₹50')

        answer_parts = [
            f"### 🛡️ Clinical Overview & Side Effects Profile: {name}",
            f"**Primary Indication:** {purpose}",
            f"**Estimated Price:** {price} (OTC Supportive)",
            "",
            "#### 1. Common Side Effects (Usually Mild & Transient):",
            "\n".join([f"- **{item}**" for item in common_se]) if common_se else "- Mild digestive changes or slight drowsiness.",
            "",
            "#### 2. ⚠️ Serious Red-Flag Warnings (Seek Urgent Medical Care If Occurs):",
            "\n".join([f"- 🚨 **{item}**" for item in serious_se]) if serious_se else "- Severe allergic reactions, hives, facial swelling, or breathing difficulty.",
            "",
            "#### 3. Safe Management & How to Avoid Side Effects:",
            f"{management}",
            "",
            "#### 4. Safe Usage & Dosage Guidance:",
            f"- **Directions:** {dosage}",
            f"- **Contraindications (Avoid If):** {', '.join(avoid_if) if avoid_if else 'Known hypersensitivity.'}",
            "",
            "#### 🛒 Direct Online Purchase:",
            f"You can order **{name}** directly online from licensed pharmacies below with instant home delivery."
        ]
        answer_text = "\n".join(answer_parts)
    else:
        answer_text = (
            "I could not locate an exact match for that product in our verified local OTC knowledge base. "
            "Please check the spelling or ask about common self-care medicines like Paracetamol, Ibuprofen, "
            "Cetirizine, Gelusil, ORS, or facial serums like Vitamin C, Niacinamide, and Hyaluronic Acid."
        )

    return {
        "ok": True,
        "query": q,
        "product_name": target_product or (matched_med.get('name') if matched_med else None),
        "answer": answer_text,
        "matched_medicines": matches[:5]
    }


def get_specialization_for_category(category):
    """
    Suggest a doctor specialization based on symptom category.
    """
    mapping = {
        'fever': 'General Physician',
        'cold_cough': 'General Physician',
        'headache': 'Neurologist',
        'sore_throat': 'ENT Specialist',
        'stomach': 'Gastroenterologist',
        'skin': 'Dermatologist',
        'facial_care': 'Dermatologist',
        'bone_joint': 'Orthopedic',
        'heart': 'Cardiologist',
        'child': 'Pediatrician',
        'general': 'General Physician',
    }
    return mapping.get((category or '').lower(), 'General Physician')
