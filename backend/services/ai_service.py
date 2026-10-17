"""
AI Service for AI Health Assistant.
Provides two modes:
1. 'openai' - Uses OpenAI API for natural conversation and extraction
2. 'demo' - Rule-based fallback with scripted follow-ups per category

WHY demo mode: The app MUST work end-to-end without an API key.
If the key is missing or the API call fails, demo mode is used automatically.

AI SAFETY RULES:
- Never diagnose ("you have X") - only "possible" or "may be related"
- Never recommend prescription drugs
- Never give medicine doses
- Flag anything serious
- Never replace professional medical advice
"""

import json
import os
import re
from backend.config import config

# Demo mode follow-up questions organized by symptom category
# WHY scripted: ensures consistent, medically-relevant questions without AI
DEMO_FOLLOWUPS = {
    'fever': [
        {'question': 'How long have you had the fever?', 'chips': ['1 day', '2-3 days', '4-7 days', 'More than a week']},
        {'question': 'How would you describe the severity?', 'chips': ['Mild', 'Moderate', 'Severe']},
        {'question': 'Is the fever getting worse or staying the same?', 'chips': ['Getting worse', 'Staying same', 'Getting better']},
        {'question': 'Do you know your temperature? (in °F)', 'chips': ['Below 100°F', '100-101°F', '101-103°F', 'Above 103°F']},
        {'question': 'Do you have any other symptoms along with the fever?', 'chips': ['Headache', 'Body ache', 'Cough', 'None']},
        {'question': 'Have you taken any medicine for it?', 'chips': ['Paracetamol', 'Ibuprofen', 'Nothing yet', 'Other']},
    ],
    'cold_cough': [
        {'question': 'How long have you had these symptoms?', 'chips': ['1-2 days', '3-5 days', 'About a week', 'More than a week']},
        {'question': 'How would you rate the severity?', 'chips': ['Mild', 'Moderate', 'Severe']},
        {'question': 'Are the symptoms getting worse?', 'chips': ['Yes, getting worse', 'Staying the same', 'Slowly improving']},
        {'question': 'Do you have a fever along with it?', 'chips': ['No fever', 'Mild fever', 'High fever']},
        {'question': 'Any other symptoms? (sore throat, body ache, etc.)', 'chips': ['Sore throat', 'Body ache', 'Runny nose', 'None']},
        {'question': 'Have you taken any medicine?', 'chips': ['Cough syrup', 'Paracetamol', 'Nothing yet', 'Other']},
    ],
    'headache': [
        {'question': 'How long have you been having headaches?', 'chips': ['Today', '2-3 days', 'About a week', 'Recurring']},
        {'question': 'How severe is the headache?', 'chips': ['Mild', 'Moderate', 'Severe', 'Worst ever']},
        {'question': 'Is it getting worse?', 'chips': ['Yes', 'No, same', 'Comes and goes']},
        {'question': 'Where exactly is the pain?', 'chips': ['Forehead', 'One side', 'Back of head', 'All over']},
        {'question': 'Any other symptoms?', 'chips': ['Nausea', 'Dizziness', 'Vision changes', 'None']},
        {'question': 'Have you taken anything for it?', 'chips': ['Paracetamol', 'Ibuprofen', 'Nothing', 'Other']},
    ],
    'sore_throat': [
        {'question': 'How long have you had the sore throat?', 'chips': ['1-2 days', '3-5 days', 'About a week', 'More than a week']},
        {'question': 'How severe is it?', 'chips': ['Mild irritation', 'Moderate pain', 'Severe - hard to swallow']},
        {'question': 'Is it getting worse?', 'chips': ['Getting worse', 'Staying same', 'Getting better']},
        {'question': 'Do you have any fever?', 'chips': ['No fever', 'Mild fever', 'High fever']},
        {'question': 'Any other symptoms?', 'chips': ['Cough', 'Runny nose', 'Ear pain', 'None']},
        {'question': 'Have you tried any remedies?', 'chips': ['Warm water gargle', 'Lozenges', 'Nothing yet', 'Other']},
    ],
    'stomach': [
        {'question': 'How long have you been having stomach issues?', 'chips': ['Today', '2-3 days', 'About a week', 'More than a week']},
        {'question': 'How severe is the discomfort?', 'chips': ['Mild', 'Moderate', 'Severe']},
        {'question': 'Is it getting worse?', 'chips': ['Yes', 'Staying same', 'Improving']},
        {'question': 'What type of stomach issue?', 'chips': ['Pain/cramps', 'Nausea', 'Diarrhea', 'Acidity']},
        {'question': 'Any other symptoms?', 'chips': ['Fever', 'Vomiting', 'Loss of appetite', 'None']},
        {'question': 'Have you taken anything for it?', 'chips': ['Antacid', 'ORS', 'Nothing yet', 'Other']},
    ],
    'general': [
        {'question': 'How long have you been experiencing these symptoms?', 'chips': ['1-2 days', '3-5 days', 'About a week', 'More than a week']},
        {'question': 'How would you rate the severity?', 'chips': ['Mild', 'Moderate', 'Severe']},
        {'question': 'Are the symptoms getting worse?', 'chips': ['Yes, worse', 'Staying same', 'Improving']},
        {'question': 'Do you have any fever?', 'chips': ['No', 'Mild fever', 'High fever']},
        {'question': 'Any other symptoms you want to mention?', 'chips': ['Fatigue', 'Pain', 'Dizziness', 'None']},
        {'question': 'Have you taken any medicine?', 'chips': ['Yes', 'No', 'Home remedies']},
    ],
}

