"""
Script to add comprehensive Facial Care & Skincare Serums & Deficiency Tests
to the local laptop Knowledge Base (medicines.json and local SQLite health_assistant.db).
Does NOT touch Supabase or PostgreSQL, keeping all medicine/product memory strictly on the laptop.
"""

import json
import os
import sqlite3
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KB_PATH = os.path.join(BASE_DIR, 'knowledge_base', 'medicines.json')
DB_PATH = os.path.join(BASE_DIR, 'health_assistant.db')

FACIAL_CARE_PRODUCTS = [
    {
        "name": "Niacinamide 10% + Zinc 1% Blemish & Pore Serum",
        "purpose": "Reduces active facial blemishes, balances excess sebum/oil, minimizes enlarged pores, and strengthens skin barrier.",
        "general_info": "High-strength clinical serum combining Vitamin B3 (Niacinamide 10%) with Zinc PCA 1% to regulate sebum production and reduce post-acne redness.",
        "precautions": [
            "Perform a 24-hour patch test behind ear or on inner arm before first facial application.",
            "Do not combine directly with pure L-Ascorbic Acid (Vitamin C) in the same immediate routine step (alternate AM/PM).",
            "Apply onto slightly damp skin followed by a gentle moisturizer."
        ],
        "avoid_if": [
            "Known hypersensitivity to topical niacinamide or zinc salts.",
            "Severely broken skin or open bleeding wounds."
        ],
        "safety_note": "First-line dermatological serum for oily, acne-prone, or blemish-prone skin. Safe for daily morning and evening use.",
        "search_term": "Minimalist Niacinamide 10% Zinc Serum",
        "price_estimate": "₹550 – ₹600",
        "dosage_guide": "Apply 2 to 3 drops across entire face morning and evening after cleansing, before heavier creams.",
        "side_effects": {
            "common": ["Mild temporary tingling sensation upon initial use", "Slight redness during first 3-5 days of adaptation"],
            "serious": ["Allergic facial swelling or severe contact dermatitis (rare)"],
            "management": "If initial tingling occurs, introduce gradually (3 times a week) before moving to daily use. Always follow with moisturizer."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Vitamin C 10% - 16% + Ferulic Acid Glow & Dark Spot Serum",
        "purpose": "Fades stubborn dark spots, evens skin tone, brightens dull fatigued face, and protects against environmental free radicals.",
        "general_info": "Potent antioxidant face serum containing stabilized Vitamin C (Ethyl Ascorbic Acid / L-Ascorbic Acid) boosted with Ferulic Acid to inhibit tyrosinase and stimulate collagen.",
        "precautions": [
            "Always follow with a broad-spectrum SPF 50 sunscreen during the daytime.",
            "Store in an opaque bottle away from direct heat and sunlight to avoid oxidation.",
            "If serum turns deep dark brown, it has oxidized and should be replaced."
        ],
        "avoid_if": [
            "Active inflamed cystic acne flare-ups or severely impaired weeping skin barrier.",
            "Known ascorbic acid allergy."
        ],
        "safety_note": "Gold standard for facial glow and post-inflammatory hyperpigmentation. Recommended for morning use.",
        "search_term": "Minimalist 10% Vitamin C Serum",
        "price_estimate": "₹600 – ₹700",
        "dosage_guide": "Dispense 3-4 drops onto palms and gently pat into clean, dry facial skin in the morning. Follow with SPF 50.",
        "side_effects": {
            "common": ["Mild initial stinging on freshly washed skin", "Temporary warm sensation"],
            "serious": ["Severe contact dermatitis or skin peeling if used with harsh scrubs"],
            "management": "Apply only onto dry skin to reduce stinging. Do not layer simultaneously with AHA/BHA exfoliants."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Hyaluronic Acid 2% + Vitamin B5 Deep Hydration Serum",
        "purpose": "Replenishes deep skin moisture, plumps fine dehydration lines, repairs tight flaking face, and restores elasticity.",
        "general_info": "Multi-molecular weight hyaluronic acid that penetrates multiple epidermal layers, drawing up to 1000x its weight in water, paired with soothing Provitamin B5 (D-Panthenol).",
        "precautions": [
            "ALWAYS apply to damp skin (after washing or misting) to draw water into the skin rather than pulling from deep tissues.",
            "Lock in immediately with an emollient moisturizer to prevent moisture evaporation.",
            "Suitable for all skin types, including sensitive and eczema-prone faces."
        ],
        "avoid_if": [
            "Known allergy to hyaluronic acid or panthenol (extremely rare)."
        ],
        "safety_note": "Crucial foundational hydration for dry, dehydrated, or barrier-compromised facial skin.",
        "search_term": "Minimalist Hyaluronic Acid 2% B5 Serum",
        "price_estimate": "₹500 – ₹600",
        "dosage_guide": "Apply 2-3 drops to damp face and neck morning and evening. Seal immediately with moisturizer.",
        "side_effects": {
            "common": ["Mild temporary tackiness before fully absorbed"],
            "serious": ["None reported; naturally occurring biocompatible humectant"],
            "management": "Ensure skin is damp before application and follow with a cream to lock in the hydration."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Salicylic Acid 2% BHA Pore-Clearing Serum",
        "purpose": "Unclogs deep congested facial pores, dissolves blackheads and whiteheads, and prevents active acne breakouts.",
        "general_info": "Oil-soluble Beta Hydroxy Acid (BHA) that penetrates deep into sebaceous follicles to dissolve sebum plugs, exfoliate dead skin cells, and calm inflammation.",
        "precautions": [
            "Start by using 2 nights per week to assess tolerance before increasing frequency.",
            "Do not combine on the same evening with Retinol or strong Vitamin C.",
            "Always apply broad-spectrum sunscreen every morning."
        ],
        "avoid_if": [
            "Known allergy to salicylates or aspirin.",
            "Active eczema flares or sunburned facial skin."
        ],
        "safety_note": "Highly effective dermatological treatment for blackheads, whiteheads, and comedonal acne.",
        "search_term": "Minimalist Salicylic Acid 2% Serum",
        "price_estimate": "₹500 – ₹550",
        "dosage_guide": "Apply 1 to 2 drops onto targeted T-zone, nose, or breakout areas 2-3 nights per week after cleansing.",
        "side_effects": {
            "common": ["Mild dryness or localized flaking", "Mild purging (temporary breakout) in weeks 1-2 as pores clear"],
            "serious": ["Excessive peeling or chemical burn if overapplied or layered with harsh acids"],
            "management": "Limit use to 2 nights weekly initially. Use a ceramide moisturizer to prevent excessive dryness."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Alpha Arbutin 2% + Kojic Acid Dark Spot & Melasma Serum",
        "purpose": "Fades dark brown patches, melasma, sun spots, and stubborn acne discoloration by safely reducing melanin synthesis.",
        "general_info": "Safe, gentle derivative of hydroquinone that inhibits tyrosinase activity to fade localized hyperpigmentation and uneven pigmentation without bleaching healthy skin.",
        "precautions": [
            "Strict daytime sun protection (SPF 50+) is mandatory as sun exposure can reactivate melanocytes.",
            "Consistent daily use for 6 to 8 weeks is required for noticeable lightening.",
            "Can be safely paired with Niacinamide or Hyaluronic Acid."
        ],
        "avoid_if": [
            "Known hypersensitivity to arbutin.",
            "Pregnancy or breastfeeding without physician clearance."
        ],
        "safety_note": "Safe, non-irritating alternative to harsh prescription bleaching creams for dark facial spots.",
        "search_term": "Minimalist Alpha Arbutin 2% Face Serum",
        "price_estimate": "₹500 – ₹550",
        "dosage_guide": "Apply 2-3 drops morning and evening onto hyperpigmented areas or full face before moisturizing.",
        "side_effects": {
            "common": ["Mild skin dryness", "Slight tingling upon application"],
            "serious": ["Paradoxical hyperpigmentation if exposed to heavy sun without sunscreen"],
            "management": "Wear broad-spectrum sunscreen religiously every single day during and after treatment."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Retinol 0.3% / Granactive Retinoid Anti-Aging & Texture Serum",
        "purpose": "Accelerates cellular skin turnover, stimulates collagen production, reduces fine lines, and refines rough bumpy skin texture.",
        "general_info": "Vitamin A derivative that communicates with skin cells to boost renewal, unclog micro-comedones, and reverse signs of premature photo-aging.",
        "precautions": [
            "Use strictly at NIGHT only; Vitamin A is degraded by sunlight and increases sun sensitivity.",
            "Begin with 'retinol sandwich' technique (moisturizer -> retinol -> moisturizer) 2 nights a week.",
            "Never apply around delicate eye corners or lips without a protective vaseline barrier."
        ],
        "avoid_if": [
            "PREGNANCY or breastfeeding (Vitamin A derivatives are strictly contraindicated).",
            "Acute rosacea or active dermatitis flare-ups."
        ],
        "safety_note": "Clinically proven gold standard anti-aging and skin smoothing molecule. Requires patient introduction.",
        "search_term": "Minimalist Retinol 0.3% Anti Aging Face Serum",
        "price_estimate": "₹600 – ₹700",
        "dosage_guide": "Apply pea-sized amount onto completely dry face at night only, 2-3 times weekly. Follow with night cream.",
        "side_effects": {
            "common": ["Retinization dryness, flakiness, and mild peeling during weeks 2 to 4", "Mild redness"],
            "serious": ["Severe dermatitis or chemical burn if used on wet skin or combined with AHAs/BHAs"],
            "management": "Wait 15 minutes after washing face until skin is bone-dry before applying. Use ceramide cream generously."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Ceramide 0.3% + Bisabolol Skin Barrier Repair Cream",
        "purpose": "Heals damaged, burning, red, or peeling facial skin barrier, prevents moisture loss, and calms sensitivity.",
        "general_info": "Biomimetic barrier cream formulated with essential ceramides (EOP, NP, AP), cholesterol, and soothing German Chamomile Bisabolol to repair the lipid matrix of irritated skin.",
        "precautions": [
            "Essential after using chemical exfoliants, retinol, or experiencing weather-induced dry patches.",
            "Can be applied multiple times a day as needed.",
            "Non-comedogenic and fragrance-free."
        ],
        "avoid_if": [
            "Known allergy to bisabolol or botanical extracts."
        ],
        "safety_note": "The ultimate dermatological reset cream when the skin barrier is damaged, stinging, or peeling.",
        "search_term": "Minimalist Ceramide Moisturizer",
        "price_estimate": "₹550 – ₹650",
        "dosage_guide": "Apply generously over face and neck as the final skincare step in morning and evening.",
        "side_effects": {
            "common": ["Rich protective layer feeling"],
            "serious": ["Extremely safe with zero common adverse reactions"],
            "management": "Use morning and night. Can be applied generously as an overnight repair sleeping mask."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Caffeine 5% + Peptides Under-Eye Dark Circle Serum",
        "purpose": "Reduces stubborn dark under-eye circles, constricts dilated capillaries, and diminishes morning puffy eye bags.",
        "general_info": "Targeted ocular serum with 5% high-solubility caffeine and EGCG green tea extract that promotes lymphatic drainage and relieves fluid accumulation under the eyes.",
        "precautions": [
            "Apply strictly to orbital bone (eye socket boundary); do not get directly into eyeball.",
            "If under-eye dark circles are due to genetic bone structure or fat loss, topical caffeine will provide supportive drainage only."
        ],
        "avoid_if": [
            "Known sensitivity to topical caffeine.",
            "Conjunctivitis or active eye infection."
        ],
        "safety_note": "Excellent supportive serum for fatigue-induced dark circles and morning puffy eye swelling.",
        "search_term": "Minimalist Caffeine 5% Under Eye Serum",
        "price_estimate": "₹550 – ₹600",
        "dosage_guide": "Dispense 1 drop onto ring finger and gently tap along under-eye bone morning and night.",
        "side_effects": {
            "common": ["Mild temporary skin tightness around under-eye area"],
            "serious": ["Eye stinging if accidentally introduced into the conjunctival sac"],
            "management": "Flush with sterile water if it gets into eyes. Follow with a gentle under-eye moisturizer."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Broad Spectrum SPF 50+ PA++++ Fluid Sunscreen",
        "purpose": "Shields facial skin from UVA/UVB rays, prevents tanning, prevents dark spot darkening, and halts premature photo-aging.",
        "general_info": "Next-generation lightweight, non-greasy sunscreen with Tinosorb M and Uvinul filters providing maximum broad-spectrum UV protection without leaving a white cast.",
        "precautions": [
            "Apply 15 to 20 minutes before stepping into outdoor daylight.",
            "Reapply every 2 to 3 hours during continuous sun exposure or sweating.",
            "Essential daily companion for anyone using active serums (Vitamin C, Retinol, Niacinamide, AHA/BHA)."
        ],
        "avoid_if": [
            "Known allergy to specific chemical UV filters (switch to physical zinc oxide sunscreen if allergic)."
        ],
        "safety_note": "The single most important anti-aging and facial health product recommended by all dermatologists worldwide.",
        "search_term": "Derma Co 1% Hyaluronic Sunscreen SPF 50",
        "price_estimate": "₹450 – ₹550",
        "dosage_guide": "Apply 2 full finger lengths of sunscreen across face, ears, and neck every single morning.",
        "side_effects": {
            "common": ["Mild eye stinging if rubbed into eyes", "Requires evening cleansing to wash off completely"],
            "serious": ["Allergic contact dermatitis to specific UV filters (rare)"],
            "management": "Wash face at night with a gentle foaming cleanser to keep pores clear."
        },
        "otc_status": "100% Non-Prescription Dermatological OTC"
    },
    {
        "name": "Vitamin D3 & B12 Diagnostic Deficiency Blood Test Panel",
        "purpose": "Clinically detects underlying Vitamin D and B12 deficiencies that cause chronic dullness, dark circles, and impaired skin immunity.",
        "general_info": "Comprehensive diagnostic blood checkup measuring 25-Hydroxy Vitamin D and Serum Cobalamin (B12). Deficiencies in these vitamins directly impair skin cell proliferation, wound healing, and collagen repair.",
        "precautions": [
            "Overnight fasting (8 to 10 hours) is recommended before sample collection.",
            "Certified phlebotomist collects venous blood sample conveniently at your home.",
            "Digital diagnostic report generated within 12 to 24 hours."
        ],
        "avoid_if": [
            "Severe active phlebitis at the puncture site."
        ],
        "safety_note": "Recommended diagnostic checkup if experiencing persistent dull skin, dark under-eye circles, fatigue, or unexplainable hair thinning.",
        "search_term": "Vitamin D and B12 Test Tata 1mg Labs",
        "price_estimate": "₹700 – ₹1200",
        "dosage_guide": "Diagnostic blood test. Order online for home sample collection; consult doctor with lab results.",
        "side_effects": {
            "common": ["Minor momentary pinprick at needle insertion site", "Small temporary bruise"],
            "serious": ["None; safe routine diagnostic venipuncture"],
            "management": "Press sterile cotton pad over puncture site for 3 minutes after collection."
        },
        "otc_status": "Diagnostic Blood Test (Direct Home Collection)"
    },
    {
        "name": "Serum Iron & Ferritin Anemia Profile Test",
        "purpose": "Tests for latent iron deficiency that causes pale lifeless facial complexion, extreme fatigue, and severe dark circles.",
        "general_info": "Complete diagnostic profile measuring Serum Ferritin, Serum Iron, and Total Iron Binding Capacity (TIBC) to diagnose cellular iron depletion before full anemia sets in.",
        "precautions": [
            "Morning sample preferred as iron levels fluctuate diurnally.",
            "Inform phlebotomist if currently taking oral iron supplements."
        ],
        "avoid_if": [
            "Bleeding disorders without informing phlebotomist."
        ],
        "safety_note": "Crucial diagnostic checkup for pale skin, sallow yellowish complexion, chronic fatigue, and brittle nails.",
        "search_term": "Iron Deficiency Ferritin Test Apollo Diagnostics",
        "price_estimate": "₹500 – ₹900",
        "dosage_guide": "Home sample diagnostic blood draw. Report available in 12 hours.",
        "side_effects": {
            "common": ["Minor temporary skin prick discomfort"],
            "serious": ["None"],
            "management": "Keep arm straight for a few minutes after blood draw."
        },
        "otc_status": "Diagnostic Blood Test (Direct Home Collection)"
    },
    {
        "name": "Serum Zinc & Micronutrient Health Checkup",
        "purpose": "Identifies zinc deficiency responsible for stubborn inflammatory facial acne, delayed healing of spots, and skin inflammation.",
        "general_info": "Diagnostic blood test measuring Serum Zinc levels. Zinc is a vital cofactor for over 300 enzymes, regulating immune defense and skin epithelial repair.",
        "precautions": [
            "Fasting sample recommended.",
            "Avoid taking zinc supplements 24 hours prior to blood test to get accurate baseline."
        ],
        "avoid_if": [
            "None"
        ],
        "safety_note": "Essential checkup for persistent, cystic, non-healing adult acne and repeated skin infections.",
        "search_term": "Zinc Test Tata 1mg Labs",
        "price_estimate": "₹650 – ₹1100",
        "dosage_guide": "Routine diagnostic venipuncture with home collection.",
        "side_effects": {
            "common": ["Minor momentary pinprick"],
            "serious": ["None"],
            "management": "Rest arm comfortably after draw."
        },
        "otc_status": "Diagnostic Blood Test (Direct Home Collection)"
    }
]


def add_facial_care():
    print(f"Loading {KB_PATH}...")
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)

    categories = kb_data.get('categories', {})
    categories['facial_care'] = FACIAL_CARE_PRODUCTS
    kb_data['categories'] = categories

    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(kb_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Added 'facial_care' with {len(FACIAL_CARE_PRODUCTS)} products to local {KB_PATH}")

    # Now sync into local laptop SQLite DB
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Ensure facial_care items are inserted/updated
        for item in FACIAL_CARE_PRODUCTS:
            cur.execute("SELECT id FROM medicines WHERE name = ?", (item['name'],))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE medicines
                    SET category = 'facial_care', purpose = ?, general_info = ?, precautions = ?,
                        avoid_if = ?, safety_note = ?, side_effects = ?, dosage_guide = ?,
                        price_estimate = ?, search_term = ?, otc_status = ?
                    WHERE id = ?
                """, (
                    item['purpose'],
                    item['general_info'],
                    json.dumps(item['precautions']),
                    json.dumps(item['avoid_if']),
                    item['safety_note'],
                    json.dumps(item['side_effects']),
                    item['dosage_guide'],
                    item['price_estimate'],
                    item['search_term'],
                    item['otc_status'],
                    row[0]
                ))
            else:
                cur.execute("""
                    INSERT INTO medicines (category, name, purpose, general_info, precautions, avoid_if, safety_note, side_effects, dosage_guide, price_estimate, search_term, otc_status)
                    VALUES ('facial_care', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item['name'],
                    item['purpose'],
                    item['general_info'],
                    json.dumps(item['precautions']),
                    json.dumps(item['avoid_if']),
                    item['safety_note'],
                    json.dumps(item['side_effects']),
                    item['dosage_guide'],
                    item['price_estimate'],
                    item['search_term'],
                    item['otc_status']
                ))
        conn.commit()
        conn.close()
        print(f"[OK] Synced {len(FACIAL_CARE_PRODUCTS)} facial care & test products into local SQLite database ({DB_PATH}).")

if __name__ == '__main__':
    add_facial_care()
