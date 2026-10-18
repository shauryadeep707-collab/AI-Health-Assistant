"""
Medical Autocomplete & Spelling Auto-Correction Service for AI Health Assistant.
Provides real-time clinical spellchecking, typo correction, and phrase completion.
Runs 100% locally on the user's laptop/system with zero cloud dependencies.
"""

import re
from difflib import SequenceMatcher

# 1. Canonical Medical Vocabulary & Common Misspelling Map
TYPO_CORRECTIONS = {
    # Fever & Body
    'fevr': 'fever',
    'feve': 'fever',
    'feverr': 'fever',
    'fvr': 'fever',
    'feverish': 'fever',
    'bukhar': 'fever',
    'buxar': 'fever',
    'chils': 'chills',
    'chilss': 'chills',
    'shiverng': 'shivering',
    'sweatng': 'sweating',
    'tirednes': 'tiredness',
    'fatig': 'fatigue',
    'fatiege': 'fatigue',
    'weaknes': 'weakness',

    # Head & ENT
    'hedache': 'headache',
    'headake': 'headache',
    'headach': 'headache',
    'headahe': 'headache',
    'migran': 'migraine',
    'migrain': 'migraine',
    'migrene': 'migraine',
    'sir dard': 'headache',
    'sar dard': 'headache',
    'dizzy': 'dizziness',
    'dizines': 'dizziness',
    'dizzines': 'dizziness',
    'dizzynes': 'dizziness',
    'caugh': 'cough',
    'cugh': 'cough',
    'coug': 'cough',
    'khansi': 'cough',
    'khasi': 'cough',
    'phlegm': 'phlegm',
    'flegm': 'phlegm',
    'balgam': 'phlegm',
    'runy nose': 'runny nose',
    'runing nose': 'runny nose',
    'congeston': 'congestion',
    'congetion': 'congestion',
    'snizing': 'sneezing',
    'snezing': 'sneezing',
    'thorat': 'throat',
    'throate': 'throat',
    'sore throate': 'sore throat',
    'gala dard': 'sore throat',

    # Stomach & Digestion
    'stomch': 'stomach',
    'stomac': 'stomach',
    'stomache': 'stomach',
    'stomack': 'stomach',
    'pet dard': 'stomach pain',
    'diarhea': 'diarrhea',
    'diahrea': 'diarrhea',
    'diarea': 'diarrhea',
    'diarrhoea': 'diarrhea',
    'dast': 'loose motion',
    'vomting': 'vomiting',
    'vomitting': 'vomiting',
    'vomitingg': 'vomiting',
    'ulti': 'vomiting',
    'nausia': 'nausea',
    'nausious': 'nauseous',
    'gasstric': 'gastric',
    'acidty': 'acidity',
    'aciddity': 'acidity',
    'constipashun': 'constipation',
    'constipaton': 'constipation',

    # Heart & Breathing
    'brething': 'breathing',
    'breathng': 'breathing',
    'brethless': 'breathless',
    'breathles': 'breathless',
    'breathlessness': 'breathlessness',
    'chsst': 'chest',
    'chesst': 'chest',
    'cheest': 'chest',
    'chest painn': 'chest pain',
    'seene me dard': 'chest pain',
    'palpitaton': 'palpitations',
    'palpitationss': 'palpitations',

    # Skin & Face
    'acnee': 'acne',
    'acn': 'acne',
    'akne': 'acne',
    'pimpal': 'pimple',
    'pimpel': 'pimple',
    'pimpls': 'pimples',
    'daane': 'pimples',
    'dark spotes': 'dark spots',
    'dark sport': 'dark spots',
    'pigmentashun': 'pigmentation',
    'pigmentatn': 'pigmentation',
    'melasmaa': 'melasma',
    'dullnes': 'dullness',
    'dull face': 'dull skin',
    'dark circels': 'dark circles',
    'dark cirkles': 'dark circles',
    'serumm': 'serum',
    'serums': 'serum',
    'rednes': 'redness',
    'iching': 'itching',
    'itchng': 'itching',
    'khujli': 'itching',
    'rashh': 'rash',
    'alergy': 'allergy',
    'allargy': 'allergy',

    # Medicines & Serums
    'paractamol': 'paracetamol',
    'paracetemol': 'paracetamol',
    'paracitamol': 'paracetamol',
    'paracetmol': 'paracetamol',
    'pacatamol': 'paracetamol',
    'dolo': 'dolo 650',
    'dolo650': 'dolo 650',
    'ibuprufen': 'ibuprofen',
    'ibroprofen': 'ibuprofen',
    'ibuprofin': 'ibuprofen',
    'combiflamm': 'combiflam',
    'cetrizin': 'cetirizine',
    'cetirizn': 'cetirizine',
    'citrizine': 'cetirizine',
    'cetrizine': 'cetirizine',
    'cetzine': 'cetirizine',
    'gelusill': 'gelusil',
    'gelusel': 'gelusil',
    'digen': 'digene',
    'omeprazol': 'omeprazole',
    'omepraxole': 'omeprazole',
    'lozenge': 'lozenges',
    'strepsil': 'strepsils',
    'strepsill': 'strepsils',
    'niacinamde': 'niacinamide',
    'niacinamid': 'niacinamide',
    'hyaloronic': 'hyaluronic acid',
    'hyaluronic acid': 'hyaluronic acid',
    'salicilic': 'salicylic acid',
    'salicylic': 'salicylic acid',
    'retinoll': 'retinol',
    'retinoidd': 'retinoid',
    'vitmin': 'vitamin',
    'vitaminn': 'vitamin',
    'vit c': 'vitamin c',
    'vit d': 'vitamin d',
    'vit b12': 'vitamin b12',
    'sunscren': 'sunscreen',
    'sunskreen': 'sunscreen',
    'sun block': 'sunscreen'
}

