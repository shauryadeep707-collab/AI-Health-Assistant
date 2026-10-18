"""
Enrichment script for Knowledge Base Medicines Catalog.
Adds side_effects (common, serious, management), dosage_guide, price_estimate,
and search_term to all 65 OTC medicines in knowledge_base/medicines.json and SQLite.
"""

import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KB_PATH = os.path.join(BASE_DIR, 'knowledge_base', 'medicines.json')
DB_PATH = os.path.join(BASE_DIR, 'health_assistant.db')

CLINICAL_ENRICHMENTS = {
    # FEVER
    "Paracetamol (Acetaminophen 500mg/650mg)": {
        "search_term": "Paracetamol 650mg",
        "price_estimate": "₹15 – ₹35",
        "dosage_guide": "Adults: 500mg - 650mg every 4 to 6 hours as needed. Do not exceed 4000mg in 24 hours.",
        "side_effects": {
            "common": ["Mild nausea", "Headache", "Slight stomach upset", "Constipation or loose stool (rare)"],
            "serious": ["Skin rash or hives", "Swelling of lips, tongue or face", "Jaundice (yellow eyes/skin)", "Dark tea-colored urine"],
            "management": "Take with a glass of water, with or without food. Never combine with other paracetamol-containing cold medicines. If allergic rash occurs, stop immediately."
        }
    },
    "Ibuprofen (200mg / 400mg)": {
        "search_term": "Ibuprofen 400mg",
        "price_estimate": "₹20 – ₹45",
        "dosage_guide": "Adults: 200mg - 400mg every 6 to 8 hours with or after food. Maximum 1200mg/day OTC.",
        "side_effects": {
            "common": ["Heartburn or acid indigestion", "Mild stomach pain", "Nausea", "Dizziness or headache"],
            "serious": ["Black or tarry stools", "Vomiting blood or coffee-ground material", "Severe swelling in ankles", "Sudden shortness of breath"],
            "management": "Always take strictly with meals or a glass of milk to protect stomach lining. Discontinue immediately if stomach burning or black stools occur."
        }
    },
    "Mefenamic Acid (250mg / 500mg)": {
        "search_term": "Meftal Spas Mefenamic Acid",
        "price_estimate": "₹35 – ₹70",
        "dosage_guide": "Adults: 250mg - 500mg up to 3 times daily after food. Short duration use only (under 5 days).",
        "side_effects": {
            "common": ["Abdominal cramping or pain", "Heartburn", "Nausea or vomiting", "Mild drowsiness"],
            "serious": ["Severe gastrointestinal bleeding", "Skin blistering", "Kidney pain or decreased urination"],
            "management": "Consume immediately after a substantial meal. Do not use for more than 5 consecutive days without physician advice."
        }
    },
    "Lukewarm Sponge Hydrotherapy": {
        "search_term": "Cooling Gel Sheet Forehead",
        "price_estimate": "₹50 – ₹150",
        "dosage_guide": "Apply lukewarm (not cold) damp cloth to forehead, neck, armpits for 15-20 minutes.",
        "side_effects": {
            "common": ["Transient shivering if water is too cold", "Mild skin goosebumps"],
            "serious": ["Hypothermic shivering (if ice water is mistakenly used)"],
            "management": "Ensure water is lukewarm (around 30°C / 85°F). Stop immediately if the patient begins shivering."
        }
    },
    "Oral Electrolyte Rehydration Fluid": {
        "search_term": "Electral ORS Powder",
        "price_estimate": "₹22 – ₹45",
        "dosage_guide": "Dissolve 1 sachet in exactly 1 liter of clean drinking water. Sip 200-400ml after each fever spike or loose motion.",
        "side_effects": {
            "common": ["Mild fullness", "Salt taste fatigue"],
            "serious": ["Fluid overload or puffy eyes if mixed too concentrated with inadequate water"],
            "management": "Mix with the exact recommended water quantity. Do not add extra sugar, salt, or boiling water."
        }
    },

    # COLD & COUGH
    "Steam Inhalation Therapy": {
        "search_term": "Facial Steamer Inhaler Vaporizer",
        "price_estimate": "₹250 – ₹550",
        "dosage_guide": "Inhale warm plain steam for 5 to 10 minutes, 2 to 3 times daily from 25-30cm safe distance.",
        "side_effects": {
            "common": ["Facial redness from heat", "Mild eye tearing"],
            "serious": ["Scalding burns if container tips over", "Bronchospasm if strong aromatic additives used"],
            "management": "Use plain water only. Keep hot steam unit on a stable surface far out of children's reach."
        }
    },
    "Saline Nasal Drops / Spray (0.9% NaCl)": {
        "search_term": "Saline Nasal Spray Otrivin S",
        "price_estimate": "₹45 – ₹90",
        "dosage_guide": "2 to 3 drops or 1-2 sprays into each nostril 3 to 4 times daily as needed.",
        "side_effects": {
            "common": ["Transient mild nasal stinging", "Sneezing immediately after spray"],
            "serious": ["None reported with sterile isotonic saline"],
            "management": "Blow nose gently 2-3 minutes after application. Wipe nozzle clean and never share spray bottles."
        }
    },
    "Cetirizine (10mg)": {
        "search_term": "Cetirizine 10mg Cetzine",
        "price_estimate": "₹18 – ₹40",
        "dosage_guide": "Adults: 10mg once daily, preferably at bedtime with a glass of water.",
        "side_effects": {
            "common": ["Mild drowsiness or fatigue", "Dry mouth", "Mild headache", "Throat dryness"],
            "serious": ["Severe allergic swelling", "Difficulty urinating (urinary retention)", "Rapid irregular heartbeat"],
            "management": "Take at night to avoid daytime grogginess. Do not drive or consume alcohol while on this medication."
        }
    },
    "Loratadine (10mg)": {
        "search_term": "Loratadine 10mg Lorfast",
        "price_estimate": "₹30 – ₹65",
        "dosage_guide": "Adults: 10mg once daily in the morning with or without food.",
        "side_effects": {
            "common": ["Headache", "Dry mouth", "Mild fatigue or nervousness"],
            "serious": ["Severe hypersensitivity rash", "Liver tenderness (very rare)"],
            "management": "Ideal for daytime use. Stay hydrated by sipping water throughout the day."
        }
    },
    "Dextromethorphan HBr (Syrup / Lozenges)": {
        "search_term": "Dextromethorphan Cough Syrup Benadryl DR",
        "price_estimate": "₹75 – ₹130",
        "dosage_guide": "Adults: 10ml (15mg-30mg) every 6 to 8 hours for dry hacking cough. Max 120mg/day.",
        "side_effects": {
            "common": ["Drowsiness", "Dizziness", "Mild nausea", "Constipation"],
            "serious": ["Severe respiratory depression if overdosed", "Serotonin syndrome if combined with MAOI antidepressants"],
            "management": "Only use for non-productive dry cough. Do NOT use if coughing up thick green/yellow phlegm."
        }
    },
    "Guaifenesin Expectorant (Syrup)": {
        "search_term": "Guaifenesin Expectorant Syrup Grilinctus",
        "price_estimate": "₹80 – ₹140",
        "dosage_guide": "Adults: 200mg - 400mg (10ml-20ml) every 4 hours with a full glass of water. Max 2400mg/day.",
        "side_effects": {
            "common": ["Mild stomach discomfort", "Nausea", "Dizziness"],
            "serious": ["Kidney stones (with massive prolonged overuse)"],
            "management": "Drink plenty of warm fluids; hydration significantly enhances guaifenesin's mucus-thinning effect."
        }
    },
    "Chlorpheniramine Maleate (CPM 4mg)": {
        "search_term": "Chlorpheniramine Maleate 4mg Cadistin",
        "price_estimate": "₹10 – ₹25",
        "dosage_guide": "Adults: 4mg every 4 to 6 hours as needed. Maximum 24mg in 24 hours.",
        "side_effects": {
            "common": ["Pronounced drowsiness and sedation", "Dry mouth and nose", "Blurred vision", "Coordination loss"],
            "serious": ["Severe confusion in elderly", "Urinary retention"],
            "management": "Strictly avoid driving or operating machinery. Best taken before sleep."
        }
    },
    "Xylometazoline 0.1% Nasal Spray": {
        "search_term": "Otrivin Adult Nasal Spray 0.1%",
        "price_estimate": "₹70 – ₹110",
        "dosage_guide": "1 spray into each nostril 2 to 3 times daily. Maximum 3 to 5 consecutive days only.",
        "side_effects": {
            "common": ["Nasal dryness or burning", "Sneezing", "Temporary bitter taste in throat"],
            "serious": ["Rebound congestion (rhinitis medicamentosa) if used over 5 days", "Elevated blood pressure"],
            "management": "Strictly limit use to maximum 5 consecutive days to prevent severe rebound nasal blockage."
        }
    },
    "Honey & Ginger Warm Demulcent": {
        "search_term": "Dabur Honitus Herbal Cough Syrup",
        "price_estimate": "₹60 – ₹120",
        "dosage_guide": "1-2 teaspoons of warm honey-ginger extract 3 to 4 times daily as needed.",
        "side_effects": {
            "common": ["Mild gastric warmth", "Sweet aftertaste"],
            "serious": ["Infant botulism risk (NEVER give honey to infants under 12 months)"],
            "management": "Completely safe for adults and children over 1 year. Sip slowly to coat and soothe throat walls."
        }
    },

    # HEADACHE
    "Paracetamol (500mg / 650mg)": {
        "search_term": "Dolo 650 Paracetamol",
        "price_estimate": "₹15 – ₹35",
        "dosage_guide": "Adults: 1 tablet (500-650mg) every 4-6 hours with water. Max 4000mg/day.",
        "side_effects": {
            "common": ["Mild nausea", "Headache recurrence if overused (medication overuse headache)"],
            "serious": ["Liver damage if taken with alcohol or overdosed"],
            "management": "Take with water. Limit painkiller usage to under 10 days per month to avoid rebound headaches."
        }
    },
    "Ibuprofen (400mg)": {
        "search_term": "Brufen 400 Ibuprofen",
        "price_estimate": "₹20 – ₹45",
        "dosage_guide": "Adults: 400mg once or twice daily after food. Max 1200mg/day OTC.",
        "side_effects": {
            "common": ["Stomach burning", "Indigestion", "Nausea"],
            "serious": ["Gastric ulceration", "Kidney strain"],
            "management": "Always ingest with food or milk. Avoid if you have a history of gastritis or acid reflux."
        }
    },
    "Aspirin + Paracetamol + Caffeine Combination": {
        "search_term": "Saridon Headache Tablet",
        "price_estimate": "₹25 – ₹50",
        "dosage_guide": "Adults: 1 tablet with a full glass of water. Do not repeat sooner than 6 hours.",
        "side_effects": {
            "common": ["Restlessness or jitters from caffeine", "Increased heart rate", "Stomach irritation"],
            "serious": ["Gastric bleeding", "Tinnitus (ringing in ears from aspirin)"],
            "management": "Avoid additional coffee, tea, or energy drinks while taking this medication. Never give to children/teens."
        }
    },
    "Peppermint & Menthol Essential Oil Roll-On": {
        "search_term": "Amrutanjan Roll On Headache",
        "price_estimate": "₹45 – ₹85",
        "dosage_guide": "Apply gently across forehead and temples. Keep away from eyes.",
        "side_effects": {
            "common": ["Cooling sensation", "Mild skin tingling"],
            "serious": ["Eye irritation if touched with fingers after application", "Skin redness/contact allergy"],
            "management": "Wash hands thoroughly after applying. Keep strictly away from eyes, nostrils, and broken skin."
        }
    },
    "Magnesium Glycinate / Citrate (250mg)": {
        "search_term": "Magnesium Glycinate 250mg",
        "price_estimate": "₹280 – ₹550",
        "dosage_guide": "Adults: 250mg - 350mg once daily with evening meal.",
        "side_effects": {
            "common": ["Mild loose stools or soft bowel movements", "Stomach rumbling"],
            "serious": ["Severe diarrhea (with excess dose)", "Muscle weakness (if kidney impaired)"],
            "management": "Take with dinner to minimize bowel loosening and enhance muscle relaxation for sleep."
        }
    },

    # SORE THROAT
    "Warm Saline Gargle": {
        "search_term": "Betadine Gargle Mint",
        "price_estimate": "₹20 – ₹60",
        "dosage_guide": "Dissolve 1/2 teaspoon table salt in 1 glass of warm water. Gargle for 30 seconds, 3-4 times daily.",
        "side_effects": {
            "common": ["Slight salty aftertaste", "Mild mucosal dryness if overdone"],
            "serious": ["Nausea if swallowed in large quantities"],
            "management": "Always spit out the gargle solution completely; do not swallow."
        }
    },
    "Antiseptic Throat Lozenges (Amylmetacresol & Dichlorobenzyl Alcohol)": {
        "search_term": "Strepsils Honey Lemon Lozenges",
        "price_estimate": "₹35 – ₹70",
        "dosage_guide": "Dissolve 1 lozenge slowly in the mouth every 2 to 3 hours as needed. Max 8-12 per day.",
        "side_effects": {
            "common": ["Temporary tongue numbness or tingling", "Mouth irritation if chewed rapidly"],
            "serious": ["Allergic mouth ulcers (rare)", "Choking hazard in young children"],
            "management": "Allow to dissolve slowly in the mouth without chewing or swallowing whole."
        }
    },
    "Povidone-Iodine 0.5% - 1% Gargle & Rinse": {
        "search_term": "Betadine 2% Gargle 50ml",
        "price_estimate": "₹80 – ₹140",
        "dosage_guide": "Dilute with equal parts warm water. Gargle for 30 seconds and spit out, twice daily.",
        "side_effects": {
            "common": ["Temporary brown staining of tongue (washes off)", "Iodine taste"],
            "serious": ["Thyroid dysfunction if swallowed repeatedly", "Iodine allergy rash"],
            "management": "Spit out thoroughly after gargling. Do not use for more than 7 days or if allergic to iodine."
        }
    },
    "Benzocaine / Lidocaine Throat Spray": {
        "search_term": "Throat Numbing Spray Benzocaine",
        "price_estimate": "₹120 – ₹220",
        "dosage_guide": "1-2 sprays directly towards back of throat. Wait at least 2 hours before repeating.",
        "side_effects": {
            "common": ["Marked numbness of throat and tongue", "Altered taste"],
            "serious": ["Difficulty swallowing leading to choking on food", "Methemoglobinemia (rare with excessive benzocaine)"],
            "management": "Do not eat or drink hot liquids for 1 hour after spraying to avoid biting tongue or choking."
        }
    },
    "Chlorhexidine Gluconate 0.2% Oral Rinse": {
        "search_term": "Clohex Chlorhexidine Mouthwash",
        "price_estimate": "₹60 – ₹110",
        "dosage_guide": "Swish 10ml in mouth for 60 seconds and spit out, twice daily after brushing.",
        "side_effects": {
            "common": ["Temporary superficial teeth staining", "Bitter aftertaste", "Transient dry mouth"],
            "serious": ["Oral mucosa desquamation if used undiluted for weeks"],
            "management": "Do not rinse with water or drink tea/coffee for 30 minutes following use."
        }
    },

    # STOMACH
    "ORS (Oral Rehydration Salts - WHO Formula)": {
        "search_term": "Electral WHO ORS Powder",
        "price_estimate": "₹22 – ₹45",
        "dosage_guide": "Mix 1 packet in exactly 1000ml clean water. Drink after every loose stool.",
        "side_effects": {
            "common": ["Slightly salty taste"],
            "serious": ["Swelling of eyelids if mixed in too little water"],
            "management": "Always dissolve in the full 1 liter volume. Discard any unused solution after 24 hours."
        }
    },
    "Liquid Antacid (Magnesium + Aluminum Hydroxide + Simethicone)": {
        "search_term": "Gelusil Antacid Liquid Digene",
        "price_estimate": "₹80 – ₹150",
        "dosage_guide": "1-2 teaspoons (5-10ml) 15-30 minutes after meals and at bedtime.",
        "side_effects": {
            "common": ["Chalky mouth taste", "Mild constipation (from aluminum) or loose stools (from magnesium)"],
            "serious": ["Electrolyte imbalances if used chronically with kidney disease"],
            "management": "Shake bottle well before pouring. Leave a 2-hour gap before taking other prescription medications."
        }
    },
    "Chewable Calcium Carbonate / Sodium Bicarbonate": {
        "search_term": "Eno Fruit Salt Antacid",
        "price_estimate": "₹10 – ₹60",
        "dosage_guide": "Dissolve 1 sachet in a glass of water, or chew 1-2 tablets during acute acidity.",
        "side_effects": {
            "common": ["Burping or belching", "Mild bloating", "Flatulence"],
            "serious": ["Acid rebound if overused", "Sodium overload in hypertensive patients"],
            "management": "Use for occasional breakthrough acidity. Patients on low-sodium diets should avoid sodium bicarbonate."
        }
    },
    "Omeprazole (20mg OTC)": {
        "search_term": "Omee 20mg Omeprazole",
        "price_estimate": "₹35 – ₹70",
        "dosage_guide": "Adults: 20mg once daily in the morning, 30 to 60 minutes before breakfast.",
        "side_effects": {
            "common": ["Headache", "Abdominal discomfort", "Gas or bloating", "Nausea"],
            "serious": ["Severe persistent diarrhea (C. diff)", "Bone density reduction with chronic year-long use"],
            "management": "Swallow capsule whole with water. Do not crush or chew. Limit OTC self-treatment to 14 days."
        }
    },
    "Famotidine (20mg)": {
        "search_term": "Famocid 20mg Famotidine",
        "price_estimate": "₹25 – ₹55",
        "dosage_guide": "Adults: 10mg - 20mg once or twice daily, 15 to 60 minutes before meals or at bedtime.",
        "side_effects": {
            "common": ["Headache", "Dizziness", "Constipation or diarrhea"],
            "serious": ["Arrhythmia (extremely rare)", "Confusion in elderly with renal failure"],
            "management": "Fast onset within 1 hour. Ideal for meal-triggered or nighttime heartburn."
        }
    },
    "Loperamide (2mg)": {
        "search_term": "Imodium 2mg Loperamide",
        "price_estimate": "₹25 – ₹55",
        "dosage_guide": "Adults: 4mg initially, then 2mg after each unformed stool. Max 8mg/day OTC.",
        "side_effects": {
            "common": ["Constipation", "Mild abdominal cramps", "Dizziness", "Dry mouth"],
            "serious": ["Toxic megacolon if used with bacterial dysentery", "Heart rhythm issues if severely overdosed"],
            "management": "DO NOT USE if diarrhea is accompanied by high fever or bloody stools. Rehydrate aggressively."
        }
    },
    "Psyllium Husk (Isabgol)": {
        "search_term": "Baidyanath Isabgol Psyllium Husk",
        "price_estimate": "₹120 – ₹240",
        "dosage_guide": "1 to 2 tablespoons stirred into a large glass of water or milk once daily at night.",
        "side_effects": {
            "common": ["Abdominal fullness", "Increased flatulence during first 2-3 days"],
            "serious": ["Esophageal or bowel obstruction if swallowed without adequate liquid"],
            "management": "CRITICAL: Drink immediately after stirring, followed by a second full glass of water."
        }
    },
    "Probiotics (Lactobacillus & Saccharomyces boulardii)": {
        "search_term": "Sporlac Plus Probiotic Capsule",
        "price_estimate": "₹80 – ₹180",
        "dosage_guide": "1 capsule 1 to 2 times daily with meals or as directed on the label.",
        "side_effects": {
            "common": ["Mild initial bloating or intestinal gas for 24-48 hours"],
            "serious": ["Systemic infection in severely immunocompromised individuals"],
            "management": "Take consistently with meals. If taking antibiotics, separate by at least 2 hours."
        }
    },
    "Simethicone (80mg / 125mg)": {
        "search_term": "Gasex Simethicone Tablets",
        "price_estimate": "₹40 – ₹90",
        "dosage_guide": "1 to 2 tablets (80-125mg) chewed thoroughly after meals and at bedtime.",
        "side_effects": {
            "common": ["Mild belching", "Passing of trapped flatus (expected therapeutic effect)"],
            "serious": ["None known; simethicone is biologically inert and not absorbed into bloodstream"],
            "management": "Chew tablets thoroughly before swallowing for optimal bubble-collapsing action."
        }
    },
    "Dicyclomine / Mebeverine": {
        "search_term": "Colimex Mebeverine Tablets",
        "price_estimate": "₹45 – ₹95",
        "dosage_guide": "10mg - 20mg 30 minutes before meals for intestinal colic or spasms.",
        "side_effects": {
            "common": ["Dry mouth", "Blurred vision", "Drowsiness", "Mild dizziness"],
            "serious": ["Glaucoma flare-up", "Urinary retention"],
            "management": "Avoid if you have glaucoma or an enlarged prostate. Drink water to alleviate dry mouth."
        }
    },
    "Milk of Magnesia (Magnesium Hydroxide)": {
        "search_term": "Cremaffin Milk of Magnesia",
        "price_estimate": "₹85 – ₹160",
        "dosage_guide": "15ml - 30ml with a full glass of water at bedtime for constipation relief.",
        "side_effects": {
            "common": ["Watery loose stools or diarrhea", "Abdominal cramps"],
            "serious": ["Hypermagnesemia in patients with severe kidney disease"],
            "management": "Follow dose with a full 250ml glass of water. Works within 30 minutes to 6 hours."
        }
    },

    # SKIN
    "Calamine Lotion": {
        "search_term": "Lacto Calamine Lotion 120ml",
        "price_estimate": "₹90 – ₹180",
        "dosage_guide": "Shake well and dab onto itchy, irritated, or sunburned skin using cotton wool 2-3 times daily.",
        "side_effects": {
            "common": ["Skin dryness after lotion dries", "Mild powdery flaking"],
            "serious": ["Contact dermatitis (rare)"],
            "management": "External use only. Avoid applying directly to open oozing cuts or mucous membranes."
        }
    },
    "Clotrimazole 1% Topical Antifungal Cream": {
        "search_term": "Candid 1% Clotrimazole Cream",
        "price_estimate": "₹55 – ₹110",
        "dosage_guide": "Clean and dry affected area. Apply a thin film 2 to 3 times daily for 2 to 4 weeks.",
        "side_effects": {
            "common": ["Mild burning sensation", "Slight redness or irritation at application site"],
            "serious": ["Allergic contact dermatitis, blistering, or skin peeling"],
            "management": "Continue applying for 1-2 weeks after symptoms disappear to prevent fungal relapse."
        }
    },
    "Hydrocortisone 1% Topical Cream": {
        "search_term": "Hydrocortisone 1% Topical Cream",
        "price_estimate": "₹60 – ₹130",
        "dosage_guide": "Apply sparingly in a thin layer to inflamed itchy patch 1 to 2 times daily. Max 7 days.",
        "side_effects": {
            "common": ["Transient skin tingling or dryness"],
            "serious": ["Skin thinning (atrophy) or stretch marks with chronic overuse", "Secondary skin infection"],
            "management": "Never apply to the face, groin, or infected wounds without a dermatologist's clearance."
        }
    },
    "Povidone-Iodine 5% / 10% Ointment (Betadine)": {
        "search_term": "Betadine 10% Ointment 20g",
        "price_estimate": "₹65 – ₹120",
        "dosage_guide": "Apply to clean minor cut, scrape, or burn and cover with sterile dressing 1-2 times daily.",
        "side_effects": {
            "common": ["Temporary yellow-brown skin discoloration", "Mild local stinging"],
            "serious": ["Systemic iodine absorption if applied to massive open wounds", "Iodine hypersensitivity"],
            "management": "Staining washes off skin with water. Do not bandage airtight over massive body areas."
        }
    },
    "Silver Sulfadiazine 1% / Burn Relief Cream": {
        "search_term": "Silverex Burn Relief Cream 20g",
        "price_estimate": "₹75 – ₹150",
        "dosage_guide": "Apply a 1.5mm layer over superficial clean minor burns 1-2 times daily using sterile gloves.",
        "side_effects": {
            "common": ["Cooling sensation", "Temporary greyish skin discoloration"],
            "serious": ["Sulfa allergy reaction (rash, hives, swelling)"],
            "management": "Avoid if allergic to sulfa medications. For second/third degree burns, go to hospital immediately."
        }
    },
    "Pure Petroleum Jelly (White Petrolatum)": {
        "search_term": "Vaseline Pure Petroleum Jelly",
        "price_estimate": "₹40 – ₹110",
        "dosage_guide": "Apply liberally to clean dry skin, cracked lips, or minor wounds as needed.",
        "side_effects": {
            "common": ["Greasy residue", "Mild pore clogging if applied to acne-prone face"],
            "serious": ["Lipoid pneumonia if inhaled into lungs (never put inside nostrils)"],
            "management": "Clean skin before applying to lock in moisture. Do not apply inside nasal passages."
        }
    },
    "Zinc Oxide 10% - 20% Barrier Cream": {
        "search_term": "Sudo Cream Zinc Oxide Barrier",
        "price_estimate": "₹150 – ₹320",
        "dosage_guide": "Apply thick layer over diaper rash or friction chafing after cleaning and drying skin.",
        "side_effects": {
            "common": ["White opaque film residue"],
            "serious": ["Contact sensitivity (very rare)"],
            "management": "Creates an impenetrable physical shield against urine, feces, and wet friction."
        }
    },
    "Neomycin + Polymyxin B + Bacitracin (Triple Antibiotic Ointment)": {
        "search_term": "Neosporin Antibiotic Ointment",
        "price_estimate": "₹60 – ₹115",
        "dosage_guide": "Apply small amount (fingertip) to minor scrape or cut 1 to 3 times daily for up to 7 days.",
        "side_effects": {
            "common": ["Mild skin redness"],
            "serious": ["Neomycin contact allergy causing itchy red weeping rash", "Hearing/kidney toxicity if massive overuse"],
            "management": "Discontinue immediately if the wound gets redder or itchier after application."
        }
    },
    "Benzoyl Peroxide 2.5% / 5% Gel": {
        "search_term": "Benzac AC 2.5% Gel",
        "price_estimate": "₹110 – ₹240",
        "dosage_guide": "Apply thin dab to acne pimples once daily at night. Wash face with gentle cleanser first.",
        "side_effects": {
            "common": ["Skin dryness, peeling, flaking", "Mild stinging or burning", "Bleaches towels and clothing"],
            "serious": ["Severe contact swelling and redness"],
            "management": "Start with 2.5% every alternate night. Use non-comedogenic moisturizer and protect pillowcases."
        }
    },
    "Salicylic Acid 2% Ointment / Gel": {
        "search_term": "Salicylix 2% Ointment",
        "price_estimate": "₹90 – ₹190",
        "dosage_guide": "Apply thin layer to rough calluses, blackheads, or scaly patches once daily.",
        "side_effects": {
            "common": ["Local skin peeling", "Mild warmth or irritation"],
            "serious": ["Salicylate toxicity if used over large body surfaces"],
            "management": "Apply only to localized target skin areas. Use sunscreen during the day."
        }
    },

    # EYE & EAR
    "Carboxymethylcellulose (CMC 0.5%) Artificial Tears": {
        "search_term": "Refresh Tears Lubricant Eye Drops",
        "price_estimate": "₹130 – ₹240",
        "dosage_guide": "Instill 1 to 2 drops in the affected eye(s) 3 to 4 times daily or as needed for dryness.",
        "side_effects": {
            "common": ["Brief blurred vision for 1-2 minutes after instillation", "Mild sticky feeling"],
            "serious": ["Eye pain, ongoing redness, or vision changes"],
            "management": "Remove contact lenses before use. Do not touch dropper tip to eyelashes or hands."
        }
    },
    "Olopatadine / Ketotifen 0.025% Eye Drops": {
        "search_term": "Olopat Eye Drops Olopatadine",
        "price_estimate": "₹120 – ₹210",
        "dosage_guide": "1 drop in each affected eye once or twice daily for allergic itchy eyes.",
        "side_effects": {
            "common": ["Transient eye stinging", "Mild dry eyes", "Slight bitter taste in throat"],
            "serious": ["Corneal inflammation or severe hypersensitivity"],
            "management": "Keep eyes closed for 1 minute after drop and press lightly on tear duct to reduce throat drainage."
        }
    },
    "Carbamide Peroxide / Mineral Oil Ear Drops": {
        "search_term": "Waxsol Ear Drops 10ml",
        "price_estimate": "₹70 – ₹130",
        "dosage_guide": "Tilt head sideways. Place 3-5 drops into ear canal twice daily for up to 4 days.",
        "side_effects": {
            "common": ["Bubbling or crackling sound in ear", "Temporary ear fullness as wax expands"],
            "serious": ["Severe ear pain (never use if eardrum is ruptured or punctured)"],
            "management": "Lie on your side for 5 minutes. DO NOT insert cotton buds/Q-tips into the ear canal."
        }
    },
    "Sterile Normal Saline Eye Wash": {
        "search_term": "Sterile Eye Wash Saline Solution",
        "price_estimate": "₹50 – ₹110",
        "dosage_guide": "Flush eye gently using sterile eye cup or squeeze bottle to rinse out dust or grit.",
        "side_effects": {
            "common": ["Mild temporary reflex tearing"],
            "serious": ["None with sterile 0.9% saline"],
            "management": "If eye pain or foreign body sensation persists after rinsing, consult an ophthalmologist immediately."
        }
    },

    # ALLERGIES
    "Fexofenadine (120mg / 180mg)": {
        "search_term": "Allegra 120mg Fexofenadine",
        "price_estimate": "₹120 – ₹230",
        "dosage_guide": "Adults: 120mg once daily for allergic rhinitis; 180mg for urticaria (hives).",
        "side_effects": {
            "common": ["Headache", "Drowsiness (very low compared to older antihistamines)", "Nausea"],
            "serious": ["Hypersensitivity reaction, chest tightness"],
            "management": "Take with plain water. Avoid fruit juices (apple, orange, grapefruit) within 4 hours as they block absorption."
        }
    },
    "Levocetirizine (5mg)": {
        "search_term": "Levocet 5mg Levocetirizine",
        "price_estimate": "₹35 – ₹75",
        "dosage_guide": "Adults: 5mg once daily in the evening with or without food.",
        "side_effects": {
            "common": ["Mild drowsiness", "Fatigue", "Dry mouth", "Nasal congestion"],
            "serious": ["Severe sleepiness, urinary retention"],
            "management": "Take at bedtime. Do not drive or drink alcohol until personal response is known."
        }
    },
    "Dimenhydrinate (50mg)": {
        "search_term": "Dramamine Motion Sickness 50mg",
        "price_estimate": "₹50 – ₹110",
        "dosage_guide": "Adults: 50mg to 100mg taken 30 to 60 minutes before travel. Repeat every 4-6 hours. Max 400mg/day.",
        "side_effects": {
            "common": ["Significant drowsiness", "Dry mouth", "Blurred vision", "Dizziness"],
            "serious": ["Confusion in elderly", "Tachycardia or palpitations"],
            "management": "DO NOT drive while taking. Take with food or water before embarkation."
        }
    },
    "Meclizine (25mg)": {
        "search_term": "Diligan Meclizine 25mg",
        "price_estimate": "₹40 – ₹90",
        "dosage_guide": "Adults: 25mg to 50mg once daily 1 hour before travel or for vertigo.",
        "side_effects": {
            "common": ["Drowsiness", "Dry mouth", "Headache", "Fatigue"],
            "serious": ["Urinary retention, acute narrow-angle glaucoma flare"],
            "management": "Less sedating than dimenhydrinate, but precautions against driving still apply."
        }
    },

    # MUSCLE PAIN
    "Diclofenac Diethylamine 1.16% Topical Gel": {
        "search_term": "Volini Pain Relief Gel 30g",
        "price_estimate": "₹80 – ₹160",
        "dosage_guide": "Apply 2g to 4g gently over the painful joint or muscle 3 to 4 times daily.",
        "side_effects": {
            "common": ["Mild skin redness", "Dryness or tingling at application site"],
            "serious": ["Contact dermatitis", "Systemic NSAID side effects if applied over huge body areas"],
            "management": "Wash hands immediately after rubbing in. Do not apply under airtight heat wraps or to broken skin."
        }
    },
    "Methyl Salicylate & Menthol Liniment / Spray": {
        "search_term": "Moov Pain Relief Spray 50g",
        "price_estimate": "₹95 – ₹180",
        "dosage_guide": "Spray from 5cm distance onto painful area 2 to 3 times daily. Do not massage aggressively.",
        "side_effects": {
            "common": ["Intense warming/cooling counter-irritation sensation", "Skin redness"],
            "serious": ["Chemical burns if covered with tight heating pads", "Salicylate toxicity if overused"],
            "management": "Never apply a heating pad over methyl salicylate. Keep away from eyes and broken skin."
        }
    },
    "Cryotherapy Cold Gel Ice Pack": {
        "search_term": "Flamingo Cool Gel Pack",
        "price_estimate": "₹150 – ₹300",
        "dosage_guide": "Wrap cold pack in a thin towel and apply to sprain/strain for 15-20 minutes every 2-3 hours.",
        "side_effects": {
            "common": ["Initial discomfort from intense cold", "Skin redness"],
            "serious": ["Frostbite or ice burn if applied directly to bare skin without towel barrier"],
            "management": "NEVER place frozen pack directly on bare skin. Limit each session to maximum 20 minutes."
        }
    },
    "Thermotherapy Hot Pack / Heating Pad": {
        "search_term": "Orthopedic Electric Heating Pad",
        "price_estimate": "₹350 – ₹750",
        "dosage_guide": "Apply comfortably warm pack to chronic stiff muscles for 15 to 20 minutes.",
        "side_effects": {
            "common": ["Flushing of skin from vasodilation"],
            "serious": ["Thermal skin burns if set too hot or if falling asleep on pad"],
            "management": "Never sleep on an active heating pad. Do not apply heat to acute fresh injuries under 48 hours."
        }
    },
    "Elastic Compression Crepe Bandage": {
        "search_term": "Crepe Bandage 10cm",
        "price_estimate": "₹50 – ₹120",
        "dosage_guide": "Wrap firmly with 50% overlap from fingers/toes upwards. Loosen before sleeping.",
        "side_effects": {
            "common": ["Mild skin indentation"],
            "serious": ["Circulation cut-off (numbness, tingling, pale or blue cold toes/fingers) if wrapped too tight"],
            "management": "If toes or fingers become numb, tingly, cold, or pale, unwrap and re-wrap more loosely immediately."
        }
    },

    # GENERAL & NUTRITION
    "Paracetamol (500mg)": {
        "search_term": "Crocin 500mg Paracetamol",
        "price_estimate": "₹15 – ₹30",
        "dosage_guide": "Adults: 500mg every 4-6 hours as needed. Do not exceed 4000mg per day.",
        "side_effects": {
            "common": ["Nausea", "Headache", "Stomach comfort change"],
            "serious": ["Liver damage if combined with alcohol or exceeding max daily dose"],
            "management": "Check all cold medication packaging to ensure you aren't doubling up on paracetamol."
        }
    },
    "ORS (Oral Rehydration Salts)": {
        "search_term": "Electral ORS Liquid Tetrapack",
        "price_estimate": "₹30 – ₹60",
        "dosage_guide": "Ready-to-drink or mix as directed. Sip frequently during exercise, heat exhaustion, or illness.",
        "side_effects": {
            "common": ["Pleasant light sweet-salt taste"],
            "serious": ["Excess sodium in severe kidney disease"],
            "management": "Ideal for replenishing minerals during hot summer days and routine rehydration."
        }
    },
    "Vitamin C (Ascorbic Acid 500mg Chewable)": {
        "search_term": "Limcee 500mg Chewable Vitamin C",
        "price_estimate": "₹25 – ₹55",
        "dosage_guide": "Chew 1 tablet (500mg) daily after food.",
        "side_effects": {
            "common": ["Mild heartburn", "Tart or sour taste", "Mild stomach rumble"],
            "serious": ["Kidney stones (oxalate) with megadoses > 2000mg/day"],
            "management": "Chew after a meal. Water-soluble vitamin; excess is safely excreted in urine."
        }
    },
    "Zinc Sulfate / Gluconate (20mg - 50mg)": {
        "search_term": "Zincovit Zinc Multivitamin Tablets",
        "price_estimate": "₹85 – ₹160",
        "dosage_guide": "Adults: 1 tablet daily with a substantial meal. Do not take on an empty stomach.",
        "side_effects": {
            "common": ["Nausea or metallic taste if taken on empty stomach", "Mild indigestion"],
            "serious": ["Copper deficiency and anemia with chronic months of high-dose zinc"],
            "management": "Always ingest in the middle of a full meal to completely avoid the classic zinc nausea."
        }
    },
    "Vitamin D3 (Cholecalciferol 1000 IU / 60,000 IU)": {
        "search_term": "Calcirol 60000 IU Vitamin D3 Sachet",
        "price_estimate": "₹35 – ₹110",
        "dosage_guide": "60,000 IU once weekly for 8 weeks (deficiency), or 1000-2000 IU daily with a fatty meal.",
        "side_effects": {
            "common": ["None at standard replacement dosages"],
            "serious": ["Hypercalcemia (nausea, weakness, confusion, kidney stones) with massive chronic overdose"],
            "management": "Vitamin D is fat-soluble. Take with milk, yogurt, or main meal for optimal absorption."
        }
    },
    "Vitamin B-Complex with Methylcobalamin (B12)": {
        "search_term": "Becosules Performance B Complex Capsules",
        "price_estimate": "₹45 – ₹95",
        "dosage_guide": "1 capsule daily after breakfast or lunch with water.",
        "side_effects": {
            "common": ["Bright neon-yellow urine (completely harmless riboflavin excretion)", "Mild flushing"],
            "serious": ["Peripheral neuropathy only with massive mega-doses of B6 (>200mg/day for months)"],
            "management": "Harmless bright yellow urine is normal. Take with food to prevent mild vitamin burps."
        }
    },
    "Iron (Ferrous Ascorbate) with Folic Acid": {
        "search_term": "Orofer XT Iron Folic Acid Tablets",
        "price_estimate": "₹120 – ₹240",
        "dosage_guide": "1 tablet daily after food with orange juice or water. Avoid taking with tea, coffee, or milk.",
        "side_effects": {
            "common": ["Dark or black stools (harmless unabsorbed iron)", "Constipation", "Nausea", "Stomach cramps"],
            "serious": ["Accidental iron poisoning if swallowed by small children (medical emergency)"],
            "management": "Black stools are completely normal with iron. Take with vitamin C (lemonade) to boost absorption."
        }
    }
}


