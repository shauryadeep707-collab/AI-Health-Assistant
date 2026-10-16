/**
 * Browser-side Red Flags Checker for AI Health Assistant.
 * WHY this module exists: runs entirely offline in the user's browser,
 * ensuring immediate detection of life-threatening emergencies even
 * if the device is disconnected from the internet.
 */

const RedFlags = {
  // Comprehensive emergency keywords including English and Hindi / Hinglish
  emergencyRules: [
    {
      id: 'chest_pain',
      name: 'Chest Pain or Pressure / Seene mein dard',
      keywords: ['chest pain', 'chest pressure', 'chest tightness', 'heart attack', 'seene mein dard', 'chhati mein dard', 'sine me dard', 'dil ka daura', 'dil ka dard'],
      regex: /chest.*(pain|pressure|tight|heavy|squeeze)|pain.*chest|heart.*attack|seene.*dard/i,
      action: 'Call emergency services (112) immediately. Do not wait or drive yourself.'
    },
    {
      id: 'breathing_difficulty',
      name: 'Severe Breathing Difficulty / Saans lene mein takleef',
      keywords: ['trouble breathing', "can't breathe", 'breathless', 'shortness of breath', 'difficulty breathing', 'gasping', 'saans lene mein takleef', 'saans nahi aa rahi', 'dum ghutna', 'saans phoolna', 'dum ghut raha'],
      regex: /(can'?t|cannot|trouble|difficulty|hard).*(breath|breathing)|short(ness)? of breath|saans.*(takleef|nahi|phool)/i,
      action: 'Call emergency services (112). Sit upright and stay calm while waiting for help.'
    },
    {
      id: 'unconscious',
      name: 'Unconsciousness / Fainting / Behosh',
      keywords: ['fainting', 'fainted', 'unconscious', 'passed out', 'collapsed', 'behosh', 'hosh nahi', 'gir gaya', 'behosh ho gaya'],
      regex: /faint|unconscious|pass.*out|behosh/i,
      action: 'Call 112 immediately. Place in recovery position and monitor airway.'
    },
    {
      id: 'seizure',
      name: 'Seizure or Convulsions / Daura / Mirgi',
      keywords: ['seizure', 'convulsion', 'fits', 'daura', 'mirgi', 'jhatkay', 'jhatke'],
      regex: /seizure|convuls|mirgi|daura|jhatk/i,
      action: 'Call 112. Clear sharp objects away. Do NOT place anything in their mouth.'
    },
    {
      id: 'stroke_signs',
      name: 'Stroke Signs / Munh teda / Lakwa',
      keywords: ['face drooping', 'slurred speech', 'one-sided weakness', 'stroke', "can't move arm", 'munh teda', 'bolne mein dikkat', 'ek taraf ka badan', 'lakwa'],
      regex: /face.*(droop|numb)|slur.*speech|stroke|munh.*teda|lakwa/i,
      action: 'Call 112 immediately. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call.'
    },
    {
      id: 'severe_bleeding',
      name: 'Severe Bleeding / Khoon band nahi ho raha',
      keywords: ['severe bleeding', "won't stop bleeding", 'blood loss', 'bahut khoon', 'khoon band nahi ho raha', 'bahut zyada khoon'],
      regex: /(severe|heavy|uncontrol|won'?t stop).*bleed|khoon.*(band|zyada)/i,
      action: 'Call 112. Apply direct, firm pressure with a clean cloth.'
    },
    {
      id: 'vomiting_blood',
      name: 'Vomiting Blood / Khoon ki ulti',
      keywords: ['vomiting blood', 'blood in vomit', 'coughing blood', 'khoon ki ulti', 'ulti mein khoon', 'khoon aa raha'],
      regex: /(vomit|throw|cough|spit).*blood|khoon.*ulti/i,
      action: 'Call 112. Do not consume food or fluids. Lie on side.'
    },
    {
      id: 'allergic_reaction',
      name: 'Severe Allergic Reaction / Gala / Chehra sooj gaya',
      keywords: ['severe allergic reaction', 'throat swelling', 'face swelling', 'anaphylaxis', 'chehra sooj gaya', 'gala sooj gaya', 'saans ruk rahi'],
      regex: /(throat|face|tongue).*swell|anaphyla|gala.*sooj/i,
      action: 'Call 112. Administer EpiPen if available.'
    },
    {
      id: 'suicidal',
      name: 'Suicidal Thoughts / Crisis / Marna chahta',
      keywords: ['suicidal', 'suicide', 'self-harm', 'want to die', 'end my life', 'kill myself', 'marna chahta', 'marna chahti', 'khudkushi'],
      regex: /(want|going|plan).*die|kill.*myself|suicid|khudkushi/i,
      action: 'You are not alone. Call 112 or suicide helpline (9152987821) immediately.'
    },
    {
      id: 'high_fever_severe',
      name: 'Extreme High Fever with Confusion / Bahut tez bukhar',
      keywords: ['fever with stiff neck', 'fever with confusion', 'fever 105', 'bahut tez bukhar', 'gardan akad gayi'],
      regex: /fever.*(stiff neck|confus|105|106)|tez.*bukhar/i,
      action: 'Seek emergency medical evaluation immediately.'
    }
  ],

  /**
   * Check text for red flags.
   * Returns list of matching flag objects or empty array.
   */
  check(text) {
    if (!text || typeof text !== 'string') return [];
    const textLower = text.toLowerCase().trim();
    const matches = [];

    for (const rule of this.emergencyRules) {
      let isMatch = false;
      for (const kw of rule.keywords) {
        if (textLower.includes(kw.toLowerCase())) {
          isMatch = true;
          break;
        }
      }
      if (!isMatch && rule.regex && rule.regex.test(textLower)) {
        isMatch = true;
      }
      if (isMatch) {
        matches.push(rule);
      }
    }
    return matches;
  }
};
