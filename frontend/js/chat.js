/**
 * Chat Module for AI Health Assistant.
 * Handles interactive conversational symptom checking, browser-level red flag checks,
 * quick-reply chips, typing animations, and completion navigation.
 */

const Chat = {
  assessmentId: null,
  isProcessing: false,

  async init() {
    const user = await Auth.requireAuth(['patient']);
    if (!user) return;
    Auth.setupNavbar(user);

    // Get or create assessment
    const params = new URLSearchParams(window.location.search);
    const existingId = params.get('id');

    if (existingId) {
      this.assessmentId = parseInt(existingId);
      await this.loadExistingAssessment();
    } else {
      await this.createNewAssessment();
    }

    this.setupListeners();
  },

  async createNewAssessment() {
    const clientId = UI.uuid();
    const res = await API.post('/api/assessments', { client_id: clientId });
    if (res.ok && res.data) {
      this.assessmentId = res.data.id;
      // Get initial symptom param if any
      const params = new URLSearchParams(window.location.search);
      const symptom = params.get('symptom');

      // Replace URL without reload
      window.history.replaceState({}, '', `/pages/symptom-check.html?id=${this.assessmentId}`);
      
      const symptomPrompts = {
        fever: {
          msg: "Hello! I am your AI Health Assistant. You selected Fever & Chills. How long have you had this fever, and what is your measured body temperature?",
          chips: ['Fever started today', 'Fever for 2-3 days', 'Temperature is above 101°F', 'Mild fever with chills']
        },
        cough: {
          msg: "Hello! I am your AI Health Assistant. You selected Cough & Cold. Is it a dry cough or with phlegm/mucus, and do you have any chest congestion?",
          chips: ['Dry cough for 2 days', 'Wet cough with mucus', 'Cough with throat pain', 'Mild cough and runny nose']
        },
        headache: {
          msg: "Hello! I am your AI Health Assistant. You selected Headache & Migraine. Where is the headache located (forehead, one side, back of head) and how severe is it?",
          chips: ['Mild throbbing headache', 'One-sided severe headache', 'Forehead sinus pressure', 'Headache with dizziness']
        },
        stomach: {
          msg: "Hello! I am your AI Health Assistant. You selected Stomach Pain. What kind of pain is it (sharp cramps, dull ache, burning acidity), and do you have nausea or vomiting?",
          chips: ['Burning acidity / gastric pain', 'Cramps after eating', 'Stomach ache with nausea', 'Mild abdominal discomfort']
        },
        sore_throat: {
          msg: "Hello! I am your AI Health Assistant. You selected Sore Throat. Is it painful to swallow, and do you also have a fever or swollen glands?",
          chips: ['Painful to swallow', 'Scratchy throat with cold', 'Throat irritation for 2 days', 'Mild soreness']
        },
        skin: {
          msg: "Hello! I am your AI Health Assistant. You selected Skin Rash. Where is the rash located, is it itchy or burning, and when did it first appear?",
          chips: ['Red itchy rash on arms/legs', 'Mild rash started today', 'Rash with slight burning', 'Dry scaling skin patch']
        }
      };

      if (symptom && symptomPrompts[symptom]) {
        const item = symptomPrompts[symptom];
        this.appendAIMessage(item.msg, item.chips);
      } else {
        this.appendAIMessage(
          "Hello! I am your AI Health Assistant. Please describe your symptoms in normal words (e.g. 'I have a mild fever and runny nose since yesterday').",
          ['I have a mild fever', 'I have a sore throat & cough', 'I have a headache', 'I have a stomach ache']
        );
      }
    } else {
      UI.toast('Failed to initialize symptom assessment session', 'error');
    }
  },

  async loadExistingAssessment() {
    const res = await API.get(`/api/assessments/${this.assessmentId}`);
    if (res.ok && res.data) {
      const data = res.data;
      if (data.status === 'completed') {
        window.location.href = `/pages/result.html?id=${this.assessmentId}`;
        return;
      }
      // Populate messages
      const messagesContainer = document.getElementById('chat-messages');
      messagesContainer.innerHTML = '';
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(m => {
          if (m.role === 'user') {
            this.appendUserMessage(m.content);
          } else if (m.role === 'assistant') {
            this.appendAIMessage(m.content);
          }
        });
      } else {
        this.appendAIMessage(
          "Hello! Please describe your current symptoms in plain words.",
          ['I have a mild fever', 'I have a sore throat', 'I have a headache']
        );
      }
    }
  },

  setupListeners() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');

    // Attach AI Autocomplete & Spelling Auto-Correction
    if (input && typeof AIAutocomplete !== 'undefined') {
      AIAutocomplete.attach(input, {
        popDirection: 'up',
        onSelect: (selectedText) => {
          // Keep focus so user can hit enter or send
          input.focus();
        }
      });
    }

    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }

    if (sendBtn) {
      sendBtn.addEventListener('click', () => this.sendMessage());
    }

    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
      micBtn.addEventListener('click', () => {
        UI.toast('Voice input is ready for future upgrade (speech-to-text module)', 'info');
      });
    }
  },

  async sendMessage(customText = null) {
    if (this.isProcessing) return;
    const input = document.getElementById('chat-input');
    const text = customText || (input ? input.value.trim() : '');
    if (!text) return;

    if (input && !customText) {
      input.value = '';
    }

    this.appendUserMessage(text);
    this.clearChips();

    // 1. Browser-side safety check: IMMEDIATE RED FLAGS (Works offline!)
    const clientRedFlags = RedFlags.check(text);
    if (clientRedFlags.length > 0) {
      console.warn('Urgent red flag detected client-side:', clientRedFlags);
    }

    this.showTypingIndicator();
    this.isProcessing = true;

    try {
      const clientId = UI.uuid();
      const payload = { content: text, client_id: clientId };

      let res;
      if (!navigator.onLine) {
        // Enqueue offline write and trigger immediate client-side emergency triage if flagged
        await Offline.enqueue(`/api/assessments/${this.assessmentId}/message`, 'POST', payload);
        this.hideTypingIndicator();
        this.isProcessing = false;

        if (clientRedFlags.length > 0) {
          window.location.href = `/pages/result.html?id=${this.assessmentId}&urgent=true&offline=true`;
          return;
        }

        this.appendAIMessage("Your message has been saved offline and will sync once internet connectivity is restored.");
        return;
      }

      res = await API.post(`/api/assessments/${this.assessmentId}/message`, payload);
      this.hideTypingIndicator();
      this.isProcessing = false;

      if (!res.ok) {
        UI.toast(res.error || 'Error processing message', 'error');
        return;
      }

      const data = res.data;

      if (data.type === 'urgent') {
        // Red flag triggered! Redirect immediately to urgent screen
        window.location.href = `/pages/result.html?id=${this.assessmentId}`;
      } else if (data.type === 'followup') {
        this.appendAIMessage(data.message, data.chips);
        if (data.progress) {
          this.updateProgress(data.progress);
        }
      } else if (data.type === 'complete') {
        // Assessment finished, redirect to result screen
        window.location.href = `/pages/result.html?id=${this.assessmentId}`;
      }
    } catch (err) {
      this.hideTypingIndicator();
      this.isProcessing = false;
      console.error(err);
      UI.toast('Network error occurred', 'error');
    }
  },

  appendUserMessage(text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble chat-bubble-user';
    bubble.textContent = text; // textContent for XSS protection
    container.appendChild(bubble);
    this.scrollToBottom();
  },

  appendAIMessage(text, chips = []) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble chat-bubble-ai';
    bubble.textContent = text;
    container.appendChild(bubble);

    if (chips && chips.length > 0) {
      this.renderChips(chips);
    }
    this.scrollToBottom();
  },

  renderChips(chips) {
    const container = document.getElementById('quick-replies');
    if (!container) return;
    container.innerHTML = '';
    chips.forEach(chip => {
      const btn = document.createElement('button');
      btn.className = 'quick-reply-chip';
      btn.textContent = chip;
      btn.onclick = () => this.sendMessage(chip);
      container.appendChild(btn);
    });
  },

  clearChips() {
    const container = document.getElementById('quick-replies');
    if (container) container.innerHTML = '';
  },

  showTypingIndicator() {
    let indicator = document.getElementById('typing-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'typing-indicator';
      indicator.className = 'typing-indicator';
      indicator.innerHTML = '<span></span><span></span><span></span>';
      const container = document.getElementById('chat-messages');
      if (container) container.appendChild(indicator);
    }
    indicator.style.display = 'flex';
    this.scrollToBottom();
  },

  hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.style.display = 'none';
  },

  updateProgress(text) {
    const prog = document.getElementById('chat-progress');
    if (prog) prog.textContent = text;
  },

  scrollToBottom() {
    const container = document.getElementById('chat-messages');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }
};