# Category detection keywords for demo mode
CATEGORY_KEYWORDS = {
    'fever': ['fever', 'temperature', 'bukhar', 'tez bukhar', 'hot', 'burning up', 'tapman', 'pyrexia', 'chills'],
    'cold_cough': ['cold', 'cough', 'sardi', 'khansi', 'sneeze', 'runny nose', 'naak', 'jukaam', 'nazla', 'congestion', 'flu', 'phlegm', 'balgam'],
    'headache': ['headache', 'head pain', 'sir dard', 'sar dard', 'migraine', 'sir me dard', 'cephalalgia', 'throbbing head'],
    'sore_throat': ['sore throat', 'throat pain', 'gala dard', 'gale mein dard', 'gala kharab', 'tonsil', 'pharyngitis', 'difficulty swallowing'],
    'stomach': ['stomach', 'pet dard', 'diarrhea', 'vomit', 'nausea', 'acidity', 'pet me dard', 'ulti', 'dast', 'kabz', 'abdominal', 'belly pain', 'loose motion'],
    'cardiac': ['chest', 'heart', 'palpitation', 'seene', 'chhati', 'pressure', 'sine me dard'],
    'skin': ['rash', 'itching', 'khujli', 'skin', 'allergy', 'daane', 'redness', 'boils'],
}


def detect_category(text):
    """Detect symptom category from text using keyword matching."""
    text_lower = (text or '').lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return 'general'


def get_ai_mode():
    """Determine which AI mode to use. Falls back to demo if key is missing."""
    if config.AI_MODE == 'openai' and config.OPENAI_API_KEY:
        return 'openai'
    return 'demo'


def get_followup_question(category, question_index, messages=None):
    """
    Get the next follow-up question for demo mode.
    Returns dict with 'question' and 'chips', or None if all asked.
    """
    followups = DEMO_FOLLOWUPS.get(category, DEMO_FOLLOWUPS['general'])
    if question_index >= len(followups):
        return None  # All questions asked
    return followups[question_index]


