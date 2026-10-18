/**
 * Result Module for AI Health Assistant.
 * Renders assessment results: Low, Medium, or Urgent.
 * - Accurate risk scoring and factors.
 * - Removed "Warning Signs to Monitor" per user request.
 * - In place of "When to See a Doctor", displays condition-matched doctors (both online & offline).
 * - High-risk alert option ("Notify Me & Alert On-Call Doctors") and emergency contact to offline doctors.
 */

const Result = {
  assessmentId: null,
  assessmentData: null,
  relatedDoctors: [],

  async init() {
    const user = await Auth.requireAuth(['patient', 'doctor']);
    if (!user) return;
    Auth.setupNavbar(user);

    const params = new URLSearchParams(window.location.search);
    this.assessmentId = params.get('id');

    if (!this.assessmentId) {
      UI.toast('No assessment ID specified', 'error');
      window.location.href = '/pages/patient-dashboard.html';
      return;
    }

    await this.loadResult();
  },

  async loadResult() {
    const res = await API.get(`/api/assessments/${this.assessmentId}`);
    const container = document.getElementById('result-container');
    if (!container) return;

    if (!res.ok || !res.data) {
      container.innerHTML = `
        <div class="card text-center p-6">
          <h3>Assessment Not Found</h3>
          <p class="text-muted mt-2">Could not load the requested health assessment.</p>
          <a href="/pages/patient-dashboard.html" class="btn btn-primary mt-4">Return to Dashboard</a>
        </div>
      `;
      return;
    }

    this.assessmentData = res.data;
    const data = this.assessmentData;
    const level = (data.risk_level || 'low').toLowerCase();

    // Fetch condition-matched doctors (including offline on-call doctors)
    const category = data.category || 'general';
    const docRes = await API.get(`/api/doctors/nearby?category=${encodeURIComponent(category)}&include_offline=true`);
    this.relatedDoctors = docRes.ok && Array.isArray(docRes.data) ? docRes.data : [];

    if (level === 'urgent') {
      this.renderUrgentScreen(container, data);
    } else if (level === 'medium') {
      this.renderMediumScreen(container, data);
    } else {
      await this.renderLowScreen(container, data);
    }

    this.ensureModalExists();
  },

  /* ==========================================================
     1. URGENT / EMERGENCY SCREEN
     ========================================================== */
  renderUrgentScreen(container, data) {
    const reasons = Array.isArray(data.risk_reasons) ? data.risk_reasons : [];
    const category = (data.category || 'general').replace('_', ' ');

    container.innerHTML = `
      <div class="urgent-panel">
        <div class="urgent-icon">🚨</div>
        <h1 class="urgent-title">EMERGENCY: Immediate Medical Care Required</h1>
        <p class="urgent-subtitle">
          Based on the reported symptoms, you may be experiencing a medical emergency that requires prompt evaluation by a healthcare professional.
        </p>

        <div class="urgent-buttons">
          <a href="tel:112" class="urgent-call-btn">
            📞 Call National Emergency (112)
          </a>
          <a href="tel:108" class="urgent-call-btn" style="background: #fef2f2; border: 2px solid white; color: var(--error);">
            🚑 Call Ambulance (108)
          </a>
        </div>

        <div class="mt-6 text-sm" style="opacity: 0.95; max-width: 600px; margin-left: auto; margin-right: auto; text-align: left; background: rgba(0,0,0,0.15); padding: 1.25rem; border-radius: 12px;">
          <strong>Important Instructions:</strong>
          <ul style="margin-top: 0.5rem; padding-left: 1.25rem;">
            <li>Do not attempt to drive yourself to the hospital; have someone drive you or wait for an ambulance.</li>
            <li>Stay calm, sit or lie down comfortably, and do not exert yourself.</li>
            <li>Keep doors unlocked so first responders can reach you easily.</li>
          </ul>
        </div>
      </div>

      <!-- Automatic Doctor Dispatch Card -->
      ${this.renderAutoDispatchCard(data)}

      <!-- Summary of Patient Talk with Health Checker -->
      ${this.renderTalkSummaryCard(data)}

      <!-- High-Risk Patient Alert Banner -->
      <div class="high-risk-alert-box card">
        <div class="flex items-center justify-between" style="flex-wrap: wrap; gap: 1rem;">
          <div>
            <h4>🔔 High-Risk Emergency Alert System</h4>
            <p class="text-sm" style="color: var(--gray-700); margin: 0;">
              Keep your phone alert on. Click below to register an immediate emergency alert and notify on-call medical doctors.
            </p>
          </div>
          <button id="alert-toggle-btn" class="btn btn-warning" onclick="Result.triggerHighRiskAlert(${data.id})">
            🔔 Alert Me &amp; Notify On-Call Doctors
          </button>
        </div>
      </div>

      <!-- Reasons for Emergency Escalation -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">Reasons for Emergency Escalation</h3>
        </div>
        <ul style="padding-left: 1.25rem; color: var(--gray-700);">
          ${reasons.length > 0 
            ? reasons.map(r => `<li style="margin-bottom: 0.5rem; font-weight: 500;">⚠️ ${UI.escapeHtml(r)}</li>`).join('') 
            : '<li>Identified high-priority symptom red flags.</li>'}
        </ul>
      </div>

      <!-- Specialist Doctors Related to This Condition (Online & Offline) -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">👨‍⚕️ Emergency Specialists &amp; On-Call Doctors</h3>
          <span class="text-xs text-muted">Specialists for ${category}</span>
        </div>
        <p class="text-sm text-muted mb-4">
          Contact doctors specializing in your condition. You can send an urgent priority alert to offline doctors as well.
        </p>
        <div id="urgent-doctors-list">
          ${this.renderDoctorCardsHtml(this.relatedDoctors, data.id, true)}
        </div>
        <div class="mt-6 flex justify-between items-center" style="flex-wrap: wrap; gap: 1rem;">
          <a href="/pages/doctors.html" class="btn btn-secondary">Find Nearest Hospital / Emergency Center</a>
          <a href="/pages/patient-dashboard.html" class="btn btn-outline">Go to Dashboard</a>
        </div>
      </div>
    `;
  },

  /* ==========================================================
     2. MEDIUM RISK SCREEN
     ========================================================== */
  renderMediumScreen(container, data) {
    const reasons = Array.isArray(data.risk_reasons) ? data.risk_reasons : [];
    const category = data.category || 'general';

    container.innerHTML = `
      <div class="risk-card risk-card-medium">
        <div class="risk-icon">⚠️</div>
        <h1 class="risk-title" style="color: var(--risk-medium);">Moderate-to-High Risk Assessment</h1>
        <p class="risk-description">
          Your symptoms require professional evaluation by a qualified doctor to ensure proper diagnosis and treatment.
        </p>
        <div class="mt-4">
          ${UI.riskBadge('medium')}
          <span style="margin-left: 0.75rem; font-weight: 700; color: var(--gray-800);">
            Risk Score: ${data.risk_score || 3} / 10
          </span>
        </div>
      </div>

      <!-- Automatic Doctor Dispatch Card -->
      ${this.renderAutoDispatchCard(data)}

      <!-- Summary of Patient Talk with Health Checker -->
      ${this.renderTalkSummaryCard(data)}

      <!-- High-Risk Patient Alert Banner -->
      <div class="high-risk-alert-box card">
        <div class="flex items-center justify-between" style="flex-wrap: wrap; gap: 1rem;">
          <div>
            <h4>🔔 High-Risk Notification &amp; On-Call Alert</h4>
            <p class="text-sm" style="color: var(--gray-700); margin: 0;">
              Enable emergency notification so you are alerted when a doctor reviews your assessment or comes online.
            </p>
          </div>
          <button id="alert-toggle-btn" class="btn btn-warning" onclick="Result.triggerHighRiskAlert(${data.id})">
            🔔 Alert Me &amp; Notify On-Call Doctors
          </button>
        </div>
      </div>

      <!-- Condition-Matched Doctors (In place of When to See a Doctor) -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">👨‍⚕️ Doctors Specializing in Your Condition</h3>
          <span class="text-xs text-muted">Specialist matching for ${category.replace('_', ' ')}</span>
        </div>
        <p class="text-sm text-muted mb-4">
          These verified specialists handle your symptom category. If a doctor is currently offline, you can dispatch an urgent high-risk alert directly to their clinic queue.
        </p>
        <div id="medium-doctors-list">
          ${this.renderDoctorCardsHtml(this.relatedDoctors, data.id, true)}
        </div>
      </div>
    `;
  },

  /* ==========================================================
     3. LOW RISK SCREEN
     ========================================================== */
  async renderLowScreen(container, data) {
    const category = data.category || 'general';

    // Fetch guidance and medicines in parallel
    const [guidanceRes, medicinesRes] = await Promise.all([
      API.get(`/api/guidance/${category}`),
      API.get(`/api/medicines/${category}`)
    ]);

    const guidance = guidanceRes.ok ? guidanceRes.data : null;
    const medicines = medicinesRes.ok ? medicinesRes.data : [];

    container.innerHTML = `
      <div class="risk-card risk-card-low">
        <div class="risk-icon">✅</div>
        <h1 class="risk-title" style="color: var(--risk-low);">Low Risk Assessment</h1>
        <p class="risk-description">
          Your reported symptoms appear mild and manageable with self-care and monitoring.
        </p>
        <div class="mt-4">
          ${UI.riskBadge('low')}
          <span style="margin-left: 0.75rem; font-weight: 600; color: var(--gray-700);">
            Risk Score: ${data.risk_score || 0} / 10
          </span>
        </div>
      </div>

      <!-- Automatic Doctor Dispatch Card -->
      ${this.renderAutoDispatchCard(data)}

      <!-- Summary of Patient Talk with Health Checker -->
      ${this.renderTalkSummaryCard(data)}

      <!-- Home-Care Guidance Accordion (Warning Signs REMOVED per user request) -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">Home-Care Guidance &amp; Self-Monitoring</h3>
        </div>
        <div id="guidance-accordion"></div>
      </div>

      <!-- Condition-Matched Doctors (Placed directly in result where 'when to see doctor' was) -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">👨‍⚕️ Doctors Specializing in Your Condition</h3>
          <span class="text-xs text-muted">Specialists for ${category.replace('_', ' ')}</span>
        </div>
        <p class="text-sm text-muted mb-4">
          Verified medical doctors available for your condition. You can request a consultation or send an alert to offline doctors if symptoms do not improve.
        </p>
        <div id="low-doctors-list">
          ${this.renderDoctorCardsHtml(this.relatedDoctors, data.id, false)}
        </div>
      </div>

      <!-- Controlled OTC Medicine Info -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">Controlled Over-The-Counter (OTC) Information</h3>
        </div>
        <div id="medicines-container"></div>
      </div>

      <!-- Bottom Navigation -->
      <div class="card mt-6 text-center">
        <h4>Need further peace of mind?</h4>
        <p class="text-sm text-muted mt-1">You can explore more doctors on the map or return to your patient dashboard.</p>
        <div class="mt-4 flex gap-4" style="justify-content: center; flex-wrap: wrap;">
          <a href="/pages/doctors.html?category=${encodeURIComponent(category)}&assessment_id=${data.id}" class="btn btn-secondary">
            View All Nearby Doctors on Map
          </a>
          <a href="/pages/patient-dashboard.html" class="btn btn-primary">
            Done &amp; Save to Dashboard
          </a>
        </div>
      </div>
    `;

    // Render Guidance Accordion - WARNING SIGNS TO MONITOR REMOVED PER USER INSTRUCTION
    const accordionContainer = document.getElementById('guidance-accordion');
    if (accordionContainer && guidance) {
      if (guidance.home_care && guidance.home_care.length > 0) {
        accordionContainer.appendChild(UI.createAccordion('Recommended Self-Care Steps', guidance.home_care));
      }
      // 'Warning Signs to Monitor' is explicitly removed.
    }

    // Render Medicines
    const medsContainer = document.getElementById('medicines-container');
    if (medsContainer) {
      if (medicines.length === 0) {
        medsContainer.innerHTML = '<p class="text-sm text-muted">No specific OTC medications indicated. Maintain rest and hydration.</p>';
      } else {
        medsContainer.innerHTML = medicines.map(m => {
          const se = m.side_effects || {};
          const common = Array.isArray(se.common) ? se.common : [];
          const serious = Array.isArray(se.serious) ? se.serious : [];
          const management = se.management || 'Take with water as directed.';
          const buyLinks = m.buy_links || {};

          return `
          <div class="medicine-card">
            <div class="medicine-header">
              <div>
                <div class="medicine-name">${UI.escapeHtml(m.name)}</div>
                <div class="medicine-purpose">${UI.escapeHtml(m.purpose || '')}</div>
              </div>
              <div class="medicine-price-badge">
                <span>🏷️</span> ${UI.escapeHtml(m.price_estimate || '₹25 – ₹50')}
              </div>
            </div>

            <p class="text-sm" style="color: var(--gray-600); margin-bottom: 0.5rem; line-height: 1.5;">${UI.escapeHtml(m.general_info || '')}</p>
            
            ${m.dosage_guide ? `
              <div class="p-2 mb-2" style="background: #f8fafc; border-radius: 6px; font-size: 0.85rem; border-left: 3px solid var(--primary);">
                <strong>Dosage:</strong> ${UI.escapeHtml(m.dosage_guide)}
              </div>
            ` : ''}

            <!-- Side Effects Breakdown -->
            <div class="side-effects-container">
              <div class="se-section-title" style="color: var(--gray-700);">
                <span>⚡ Common Side Effects (Usually Mild):</span>
              </div>
              <div class="se-tags-wrapper">
                ${common.length > 0 ? common.map(c => `
                  <span class="se-tag se-tag-common">✓ ${UI.escapeHtml(c)}</span>
                `).join('') : '<span class="text-xs text-muted">Rarely reported at standard dosages.</span>'}
              </div>

              <div class="se-section-title" style="color: var(--error);">
                <span>🚨 Serious Warnings (Stop &amp; Consult Doctor If Occurs):</span>
              </div>
              <div class="se-tags-wrapper">
                ${serious.length > 0 ? serious.map(s => `
                  <span class="se-tag se-tag-serious">⚠️ ${UI.escapeHtml(s)}</span>
                `).join('') : '<span class="text-xs text-muted">Discontinue if allergic hives or swelling develops.</span>'}
              </div>

              <div class="se-management-box">
                <strong>💡 How to manage &amp; avoid side effects:</strong> ${UI.escapeHtml(management)}
              </div>
            </div>

            <div style="font-size: 0.85rem; margin-top: 0.5rem;">
              <strong>Precautions:</strong>
              <ul style="padding-left: 1.25rem; color: var(--gray-600); margin-top: 0.25rem;">
                ${(m.precautions || []).map(p => `<li>${UI.escapeHtml(p)}</li>`).join('')}
              </ul>
            </div>

            <div style="font-size: 0.85rem; margin-top: 0.5rem; color: var(--error);">
              <strong>Avoid If:</strong> ${(m.avoid_if || []).map(a => UI.escapeHtml(a)).join(', ')}
            </div>

            <!-- Direct Buy Online Pharmacy Buttons -->
            <div class="direct-buy-section">
              <div class="direct-buy-title">
                <span>🛒 <strong>Direct Buy Online (Verified Pharmacies):</strong></span>
                <a href="/pages/self-care.html?product=${encodeURIComponent(m.search_term || m.name)}" class="text-xs text-primary font-semibold" style="text-decoration: underline;">
                  Ask Side Effects AI &rarr;
                </a>
              </div>
              <div class="direct-buy-buttons">
                <a href="${buyLinks.tata_1mg || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-1mg" title="Buy on Tata 1mg">
                  🛒 Tata 1mg
                </a>
                <a href="${buyLinks.apollo || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-apollo" title="Buy on Apollo Pharmacy">
                  🏥 Apollo
                </a>
                <a href="${buyLinks.netmeds || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-netmeds" title="Buy on Netmeds">
                  💊 Netmeds
                </a>
                <a href="${buyLinks.pharmeasy || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-pharmeasy" title="Buy on PharmEasy">
                  📦 PharmEasy
                </a>
              </div>
            </div>
          </div>
        `}).join('');
      }
    }
  },

  /* ==========================================================
     4. AUTOMATIC DOCTOR ROUTING & TALK SUMMARY CARDS
     ========================================================== */
  renderAutoDispatchCard(data) {
    const ac = data.assigned_consultation;
    if (!ac) {
      return '';
    }
    const docName = ac.doctor_name || 'Specialist Doctor';
    const spec = ac.doctor_specialization || 'Consultant';
    const clinic = ac.clinic_name ? ` &bull; ${UI.escapeHtml(ac.clinic_name)}` : '';
    const status = ac.status || 'pending';

    return `
      <div class="card mt-6" style="border: 2px solid #10b981; background: #f0fdf4;">
        <div class="flex items-center justify-between" style="flex-wrap: wrap; gap: 1rem;">
          <div style="display: flex; gap: 0.75rem; align-items: center;">
            <div style="font-size: 2rem;">⚡</div>
            <div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <h4 style="margin: 0; color: #065f46;">Case Automatically Forwarded to Doctor</h4>
                <span class="badge" style="background: #10b981; color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 12px;">AUTO-DISPATCHED</span>
              </div>
              <p class="text-sm mt-1" style="color: #047857; margin-bottom: 0;">
                Your triage summary and health checkup talk have been automatically sent to <strong>Dr. ${UI.escapeHtml(docName)}</strong> (${UI.escapeHtml(spec)}${clinic}).
              </p>
              <div class="text-xs text-muted mt-1">
                Queue Status: <strong style="text-transform: capitalize; color: #065f46;">${UI.escapeHtml(status)}</strong> &bull; The doctor has been notified and will review your case shortly.
              </div>
            </div>
          </div>
          <div>
            <a href="/pages/consultations.html" class="btn btn-sm btn-primary">
              View Consultation Status
            </a>
          </div>
        </div>
      </div>
    `;
  },

  renderTalkSummaryCard(data) {
    const summary = data.summary || '';
    if (!summary) return '';
    const structured = (typeof data.structured_json === 'object') ? (data.structured_json || {}) : {};
    const duration = structured.duration_days;
    const severity = structured.severity;
    const worsening = structured.worsening;
    const temp = structured.temperature_f;
    const reasons = Array.isArray(data.risk_reasons) ? data.risk_reasons : [];

    return `
      <div class="card mt-6" style="border-left: 5px solid var(--primary);">
        <div class="card-header">
          <h3 class="card-title">📋 Summary of Your Talk with AI Health Checker</h3>
          <span class="badge badge-info">Auto-Generated Dialogue Summary</span>
        </div>
        <p style="color: var(--gray-800); font-size: 0.95rem; line-height: 1.6; margin-top: 0.5rem;">
          ${UI.escapeHtml(summary)}
        </p>
        ${(duration !== undefined || severity || worsening !== undefined || temp) ? `
          <div class="flex gap-4 mt-3 pt-3" style="border-top: 1px solid var(--gray-200); flex-wrap: wrap; font-size: 0.85rem; color: var(--gray-700);">
            ${duration ? `<span>⏱️ <strong>Duration:</strong> ${duration} day(s)</span>` : ''}
            ${severity ? `<span>🩺 <strong>Severity:</strong> ${UI.escapeHtml(severity)}</span>` : ''}
            ${worsening !== undefined ? `<span>📈 <strong>Progression:</strong> ${worsening ? 'Getting worse' : 'Stable'}</span>` : ''}
            ${temp ? `<span>🌡️ <strong>Temperature:</strong> ${temp}°F</span>` : ''}
          </div>
        ` : ''}
        ${reasons.length > 0 ? `
          <div class="mt-3 pt-2" style="font-size: 0.85rem; color: var(--gray-600);">
            <strong>Clinical Factors Identified:</strong>
            <ul style="margin-top: 0.25rem; padding-left: 1.25rem;">
              ${reasons.map(r => `<li>${UI.escapeHtml(r)}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
    `;
  },

  /* ==========================================================
     5. DOCTOR CARDS RENDERER (Online & Offline Support)
     ========================================================== */
  renderDoctorCardsHtml(doctors, assessmentId, isHighRisk) {
    if (!doctors || doctors.length === 0) {
      return `
        <div class="p-4 text-center text-muted" style="background: var(--gray-50); border-radius: 8px;">
          No verified doctors currently registered for this specialty. You can consult any general physician.
        </div>
      `;
    }

    return doctors.slice(0, 5).map(doc => {
      const isOnline = doc.is_available === 1;
      const degree = doc.medical_degree ? `, ${doc.medical_degree}` : '';
      const avatarInitial = doc.name.replace('Dr. ', '').charAt(0) || 'D';

      return `
        <div class="doctor-card mb-3" style="align-items: center;">
          <div class="doctor-avatar">
            ${avatarInitial}
          </div>
          <div class="doctor-info" style="flex: 1;">
            <div class="flex justify-between items-center" style="flex-wrap: wrap; gap: 0.25rem;">
              <h4 class="doctor-name" style="margin: 0;">
                ${UI.escapeHtml(doc.name)}${UI.escapeHtml(degree)}
              </h4>
              ${isOnline 
                ? '<span class="doctor-status-pill doctor-status-online">🟢 Online &amp; Available</span>'
                : '<span class="doctor-status-pill doctor-status-offline">⚪ Currently Offline</span>'}
            </div>
            <div class="doctor-specialization" style="font-weight: 600; color: var(--primary);">
              🩺 ${UI.escapeHtml(doc.specialization || 'Medical Specialist')}
            </div>
            <div class="doctor-details text-xs" style="color: var(--gray-600);">
              🏥 ${UI.escapeHtml(doc.clinic_name || 'Clinic')} &bull; ${UI.escapeHtml(doc.city || 'Dehradun')}
              ${doc.fee ? `&bull; ₹${doc.fee} fee` : ''}
              ${doc.experience_years ? `&bull; ${doc.experience_years} yrs exp` : ''}
            </div>
            ${doc.distance_km !== null && doc.distance_km !== undefined ? `
              <div class="text-xs text-muted mt-1">📍 ${doc.distance_km} km away</div>
            ` : ''}
          </div>
          <div style="flex-shrink: 0; margin-left: 0.75rem;">
            ${isOnline ? `
              <button class="btn btn-primary btn-sm" onclick="Result.openConsultModal(${doc.id}, '${UI.escapeHtml(doc.name)}', false)">
                💬 Consult Now
              </button>
            ` : `
              <button class="btn btn-sm" style="background: #e11d48; color: white;" onclick="Result.openConsultModal(${doc.id}, '${UI.escapeHtml(doc.name)}', true)">
                🚨 Alert Doctor (Offline)
              </button>
            `}
          </div>
        </div>
      `;
    }).join('');
  },

  /* ==========================================================
     5. ACTIONS: HIGH-RISK ALERT & OFFLINE DOCTOR CONTACT
     ========================================================== */
  async triggerHighRiskAlert(assessmentId) {
    const btn = document.getElementById('alert-toggle-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '⏳ Activating Alert...';
    }

    const res = await API.post(`/api/assessments/${assessmentId}/alert`, {});
    if (res.ok) {
      UI.toast('🚨 High-risk health alert activated! You and emergency on-call doctors have been notified.', 'success');
      if (btn) {
        btn.className = 'btn btn-success';
        btn.innerHTML = '✅ Alert Active – You &amp; Doctors Notified';
      }
    } else {
      UI.toast(res.error || 'Failed to activate alert', 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '🔔 Alert Me &amp; Notify On-Call Doctors';
      }
    }
  },

  openConsultModal(doctorId, doctorName, isOffline) {
    this.targetDoctorId = doctorId;
    this.targetDoctorName = doctorName;
    this.targetIsOffline = isOffline;

    const modal = document.getElementById('consult-request-modal');
    const title = document.getElementById('consult-modal-title');
    const desc = document.getElementById('consult-modal-desc');
    const submitBtn = document.getElementById('consult-modal-submit-btn');

    if (title) {
      title.textContent = isOffline 
        ? `🚨 Send Emergency Alert to Dr. ${doctorName}` 
        : `Request Consultation with Dr. ${doctorName}`;
    }

    if (desc) {
      desc.innerHTML = isOffline ? `
        <div class="p-3 mb-3" style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; color: #be123c;">
          <strong>Doctor Offline Notice:</strong> Dr. ${UI.escapeHtml(doctorName)} is currently off-duty/offline. 
          Sending this request will dispatch an <strong>Urgent High-Priority Alert</strong> to their emergency queue and clinic portal. 
          You will receive an instant notification the moment they respond.
        </div>
      ` : `
        Dr. ${UI.escapeHtml(doctorName)} is online and will receive your assessment summary immediately.
      `;
    }

    if (submitBtn) {
      submitBtn.textContent = isOffline ? '🚨 Dispatch Urgent Alert' : 'Submit Consultation Request';
      submitBtn.className = isOffline ? 'btn btn-danger' : 'btn btn-primary';
    }

    UI.showModal(modal);
  },

  closeConsultModal() {
    const modal = document.getElementById('consult-request-modal');
    if (modal) UI.hideModal(modal);
  },

  async confirmConsultationRequest() {
    const consent = document.getElementById('consult-modal-consent')?.checked;
    if (!consent) {
      UI.toast('Please grant consent to share health assessment summary with the doctor', 'warning');
      return;
    }

    const payload = {
      client_id: UI.uuid(),
      doctor_id: this.targetDoctorId,
      assessment_id: parseInt(this.assessmentId),
      consent_given: true,
      is_urgent: this.targetIsOffline || (this.assessmentData && this.assessmentData.risk_level !== 'low')
    };

    const res = await API.post('/api/consultations', payload);
    this.closeConsultModal();

    if (res.ok) {
      if (this.targetIsOffline) {
        UI.toast(`🚨 Emergency alert sent to Dr. ${this.targetDoctorName}. You will be alerted when they respond.`, 'success');
      } else {
        UI.toast(`Consultation request submitted to Dr. ${this.targetDoctorName}!`, 'success');
      }
      setTimeout(() => {
        window.location.href = '/pages/consultations.html';
      }, 1500);
    } else {
      UI.toast(res.error || 'Failed to submit consultation request', 'error');
    }
  },

  ensureModalExists() {
    if (document.getElementById('consult-request-modal')) return;

    const modalDiv = document.createElement('div');
    modalDiv.id = 'consult-request-modal';
    modalDiv.className = 'modal-backdrop';
    modalDiv.style.display = 'none';
    modalDiv.innerHTML = `
      <div class="modal card" style="max-width: 500px; margin: auto;">
        <div class="modal-header flex justify-between items-center mb-4">
          <h3 id="consult-modal-title" style="margin: 0; font-size: 1.15rem;">Request Consultation</h3>
          <button type="button" class="btn btn-secondary btn-sm" onclick="Result.closeConsultModal()">✕</button>
        </div>
        <div id="consult-modal-desc" class="mb-4 text-sm"></div>
        <div class="form-group mb-4">
          <label class="flex items-center gap-2" style="cursor: pointer;">
            <input type="checkbox" id="consult-modal-consent" checked>
            <span class="text-xs" style="color: var(--gray-700);">
              I give consent to share my AI health assessment summary and symptoms with the doctor.
            </span>
          </label>
        </div>
        <div class="flex justify-end gap-3">
          <button type="button" class="btn btn-secondary" onclick="Result.closeConsultModal()">Cancel</button>
          <button type="button" id="consult-modal-submit-btn" class="btn btn-primary" onclick="Result.confirmConsultationRequest()">
            Submit Request
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(modalDiv);
  }
};