# 2. Curated Clinical Phrases for Smart Autocompletion
AUTOCOMPLETE_PHRASES = [
    # Fever
    "fever and body ache",
    "fever with chills and shivering",
    "fever temperature above 101°F",
    "fever since 2 days",
    "fever since 3 days getting worse",
    "fever with mild headache",
    "fever and sore throat",
    "paracetamol 650mg dosage and side effects",

    # Cold & Cough
    "cough and cold with runny nose",
    "dry hacking cough at night",
    "wet cough with yellow phlegm",
    "cough with chest congestion",
    "cough syrup for dry cough",
    "cetirizine 10mg for cold allergy",
    "steam inhalation for nasal congestion",

    # Headache
    "headache on forehead and eyes",
    "headache on one side of head (migraine)",
    "throbbing headache with nausea",
    "severe headache since yesterday",
    "headache medicine with least side effects",

    # Stomach & Digestion
    "stomach pain and cramps",
    "stomach burning with acid reflux",
    "stomach ache after eating",
    "diarrhea and loose motion since today",
    "nausea and vomiting with stomach ache",
    "antacid gelusil for heartburn",
    "ORS oral rehydration salts for dehydration",

    # Throat
    "sore throat and pain when swallowing",
    "sore throat with cold and fever",
    "throat infection lozenges",
    "warm salt water gargle instructions",

    # Face & Skincare
    "dark spots and dullness on face",
    "dark spots acne marks serum",
    "acne and oily face serum recommendations",
    "what serum to apply for acne and pores",
    "what blood test to check skin deficiency",
    "vitamin D and B12 deficiency test for dull skin",
    "iron deficiency ferritin test for dark circles",
    "serum zinc test for acne breakouts",
    "niacinamide 10% zinc serum for blemishes",
    "vitamin c 10% serum for glowing skin",
    "hyaluronic acid 2% serum for dry skin",
    "salicylic acid 2% BHA serum for blackheads",
    "ceramide barrier repair cream for peeling skin",
    "caffeine 5% under eye serum for dark circles",
    "broad spectrum SPF 50 sunscreen for daily use",

    # Cardiac & Emergency
    "chest pain and pressure radiating to left arm",
    "shortness of breath and chest tightness",
    "sudden difficulty breathing",
    "heart palpitations and dizziness",

    # Skin general
    "red itchy rash on arms and legs",
    "skin allergy hives with intense itching",
    "calamine lotion for skin rash"
]

# Clinical word vocabulary for single-word completion
CLINICAL_VOCABULARY = sorted(list(set(
    list(TYPO_CORRECTIONS.values()) + [
        'paracetamol', 'ibuprofen', 'cetirizine', 'omeprazole', 'gelusil', 'digene',
        'niacinamide', 'hyaluronic', 'salicylic', 'retinol', 'ceramide', 'arbutin',
        'caffeine', 'sunscreen', 'headache', 'fever', 'cough', 'chills', 'vomiting',
        'diarrhea', 'nausea', 'acidity', 'congestion', 'dizziness', 'fatigue',
        'asthma', 'allergy', 'rash', 'pimples', 'acne', 'melasma', 'pigmentation',
        'deficiency', 'vitamin', 'ferritin', 'zinc', 'swallowing', 'palpitations'
    ]
)))