def extract_structured_data_demo(messages, category):
    """
    Intelligently extract structured clinical data from chat messages in demo mode.
    Analyzes the full conversational history (all user messages) for:
    - Duration (days, weeks, relative phrases)
    - Severity (mild, moderate, severe across English & Hindi)
    - Worsening status (improving vs worsening)
    - Temperature (°F)
    - Associated symptoms
    - AI risk recommendation
    """
    structured = {
        'main_symptoms': [],
        'category': category or 'general',
        'duration_days': 1,
        'severity': 'mild',
        'worsening': False,
        'temperature_f': 0,
        'other_symptoms': [],
        'medicines_taken': [],
        'notes': '',
        'ai_risk_level': 'low'
    }
    
    user_messages = [m for m in messages if m.get('role') == 'user']
    if not user_messages:
        return structured

    all_user_text = ' '.join([m.get('content', '') for m in user_messages]).lower().strip()
    first_msg = user_messages[0].get('content', '')
    structured['main_symptoms'] = [first_msg] if first_msg else []

    # 1. DURATION EXTRACTION
    day_match = re.search(r'(\d+)\s*(?:-\s*(\d+))?\s*(?:day|din|dias)', all_user_text)
    week_match = re.search(r'(\d+)\s*(?:-\s*(\d+))?\s*(?:week|hafte|hafta)', all_user_text)
    if week_match:
        weeks = int(week_match.group(2) or week_match.group(1))
        structured['duration_days'] = max(7, weeks * 7)
    elif day_match:
        days = int(day_match.group(2) or day_match.group(1))
        structured['duration_days'] = days
    elif any(p in all_user_text for p in ['more than a week', 'over a week', 'about a week', '1 week', 'ek hafta']):
        structured['duration_days'] = 7
    elif any(p in all_user_text for p in ['4-7 days', '4 to 7 days', 'char se saat din']):
        structured['duration_days'] = 5
    elif any(p in all_user_text for p in ['2-3 days', '2 to 3 days', 'do teen din']):
        structured['duration_days'] = 3
    elif any(p in all_user_text for p in ['since yesterday', 'kal se']):
        structured['duration_days'] = 2
    elif any(p in all_user_text for p in ['today', 'aaj se', '1 day', 'ek din']):
        structured['duration_days'] = 1

    # Also parse sequential answers if chips were clicked
    for i, msg in enumerate(user_messages[1:], 1):
        ans = (msg.get('content', '') or '').lower().strip()
        if i == 1:
            if 'week' in ans or '7' in ans:
                structured['duration_days'] = max(structured['duration_days'], 7)
            elif '4' in ans or '5' in ans or '6' in ans:
                structured['duration_days'] = max(structured['duration_days'], 5)
            elif '2' in ans or '3' in ans:
                structured['duration_days'] = max(structured['duration_days'], 3)

    # 2. SEVERITY EXTRACTION (English & Hindi)
    severe_words = [
        'severe', 'worst', 'unbearable', 'extreme', 'intense', 'critical',
        'very high', 'very bad', 'bahut zyada', 'tez', 'bura', 'cannot sleep',
        'hard to swallow', 'terrible', 'excruciating', 'acute', 'high intensity',
        'shiddat', 'asahy', 'unbearable pain', 'very painful'
    ]
    moderate_words = [
        'moderate', 'medium', 'quite bad', 'bothersome', 'persistent', 'bad',
        'painful', 'achy', 'frequent', 'thoda zyada', 'kafi', 'disturbing', 'troublesome'
    ]
    if any(w in all_user_text for w in severe_words):
        structured['severity'] = 'severe'
    elif any(w in all_user_text for w in moderate_words):
        structured['severity'] = 'moderate'
    else:
        # Check follow-up answers for chip clicks
        for i, msg in enumerate(user_messages[1:], 1):
            ans = (msg.get('content', '') or '').lower().strip()
            if i == 2:
                if 'severe' in ans or 'worst' in ans:
                    structured['severity'] = 'severe'
                elif 'moderate' in ans:
                    structured['severity'] = 'moderate'

    # 3. WORSENING EXTRACTION
    worse_words = [
        'getting worse', 'worse', 'worsening', 'increasing', 'escalating',
        'spreading', 'badh raha', 'zyada ho raha', 'badhti ja rahi',
        'yes, getting worse', 'yes, worse', 'intensifying', 'worsened'
    ]
    improving_words = ['improving', 'better', 'getting better', 'recovering', 'easing', 'slowly improving']
    if any(w in all_user_text for w in worse_words) and not any(w in all_user_text for w in improving_words):
        structured['worsening'] = True
    else:
        for i, msg in enumerate(user_messages[1:], 1):
            ans = (msg.get('content', '') or '').lower().strip()
            if i == 3:
                structured['worsening'] = 'worse' in ans or 'yes' in ans

    # 4. TEMPERATURE EXTRACTION
    temp_match = re.search(r'\b(10[0-6](?:\.[0-9])?)\b', all_user_text)
    if temp_match:
        try:
            structured['temperature_f'] = float(temp_match.group(1))
        except ValueError:
            pass
    elif any(p in all_user_text for p in ['above 103', '>103', 'high fever', 'tez bukhar']):
        structured['temperature_f'] = 103.5
    elif any(p in all_user_text for p in ['101-103', '101 to 103', '102']):
        structured['temperature_f'] = 102.0
    elif any(p in all_user_text for p in ['100-101', 'mild fever', 'halka bukhar']):
        structured['temperature_f'] = 100.5

    # 5. ASSOCIATED / OTHER SYMPTOMS
    symptom_catalog = [
        ('headache', 'Headache'), ('cough', 'Cough'), ('cold', 'Common Cold'),
        ('sore throat', 'Sore Throat'), ('throat pain', 'Throat Pain'),
        ('body ache', 'Body Ache'), ('fatigue', 'Fatigue / Weakness'),
        ('dizziness', 'Dizziness'), ('nausea', 'Nausea'), ('vomiting', 'Vomiting'),
        ('diarrhea', 'Diarrhea'), ('stomach pain', 'Abdominal Pain'),
        ('chills', 'Chills / Shivering'), ('runny nose', 'Runny Nose'),
        ('loss of appetite', 'Loss of Appetite'), ('rash', 'Skin Rash')
    ]
    detected_others = []
    for kw, label in symptom_catalog:
        if kw in all_user_text:
            if not first_msg or kw not in first_msg.lower():
                detected_others.append(label)
    if detected_others:
        structured['other_symptoms'] = list(dict.fromkeys(detected_others))[:5]

    # 6. ESTIMATE AI_RISK_LEVEL (helps elevate risk when appropriate)
    if structured['temperature_f'] >= 103 or (structured['severity'] == 'severe' and structured['duration_days'] >= 3):
        structured['ai_risk_level'] = 'urgent'
    elif structured['severity'] in ('moderate', 'severe') or structured['duration_days'] >= 3 or structured['temperature_f'] >= 101 or structured['worsening']:
        structured['ai_risk_level'] = 'medium'
    else:
        structured['ai_risk_level'] = 'low'

    return structured


