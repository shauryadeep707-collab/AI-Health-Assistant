/**
 * Result Module for AI Health Assistant.
 * Renders assessment results: Low (guidance + OTC medicines),
 * Medium (nearby doctor consultation), or Urgent (112/108 emergency panel).
 */

const Result = {
  assessmentId: null,

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

    const data = res.data;
    const level = (data.risk_level || 'low').toLowerCase();

    if (level === 'urgent') {
      this.renderUrgentScreen(container, data);
    } else if (level === 'medium') {
      this.renderMediumScreen(container, data);
    } else {
      await this.renderLowScreen(container, data);
    }
  },

  renderUrgentScreen(container, data) {
    const reasons = Array.isArray(data.risk_reasons) ? data.risk_reasons : [];
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

      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">Reasons for Emergency Escalation</h3>
        </div>
        <ul style="padding-left: 1.25rem; color: var(--gray-700);">
          ${reasons.length > 0 
            ? reasons.map(r => `<li style="margin-bottom: 0.5rem;">${UI.escapeHtml(r)}</li>`).join('') 
            : '<li>Identified high-priority symptom red flags.</li>'}
        </ul>
        <div class="mt-6 flex justify-between items-center" style="flex-wrap: wrap; gap: 1rem;">
          <a href="/pages/doctors.html" class="btn btn-secondary">Find Nearest Hospital / Emergency Center</a>
          <a href="/pages/patient-dashboard.html" class="btn btn-outline">Go to Dashboard</a>
        </div>
      </div>
    `;
  },

  renderMediumScreen(container, data) {
    const reasons = Array.isArray(data.risk_reasons) ? data.risk_reasons : [];
    const category = data.category || 'general';

    container.innerHTML = `
      <div class="risk-card risk-card-medium">
        <div class="risk-icon">⚠️</div>
        <h1 class="risk-title" style="color: var(--risk-medium);">Medium Risk Assessment</h1>
        <p class="risk-description">
          Your symptoms require professional evaluation by a qualified doctor to ensure proper diagnosis and treatment.
        </p>
        <div class="mt-4">
          ${UI.riskBadge('medium')}
          <span style="margin-left: 0.75rem; font-weight: 600; color: var(--gray-700);">
            Risk Score: ${data.risk_score || 0} / 10
          </span>
        </div>
      </div>

      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">Assessment Summary</h3>
        </div>
        <p style="color: var(--gray-700); font-size: 1rem; line-height: 1.6;">
          ${UI.escapeHtml(data.summary || 'Symptoms assessed requiring doctor consultation.')}
        </p>
        <div class="mt-4">
          <strong>Key Factors Identified:</strong>
          <ul style="margin-top: 0.5rem; padding-left: 1.25rem; color: var(--gray-600);">
            ${reasons.map(r => `<li>${UI.escapeHtml(r)}</li>`).join('')}
          </ul>
        </div>

        <div class="mt-8 p-4" style="background: var(--primary-bg); border-radius: 12px; border: 1px solid var(--primary-light);">
          <h4 style="color: var(--primary-dark); font-weight: 600;">Recommended Next Step: Doctor Consultation</h4>
          <p class="text-sm mt-1" style="color: var(--gray-700);">
            Connect directly with an available local doctor. You can share this AI-generated assessment summary so the doctor is pre-briefed.
          </p>
          <div class="mt-4 flex gap-4" style="flex-wrap: wrap;">
            <a href="/pages/doctors.html?category=${encodeURIComponent(category)}&assessment_id=${data.id}" class="btn btn-primary">
              👨‍⚕️ View Nearby Available Doctors
            </a>
            <a href="/pages/patient-dashboard.html" class="btn btn-secondary">
              Back to Dashboard
            </a>
          </div>
        </div>
      </div>
    `;
  },

  async renderLowScreen(container, data) {
    const category = data.category || 'general';
    const reasons = Array.isArray(data.risk_reasons) ? data.risk_reasons : [];

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

      <!-- Home-Care Guidance Accordion -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">Home-Care Guidance & Self-Monitoring</h3>
        </div>
        <div id="guidance-accordion"></div>
      </div>

      <!-- Controlled OTC Medicine Info -->
      <div class="card mt-6">
        <div class="card-header">
          <h3 class="card-title">Controlled Over-The-Counter (OTC) Information</h3>
        </div>
        <div id="medicines-container"></div>
      </div>

      <!-- Doctor connect option -->
      <div class="card mt-6 text-center">
        <h4>Need further peace of mind?</h4>
        <p class="text-sm text-muted mt-1">You can still consult an available doctor anytime if symptoms do not improve.</p>
        <div class="mt-4 flex gap-4" style="justify-content: center;">
          <a href="/pages/doctors.html?category=${encodeURIComponent(category)}&assessment_id=${data.id}" class="btn btn-secondary">
            Find Nearby Doctors
          </a>
          <a href="/pages/patient-dashboard.html" class="btn btn-primary">
            Done & Save to Dashboard
          </a>
        </div>
      </div>
    `;

    // Render Guidance Accordion
    const accordionContainer = document.getElementById('guidance-accordion');
    if (accordionContainer && guidance) {
      if (guidance.home_care && guidance.home_care.length > 0) {
        accordionContainer.appendChild(UI.createAccordion('Recommended Self-Care Steps', guidance.home_care));
      }
      if (guidance.watch_for && guidance.watch_for.length > 0) {
        accordionContainer.appendChild(UI.createAccordion('Warning Signs to Monitor', guidance.watch_for));
      }
      if (guidance.see_doctor_if && guidance.see_doctor_if.length > 0) {
        accordionContainer.appendChild(UI.createAccordion('When to See a Doctor', guidance.see_doctor_if));
      }
    }

    // Render Medicines
    const medsContainer = document.getElementById('medicines-container');
    if (medsContainer) {
      if (medicines.length === 0) {
        medsContainer.innerHTML = '<p class="text-sm text-muted">No specific OTC medications indicated. Maintain rest and hydration.</p>';
      } else {
        medsContainer.innerHTML = medicines.map(m => `
          <div class="medicine-card">
            <div class="medicine-notice">
              ⚠️ Not a prescription — For general information only. Always read the package label or ask a pharmacist.
            </div>
            <div class="medicine-name">${UI.escapeHtml(m.name)}</div>
            <div class="medicine-purpose">${UI.escapeHtml(m.purpose)}</div>
            <p class="text-sm" style="color: var(--gray-600); margin-bottom: 0.5rem;">${UI.escapeHtml(m.general_info || '')}</p>
            
            <div style="font-size: 0.85rem; margin-top: 0.5rem;">
              <strong>Precautions:</strong>
              <ul style="padding-left: 1.25rem; color: var(--gray-600);">
                ${(m.precautions || []).map(p => `<li>${UI.escapeHtml(p)}</li>`).join('')}
              </ul>
            </div>

            <div style="font-size: 0.85rem; margin-top: 0.5rem; color: var(--error);">
              <strong>Avoid If:</strong> ${(m.avoid_if || []).map(a => UI.escapeHtml(a)).join(', ')}
            </div>
            
            <div class="text-xs text-muted mt-2">
              <em>${UI.escapeHtml(m.note || 'Follow package directions carefully.')}</em>
            </div>
          </div>
        `).join('');
      }
    }
  }
};