def _similarity(s1, s2):
    """Calculates string similarity ratio between 0 and 1."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def auto_correct_token(word):
    """
    Checks if a single word has a typo and returns its best clinical correction.
    """
    w = word.strip().lower()
    if not w or len(w) < 3:
        return word, False

    # 1. Exact match in typo dictionary
    if w in TYPO_CORRECTIONS:
        return TYPO_CORRECTIONS[w], True

    # 2. Check if already correctly spelled
    if w in CLINICAL_VOCABULARY:
        return word, False

    # 3. Fuzzy similarity search against vocabulary
    best_match = None
    best_score = 0.0

    for vocab in CLINICAL_VOCABULARY:
        sim = _similarity(w, vocab)
        if sim > 0.75 and sim > best_score:
            # Check length constraint to prevent over-matching short words
            if abs(len(w) - len(vocab)) <= 3:
                best_match = vocab
                best_score = sim

    if best_match and best_score >= 0.80:
        return best_match, True

    return word, False


def auto_correct_query(query_text):
    """
    Auto-corrects an entire symptom or search query sentence.
    Returns: (corrected_text, has_correction, list_of_fixes)
    """
    if not query_text or not query_text.strip():
        return query_text, False, []

    # Check multi-word typo phrases first
    q_lower = query_text.lower().strip()
    has_correction = False
    fixes = []

    for typo_phrase, correct_phrase in TYPO_CORRECTIONS.items():
        if ' ' in typo_phrase:
            pattern = r'\b' + re.escape(typo_phrase) + r'\b'
            if re.search(pattern, q_lower):
                q_lower = re.sub(pattern, correct_phrase, q_lower)
                has_correction = True
                fixes.append({'original': typo_phrase, 'corrected': correct_phrase})

    # Word-by-word correction
    tokens = re.split(r'(\s+|[^\w\s])', q_lower)
    corrected_tokens = []

    for token in tokens:
        # Only process word tokens
        if re.match(r'^[a-zA-Z0-9]+$', token):
            corrected, changed = auto_correct_token(token)
            if changed and corrected.lower() != token.lower():
                has_correction = True
                fixes.append({'original': token, 'corrected': corrected})
                corrected_tokens.append(corrected)
            else:
                corrected_tokens.append(token)
        else:
            corrected_tokens.append(token)

    corrected_text = "".join(corrected_tokens)
    return corrected_text, has_correction, fixes


def get_autocomplete_suggestions(query_text, limit=6):
    """
    Generates intelligent autocompletions for the user's ongoing input.
    Matches prefix, word-in-phrase, and fuzzy relevance.
    """
    q = (query_text or '').strip().lower()
    if not q or len(q) < 2:
        return []

    # First auto-correct the query base to find relevant completions
    corrected_base, _, _ = auto_correct_query(q)
    search_q = corrected_base if corrected_base else q

    matches = []
    seen = set()

    # 1. Exact prefix match on curated phrases
    for phrase in AUTOCOMPLETE_PHRASES:
        p_lower = phrase.lower()
        if p_lower.startswith(q) or p_lower.startswith(search_q):
            if p_lower not in seen:
                matches.append(phrase)
                seen.add(p_lower)

    # 2. Substring or token match on phrases
    tokens = [t for t in search_q.split() if len(t) > 2]
    for phrase in AUTOCOMPLETE_PHRASES:
        p_lower = phrase.lower()
        if p_lower not in seen:
            if search_q in p_lower or all(t in p_lower for t in tokens if tokens):
                matches.append(phrase)
                seen.add(p_lower)

    # 3. Single-word completions if still under limit
    if len(matches) < limit:
        for word in CLINICAL_VOCABULARY:
            if word.startswith(q) or word.startswith(search_q):
                if word not in seen:
                    matches.append(word.capitalize())
                    seen.add(word)
            if len(matches) >= limit:
                break

    return matches[:limit]


def get_clinical_suggestions(query_text):
    """
    Complete response bundle:
    - original: original input
    - corrected: spell-checked text
    - has_correction: True if typos were fixed
    - fixes: specific replacements made
    - autocompletions: suggested phrases to complete the thought
    """
    q = (query_text or '').strip()
    corrected, has_correction, fixes = auto_correct_query(q)
    completions = get_autocomplete_suggestions(q, limit=5)

    return {
        "ok": True,
        "original": q,
        "corrected": corrected,
        "has_correction": has_correction,
        "fixes": fixes,
        "autocompletions": completions,
        "completions": completions
    }