def call_openai(messages_for_api, system_prompt):
    """
    Call the OpenAI API.
    Returns the response content string, or None on failure.
    """
    try:
        import urllib.request
        import json as json_module
        
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.OPENAI_API_KEY}'
        }
        
        body = json_module.dumps({
            'model': config.OPENAI_MODEL,
            'messages': [{'role': 'system', 'content': system_prompt}] + messages_for_api,
            'temperature': 0.3,
            'max_tokens': 800,
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        response = urllib.request.urlopen(req, timeout=30)
        result = json_module.loads(response.read().decode('utf-8'))
        
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f'OpenAI API error: {e}')
        return None


# System prompt for the AI - enforces safety rules
SYSTEM_PROMPT_CHAT = """You are a helpful health assistant chatbot. You help users understand their symptoms.

IMPORTANT RULES:
- NEVER diagnose. Say "this could possibly be" or "may be related to" instead of "you have".
- NEVER recommend prescription drugs. Only mention common OTC items if relevant.
- NEVER give specific medicine doses, especially for children.
- ALWAYS flag anything that sounds serious.
- If the user mentions chest pain, trouble breathing, fainting, seizure, stroke signs, severe bleeding, vomiting blood, or severe allergic reactions, immediately tell them to call emergency services (112).
- Accept Hindi, Hinglish, and English input. Reply in the same language the user writes in.
- Be empathetic, clear, and concise.
- You are asking follow-up questions to understand the patient's symptoms better.
- Ask ONE question at a time.
- After enough information, you will be asked to extract structured data."""

SYSTEM_PROMPT_EXTRACT = """You are a medical data extraction assistant. Extract structured information from the patient chat conversation.

Return ONLY valid JSON with this exact format:
{
  "main_symptoms": ["list of main symptoms described"],
  "category": "fever|cold_cough|headache|sore_throat|stomach|general",
  "duration_days": number,
  "severity": "mild|moderate|severe",
  "worsening": true/false,
  "temperature_f": number or 0 if unknown,
  "other_symptoms": ["list"],
  "medicines_taken": ["list"],
  "notes": "any other relevant observations",
  "ai_risk_level": "low|medium|urgent",
  "ai_reason": "one sentence explaining the risk assessment"
}

Rules for ai_risk_level:
- "urgent": chest pain, breathing difficulty, stroke signs, seizure, severe bleeding, high fever with confusion
- "medium": symptoms > 3 days, moderate-severe severity, worsening, fever > 101F, age < 5 or > 60
- "low": mild symptoms, short duration, improving

Return ONLY the JSON object, no other text."""


def generate_followup_openai(messages, patient_profile=None):
    """
    Use OpenAI to generate a contextual follow-up question.
    Returns dict with 'question' and optional 'chips'.
    """
    # Build messages for API
    api_messages = []
    for m in messages:
        api_messages.append({'role': m.get('role', 'user'), 'content': m.get('content', '')})
    
    # Add context about what we know from profile
    context = ''
    if patient_profile:
        age = patient_profile.get('age', '')
        gender = patient_profile.get('gender', '')
        conditions = patient_profile.get('chronic_conditions', '')
        if age:
            context += f"Patient is {age} years old. "
        if gender:
            context += f"Gender: {gender}. "
        if conditions and conditions.lower() not in ('none', 'nil', 'na'):
            context += f"Known conditions: {conditions}. "
    
    prompt = SYSTEM_PROMPT_CHAT
    if context:
        prompt += f"\n\nPatient context (already known, do NOT re-ask): {context}"
    
    prompt += f"\n\nYou have asked {len([m for m in messages if m.get('role') == 'assistant'])} questions so far. Ask a maximum of 6 follow-up questions total. Ask ONE question now."
    
    response = call_openai(api_messages, prompt)
    if response:
        return {'question': response, 'chips': []}
    return None


def extract_structured_openai(messages):
    """
    Use OpenAI to extract structured data from the conversation.
    Returns a dict, or None on failure.
    """
    # Build conversation text
    conversation = '\n'.join([
        f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
        for m in messages
    ])
    
    api_messages = [{'role': 'user', 'content': f'Extract structured data from this conversation:\n\n{conversation}'}]
    
    response = call_openai(api_messages, SYSTEM_PROMPT_EXTRACT)
    if response:
        try:
            # Try to parse JSON from the response
            # Handle cases where the AI wraps it in ```json blocks
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[1]
                cleaned = cleaned.rsplit('```', 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Retry once with a stricter prompt
            response2 = call_openai(
                [{'role': 'user', 'content': f'Return ONLY valid JSON, no markdown:\n{conversation}'}],
                SYSTEM_PROMPT_EXTRACT
            )
            if response2:
                try:
                    return json.loads(response2.strip())
                except json.JSONDecodeError:
                    pass
    return None


def process_message(messages, patient_profile=None):
    """
    Main entry point: process chat messages and return the next action.
    
    Returns dict:
    - If more questions needed: {'type': 'followup', 'question': str, 'chips': [str], 'progress': str}
    - If assessment complete: {'type': 'complete', 'structured_data': dict}
    """
    mode = get_ai_mode()
    user_messages = [m for m in messages if m.get('role') == 'user']
    question_count = len([m for m in messages if m.get('role') == 'assistant'])
    
    if mode == 'openai':
        # Use OpenAI for follow-up generation
        max_questions = 6
        
        if question_count >= max_questions:
            # Extract structured data
            structured = extract_structured_openai(messages)
            if structured is None:
                # Fallback to demo extraction
                category = detect_category(user_messages[0].get('content', '') if user_messages else '')
                structured = extract_structured_data_demo(messages, category)
            return {'type': 'complete', 'structured_data': structured}
        
        result = generate_followup_openai(messages, patient_profile)
        if result:
            return {
                'type': 'followup',
                'question': result['question'],
                'chips': result.get('chips', []),
                'progress': f'Question {question_count + 1} of ~{max_questions}'
            }
        
        # Fallback to demo mode if OpenAI fails
        mode = 'demo'
    
    # Demo mode
    if not user_messages:
        return {
            'type': 'followup',
            'question': 'I\'m here to help you understand your symptoms. Could you describe what you\'re experiencing?',
            'chips': ['I have a fever', 'I have a cough/cold', 'I have a headache', 'My throat hurts'],
            'progress': 'Getting started'
        }
    
    category = detect_category(user_messages[0].get('content', ''))
    
    # question_count is the number of assistant messages (which is the number of questions asked)
    followup = get_followup_question(category, question_count - 1)  # -1 because first assistant msg was the initial greeting-type prompt
    
    if followup and question_count <= 6:
        return {
            'type': 'followup',
            'question': followup['question'],
            'chips': followup['chips'],
            'progress': f'Question {question_count} of ~6'
        }
    
    # All questions asked - extract data
    structured = extract_structured_data_demo(messages, category)
    return {'type': 'complete', 'structured_data': structured}
