/**
 * AI Autocomplete & Spelling Auto-Correction Module for AI Health Assistant.
 * Provides real-time clinical spellchecking, typo fixes, and phrase completion.
 * Operates with 0ms client-side speed and syncs with backend /api/ai/suggest.
 */

const AIAutocomplete = {
  // Client-side quick lookup dictionary for 0ms instant offline feedback
  CLIENT_TYPOS: {
    'fevr': 'fever', 'feve': 'fever', 'feverr': 'fever', 'fvr': 'fever', 'bukhar': 'fever',
    'hedache': 'headache', 'headake': 'headache', 'headach': 'headache', 'sir dard': 'headache',
    'caugh': 'cough', 'cugh': 'cough', 'khansi': 'cough', 'balgam': 'phlegm',
    'stomch': 'stomach', 'stomac': 'stomach', 'stomache': 'stomach', 'pet dard': 'stomach pain',
    'diarhea': 'diarrhea', 'diahrea': 'diarrhea', 'vomting': 'vomiting', 'vomitting': 'vomiting',
    'chsst': 'chest', 'chesst': 'chest', 'brething': 'breathing', 'brethless': 'breathless',
    'paractamol': 'paracetamol', 'paracetemol': 'paracetamol', 'dolo650': 'dolo 650',
    'ibuprufen': 'ibuprofen', 'cetrizin': 'cetirizine', 'gelusill': 'gelusil',
    'acnee': 'acne', 'pimpal': 'pimple', 'dark spotes': 'dark spots', 'dullnes': 'dullness',
    'niacinamde': 'niacinamide', 'hyaloronic': 'hyaluronic acid', 'salicilic': 'salicylic acid',
    'sunscren': 'sunscreen', 'dark circels': 'dark circles'
  },

  CLIENT_PHRASES: [
    "fever and body ache",
    "fever with chills and shivering",
    "fever temperature above 101°F",
    "fever since 2 days",
    "cough and cold with runny nose",
    "dry hacking cough at night",
    "headache on forehead and eyes",
    "headache on one side of head (migraine)",
    "stomach pain and cramps",
    "stomach burning with acid reflux",
    "diarrhea and loose motion since today",
    "sore throat and pain when swallowing",
    "dark spots and dullness on face",
    "acne and oily face serum recommendations",
    "what serum to apply for acne and pores",
    "what blood test to check skin deficiency",
    "vitamin D and B12 deficiency test for dull skin",
    "niacinamide 10% zinc serum for blemishes",
    "vitamin c 10% serum for glowing skin",
    "hyaluronic acid 2% serum for dry skin",
    "salicylic acid 2% BHA serum for blackheads",
    "ceramide barrier repair cream for peeling skin",
    "caffeine 5% under eye serum for dark circles",
    "chest pain and pressure radiating to arm",
    "shortness of breath and chest tightness",
    "paracetamol 650mg dosage and side effects"
  ],

  attach(input, options = {}) {
    if (!input || input._aiAutocompleteAttached) return;
    input._aiAutocompleteAttached = true;

    const popDirection = options.popDirection || 'up'; // 'up' or 'down'
    const onSelect = options.onSelect || null;

    // Create wrapper and dropdown elements
    const wrapper = document.createElement('div');
    wrapper.className = 'ai-autocomplete-wrapper';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const dropdown = document.createElement('div');
    dropdown.className = `ai-autocomplete-dropdown ${popDirection === 'down' ? 'pop-down' : ''}`;
    wrapper.appendChild(dropdown);

    let activeIndex = -1;
    let currentSuggestions = [];
    let currentCorrection = null;
    let debounceTimer = null;

    const closeDropdown = () => {
      dropdown.style.display = 'none';
      dropdown.innerHTML = '';
      activeIndex = -1;
      currentSuggestions = [];
      currentCorrection = null;
    };

    const applyText = (text) => {
      input.value = text;
      input.focus();
      closeDropdown();
      if (typeof onSelect === 'function') {
        onSelect(text);
      }
    };

    const renderUI = (correction, completions, query) => {
      if (!correction && (!completions || completions.length === 0)) {
        closeDropdown();
        return;
      }

      currentCorrection = correction;
      currentSuggestions = completions || [];
      activeIndex = -1;

      let html = '';

      // 1. Auto-Correction "Did you mean" pill
      if (correction && correction.toLowerCase() !== query.toLowerCase()) {
        html += `
          <div class="ai-autocorrect-pill" id="ai-autocorrect-banner">
            <div>
              <span>💡 Did you mean: <strong>${UI.escapeHtml(correction)}</strong>?</span>
            </div>
            <button type="button" class="ai-autocorrect-apply-btn" id="ai-apply-correction-btn">
              Apply (Tab)
            </button>
          </div>
        `;
      }

      // 2. Autocomplete suggestions list
      if (currentSuggestions.length > 0) {
        html += '<ul class="ai-autocomplete-list">';
        currentSuggestions.forEach((item, idx) => {
          // Highlight the user's current query prefix
          const qEscaped = query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const regex = new RegExp(`(${qEscaped})`, 'gi');
          const highlighted = UI.escapeHtml(item).replace(regex, '<strong>$1</strong>');

          html += `
            <li class="ai-autocomplete-item" data-index="${idx}">
              <div class="ai-autocomplete-item-text">
                <span>🔍</span>
                <span>${highlighted}</span>
              </div>
              <span class="ai-autocomplete-badge">Suggest</span>
            </li>
          `;
        });
        html += '</ul>';
      }

      dropdown.innerHTML = html;
      dropdown.style.display = 'block';

      // Bind correction click
      const applyBtn = dropdown.querySelector('#ai-apply-correction-btn');
      if (applyBtn) {
        applyBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          applyText(correction);
        });
      }

      // Bind item clicks
      dropdown.querySelectorAll('.ai-autocomplete-item').forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const idx = parseInt(el.getAttribute('data-index'));
          if (currentSuggestions[idx]) {
            applyText(currentSuggestions[idx]);
          }
        });
      });
    };

    // Client-side quick matcher (instant 0ms)
    const runClientMatch = (query) => {
      const q = query.trim().toLowerCase();
      if (!q || q.length < 2) {
        closeDropdown();
        return;
      }

      // Check client typo dictionary
      let correction = null;
      for (const [typo, fix] of Object.entries(AIAutocomplete.CLIENT_TYPOS)) {
        if (q === typo || q.endsWith(' ' + typo) || q.startsWith(typo + ' ')) {
          correction = q.replace(new RegExp('\\b' + typo + '\\b', 'g'), fix);
          break;
        }
      }

      // Filter client phrases
      const searchTarget = correction || q;
      const completions = AIAutocomplete.CLIENT_PHRASES.filter(p => {
        const pLow = p.toLowerCase();
        return pLow.startsWith(q) || pLow.startsWith(searchTarget) || pLow.includes(q);
      }).slice(0, 4);

      if (correction || completions.length > 0) {
        renderUI(correction, completions, query);
      }
    };

    // Server-side deep clinical matcher (debounced 150ms)
    const runServerMatch = async (query) => {
      const q = query.trim();
      if (!q || q.length < 2) return;

      try {
        const res = await fetch(`/api/ai/suggest?q=${encodeURIComponent(q)}`);
        if (res.ok) {
          const data = await res.json();
          if (data.ok && input.value.trim() === q) {
            const correction = data.has_correction ? data.corrected : null;
            const completions = data.autocompletions || [];
            if (correction || completions.length > 0) {
              renderUI(correction, completions, q);
            }
          }
        }
      } catch (err) {
        // Fallback silently to client-side matches if offline
      }
    };

    // Input events
    input.addEventListener('input', (e) => {
      const val = e.target.value;
      clearTimeout(debounceTimer);

      // Instant client feedback
      runClientMatch(val);

      // Debounced backend clinical validation
      debounceTimer = setTimeout(() => {
        runServerMatch(val);
      }, 150);
    });

    input.addEventListener('keydown', (e) => {
      const items = dropdown.querySelectorAll('.ai-autocomplete-item');
      
      // TAB: Apply correction or active suggestion
      if (e.key === 'Tab') {
        if (currentCorrection && currentCorrection.toLowerCase() !== input.value.trim().toLowerCase()) {
          e.preventDefault();
          applyText(currentCorrection);
          return;
        }
        if (activeIndex >= 0 && currentSuggestions[activeIndex]) {
          e.preventDefault();
          applyText(currentSuggestions[activeIndex]);
          return;
        }
      }

      // ESC: Close dropdown
      if (e.key === 'Escape') {
        closeDropdown();
        return;
      }

      // ARROW DOWN
      if (e.key === 'ArrowDown' && items.length > 0) {
        e.preventDefault();
        activeIndex = (activeIndex + 1) % items.length;
        items.forEach((it, i) => it.classList.toggle('active', i === activeIndex));
        items[activeIndex].scrollIntoView({ block: 'nearest' });
        return;
      }

      // ARROW UP
      if (e.key === 'ArrowUp' && items.length > 0) {
        e.preventDefault();
        activeIndex = (activeIndex - 1 + items.length) % items.length;
        items.forEach((it, i) => it.classList.toggle('active', i === activeIndex));
        items[activeIndex].scrollIntoView({ block: 'nearest' });
        return;
      }

      // ENTER: Select active suggestion
      if (e.key === 'Enter' && activeIndex >= 0 && currentSuggestions[activeIndex]) {
        e.preventDefault();
        applyText(currentSuggestions[activeIndex]);
        return;
      }
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) {
        closeDropdown();
      }
    });
  }
};