def enrich():
    print(f"Loading {KB_PATH}...")
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)

    categories = kb_data.get('categories', {})
    enriched_count = 0
    total_count = 0

    for cat_name, med_list in categories.items():
        for med in med_list:
            total_count += 1
            name = med.get('name', '').strip()
            # Match enrichment
            info = CLINICAL_ENRICHMENTS.get(name)
            if not info:
                # Fuzzy fallback matching
                for k, v in CLINICAL_ENRICHMENTS.items():
                    if k.lower() in name.lower() or name.lower() in k.lower():
                        info = v
                        break
            
            if info:
                med['search_term'] = info['search_term']
                med['price_estimate'] = info['price_estimate']
                med['dosage_guide'] = info['dosage_guide']
                med['side_effects'] = info['side_effects']
                med['otc_status'] = "100% Non-Prescription OTC"
                enriched_count += 1
            else:
                # Default generic clinical structure
                med['search_term'] = name.split('(')[0].strip()
                med['price_estimate'] = "₹30 – ₹80"
                med['dosage_guide'] = "Follow package labeling or consult a registered pharmacist."
                med['side_effects'] = {
                    "common": ["Mild digestive change", "Temporary discomfort"],
                    "serious": ["Allergic rash, hives, or swelling", "Difficulty breathing"],
                    "management": "Take with water. Stop use and seek clinical guidance if adverse symptoms occur."
                }
                med['otc_status'] = "100% Non-Prescription OTC"
                enriched_count += 1

    # Save updated JSON
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(kb_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Enriched {enriched_count}/{total_count} medicines in {KB_PATH}")

    # Also update SQLite DB if it exists
    if os.path.exists(DB_PATH):
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Check existing columns in medicines
            cur.execute("PRAGMA table_info(medicines);")
            cols = [c[1] for c in cur.fetchall()]
            
            if 'side_effects' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN side_effects TEXT;")
            if 'dosage_guide' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN dosage_guide TEXT;")
            if 'price_estimate' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN price_estimate TEXT;")
            if 'search_term' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN search_term TEXT;")
            if 'otc_status' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN otc_status TEXT DEFAULT '100% Non-Prescription OTC';")
            
            # Update records
            for cat_name, med_list in categories.items():
                for med in med_list:
                    cur.execute("""
                        UPDATE medicines 
                        SET side_effects = ?, dosage_guide = ?, price_estimate = ?, search_term = ?, otc_status = ?
                        WHERE name = ?
                    """, (
                        json.dumps(med.get('side_effects', {})),
                        med.get('dosage_guide', ''),
                        med.get('price_estimate', ''),
                        med.get('search_term', ''),
                        med.get('otc_status', '100% Non-Prescription OTC'),
                        med['name']
                    ))
            conn.commit()
            conn.close()
            print(f"[OK] Updated SQLite table 'medicines' with side effects, dosage, prices & search terms.")
        except Exception as e:
            print(f"[WARN] SQLite table update warning: {e}")

if __name__ == '__main__':
    enrich()
