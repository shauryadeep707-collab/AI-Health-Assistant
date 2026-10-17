/**
 * Consultations and Doctor Dashboard Module for AI Health Assistant.
 * Handles patient consultation lists, doctor FIFO queue, request reviews,
 * and advice submission.
 */

const Consultations = {
  consultations: [],

  async initPatientView() {
    const user = await Auth.requireAuth(['patient']);
    if (!user) return;
    Auth.setupNavbar(user);
    await this.fetchConsultations();
  },

  async initDoctorDashboard() {
    const user = await Auth.requireAuth(['doctor']);
    if (!user) return;
    Auth.setupNavbar(user);
    this.setupDoctorAvailabilityToggle(user);
    await this.fetchDoctorConsultations();
  },

  async initDoctorConsultationView() {
    const user = await Auth.requireAuth(['doctor']);
    if (!user) return;
    Auth.setupNavbar(user);

    const params = new URLSearchParams(window.location.search);
    const consultationId = params.get('id');
    if (!consultationId) {
      window.location.href = '/pages/doctor-dashboard.html';
      return;
    }
    await this.loadDoctorConsultationDetail(consultationId);
  },

  async fetchConsultations() {
    const container = document.getElementById('consultations-list');
    if (container) UI.showLoading(container, 3);

    const res = await API.get('/api/consultations');
    if (res.ok && res.data) {
      this.consultations = res.data;
      this.renderPatientConsultations();
    } else {
      if (container) UI.showEmpty(container, '📋', 'No consultations requested yet.');
    }
  },

  renderPatientConsultations() {
    const container = document.getElementById('consultations-list');
    if (!container) return;

    if (this.consultations.length === 0) {
      UI.showEmpty(container, '👨‍⚕️', 'No consultation requests found', 'When your risk assessment is Medium, you can request a consultation with a local doctor.');
      return;
    }

    container.innerHTML = this.consultations.map(c => `
      <div class="card mb-4">
        <div class="card-header">
          <div>
            <h4 class="card-title">${UI.escapeHtml(c.doctor_name || 'Doctor')}</h4>
            <span class="text-sm text-primary">${UI.escapeHtml(c.specialization || 'General Physician')} &bull; ${UI.escapeHtml(c.clinic_name || '')}</span>
          </div>
          <div>
            ${UI.statusBadge(c.status)}
          </div>
        </div>

        <div class="text-sm text-muted mb-2">
          Requested on: ${new Date(c.created_at).toLocaleString()}
        </div>

        ${c.doctor_advice ? `
          <div class="p-4 mt-3" style="background: var(--risk-low-bg); border-left: 4px solid var(--success); border-radius: 8px;">
            <strong style="color: var(--success); font-size: 0.95rem;">👨‍⚕️ Doctor's Professional Advice:</strong>
            <p style="margin-top: 0.5rem; color: var(--gray-800); white-space: pre-wrap;">${UI.escapeHtml(c.doctor_advice)}</p>
          </div>
        ` : (c.status === 'pending' ? `
          <div class="p-3 mt-2" style="background: var(--risk-medium-bg); border-radius: 8px; font-size: 0.875rem; color: #92400e;">
            ⏳ Your request is in the doctor's queue. You will receive an in-app notification when the doctor responds.
          </div>
        ` : (c.status === 'declined' ? `
          <div class="p-3 mt-2" style="background: var(--risk-urgent-bg); border-radius: 8px; font-size: 0.875rem; color: var(--error);">
            ❌ Doctor was unavailable. Please select another nearby doctor.
          </div>
        ` : ''))}

        <div class="mt-4 flex gap-2">
          <a href="/pages/result.html?id=${c.assessment_id}" class="btn btn-secondary btn-sm">
            View AI Assessment
          </a>
        </div>
      </div>
    `).join('');
  },

  async fetchDoctorConsultations() {
    const res = await API.get('/api/consultations');
    if (res.ok && res.data) {
      this.consultations = res.data;
      this.renderDoctorDashboardStats();
      this.renderDoctorQueue();
    }
  },

  renderDoctorDashboardStats() {
    const pending = this.consultations.filter(c => c.status === 'pending').length;
    const accepted = this.consultations.filter(c => c.status === 'accepted').length;
    const completed = this.consultations.filter(c => c.status === 'completed').length;

    const elPending = document.getElementById('stat-pending');
    const elAccepted = document.getElementById('stat-accepted');
    const elCompleted = document.getElementById('stat-completed');

    if (elPending) elPending.textContent = pending;
    if (elAccepted) elAccepted.textContent = accepted;
    if (elCompleted) elCompleted.textContent = completed;
  },

  renderDoctorQueue() {
    const container = document.getElementById('doctor-queue');
    if (!container) return;

    if (this.consultations.length === 0) {
      UI.showEmpty(container, '🏥', 'No patient consultations in your queue.');
      return;
    }

    container.innerHTML = this.consultations.map(c => `
      <div class="card mb-4" style="border-left: 5px solid ${c.status === 'pending' ? 'var(--warning)' : (c.status === 'completed' ? 'var(--success)' : 'var(--primary)')};">
        <div class="card-header">
          <div>
            <h4 class="card-title">Patient: ${UI.escapeHtml(c.patient_name || 'Patient')}</h4>
            <span class="text-sm text-muted">Category: ${UI.escapeHtml(c.category || 'General')} &bull; Risk: ${UI.riskBadge(c.risk_level || 'medium')}</span>
          </div>
          <div>
            ${UI.statusBadge(c.status)}
          </div>
        </div>

        <p class="text-sm" style="color: var(--gray-700); margin: 0.5rem 0;">
          <strong>AI Summary:</strong> ${UI.escapeHtml(c.summary || 'Summary not available')}
        </p>

        <div class="text-xs text-muted mb-4">
          FIFO Queue Position &bull; Received: ${UI.timeAgo(c.created_at)} (${new Date(c.created_at).toLocaleTimeString()})
        </div>

        <div class="flex gap-2">
          <a href="/pages/doctor-consultation.html?id=${c.id}" class="btn btn-primary btn-sm">
            Review Case & Advice
          </a>
        </div>
      </div>
    `).join('');
  },

  setupDoctorAvailabilityToggle(user) {
    const toggle = document.getElementById('availability-toggle');
    const statusText = document.getElementById('availability-text');
    if (!toggle) return;

    const isAvailable = user.profile?.is_available !== 0;
    toggle.checked = isAvailable;
    if (statusText) statusText.textContent = isAvailable ? 'Available for Consultations' : 'Unavailable';

    toggle.addEventListener('change', async () => {
      const newState = toggle.checked;
      if (statusText) statusText.textContent = newState ? 'Available for Consultations' : 'Unavailable';

      if (!navigator.onLine) {
        await Offline.enqueue('/api/doctor/availability', 'PUT', { is_available: newState });
        return;
      }
      await API.put('/api/doctor/availability', { is_available: newState });
      UI.toast(`Availability status updated: ${newState ? 'Available' : 'Unavailable'}`, 'info');
    });
  },

  async loadDoctorConsultationDetail(id) {
    const res = await API.get(`/api/consultations/${id}`);
    const container = document.getElementById('consultation-detail');
    if (!container) return;

    if (!res.ok || !res.data) {
      container.innerHTML = '<div class="card p-6 text-center">Consultation not found.</div>';
      return;
    }

    const { consultation, patient, assessment, messages } = res.data;

    const structured = (assessment && typeof assessment.structured_json === 'object') ? (assessment.structured_json || {}) : {};
    const riskReasons = Array.isArray(assessment?.risk_reasons) ? assessment.risk_reasons : [];
    const mainSymptoms = Array.isArray(structured.main_symptoms) ? structured.main_symptoms.join(', ') : (assessment?.category || 'General');
    const otherSymptoms = Array.isArray(structured.other_symptoms) && structured.other_symptoms.length > 0 ? structured.other_symptoms.join(', ') : 'None reported';
    const medsTaken = Array.isArray(structured.medicines_taken) && structured.medicines_taken.length > 0 ? structured.medicines_taken.join(', ') : 'None';

    container.innerHTML = `
      <div class="card mb-6">
        <div class="card-header">
          <div>
            <h2 class="card-title">Patient Case: ${UI.escapeHtml(patient?.name || 'Patient')}</h2>
            <div class="text-sm text-muted">
              Age: ${patient?.age || 'N/A'} &bull; Gender: ${patient?.gender || 'N/A'} &bull; Phone: ${patient?.phone || 'N/A'}
            </div>
            <div class="text-xs text-muted mt-1">
              Chronic Conditions: ${UI.escapeHtml(patient?.chronic_conditions || 'None')} &bull; Allergies: ${UI.escapeHtml(patient?.allergies || 'None')}
            </div>
          </div>
          <div>
            ${UI.statusBadge(consultation.status)}
          </div>
        </div>

        <!-- Automatic Dispatch Status Banner -->
        <div class="p-3 mb-4 flex items-center justify-between" style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px;">
          <div class="text-xs" style="color: #065f46; font-weight: 600;">
            ✓ Automatically routed &amp; delivered to your queue on ${consultation.created_at ? new Date(consultation.created_at).toLocaleString() : 'Just now'}
          </div>
          <span class="badge" style="background: #10b981; color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px;">AUTO-ROUTED</span>
        </div>

        <!-- Patient-Checker Talk Summary Box -->
        <div class="p-4 mb-4" style="background: var(--primary-bg); border-radius: 8px; border: 1px solid #bfdbfe;">
          <div class="flex items-center justify-between mb-2">
            <h4 style="color: var(--primary-dark); font-size: 1rem; margin: 0;">
              📋 Summary of Patient Talk with AI Health Checker
            </h4>
            <div>
              ${UI.riskBadge(assessment?.risk_level || 'medium')}
              <span class="text-xs text-muted" style="margin-left: 0.5rem; font-weight: 600;">Score: ${assessment?.risk_score || 0}/10</span>
            </div>
          </div>

          <p class="text-sm mt-2" style="color: var(--gray-800); line-height: 1.6; font-weight: 500;">
            ${UI.escapeHtml(assessment?.summary || 'No dialogue summary generated.')}
          </p>

          <!-- Dialogue Clinical Parameters -->
          <div class="grid grid-2 gap-3 mt-4 pt-3" style="border-top: 1px solid #dbeafe; font-size: 0.85rem;">
            <div>
              <span class="text-muted">Chief Complaint:</span> 
              <strong style="color: var(--gray-800);">${UI.escapeHtml(mainSymptoms)}</strong>
            </div>
            <div>
              <span class="text-muted">Duration &amp; Severity:</span> 
              <strong style="color: var(--gray-800);">${structured.duration_days || 1} day(s) &bull; ${(structured.severity || 'moderate').toUpperCase()}</strong>
            </div>
            <div>
              <span class="text-muted">Progression:</span> 
              <strong style="color: var(--gray-800);">${structured.worsening ? '⚠️ Getting worse' : 'Stable'}</strong>
              ${structured.temperature_f ? ` &bull; Temp: <strong>${structured.temperature_f}°F</strong>` : ''}
            </div>
            <div>
              <span class="text-muted">Prior Meds Taken:</span> 
              <strong style="color: var(--gray-800);">${UI.escapeHtml(medsTaken)}</strong>
            </div>
            <div style="grid-column: 1 / -1;">
              <span class="text-muted">Associated Symptoms:</span> 
              <span style="color: var(--gray-800);">${UI.escapeHtml(otherSymptoms)}</span>
            </div>
            ${riskReasons.length > 0 ? `
              <div style="grid-column: 1 / -1;">
                <span class="text-muted">Clinical Factors:</span> 
                <span style="color: var(--risk-urgent); font-weight: 500;">${riskReasons.map(r => UI.escapeHtml(r)).join('; ')}</span>
              </div>
            ` : ''}
          </div>
        </div>

        <div class="mb-4">
          <div class="text-xs" style="color: var(--success); font-weight: 600;">
            ✓ Patient Consent Verified: Authorized data sharing on ${consultation.consent_at ? new Date(consultation.consent_at).toLocaleString() : 'N/A'}
          </div>
        </div>

        <!-- Chat Transcript Accordion -->
        <div class="accordion-item mb-4">
          <button class="accordion-header" onclick="this.classList.toggle('open'); this.nextElementSibling.classList.toggle('open')">
            💬 View Complete Patient &amp; Checker Talk Transcript (${messages?.length || 0} messages)
          </button>
          <div class="accordion-body">
            <div style="display: flex; flex-direction: column; gap: 0.5rem; padding: 0.5rem 0;">
              ${(messages || []).map(m => `
                <div style="font-size: 0.85rem; padding: 0.5rem 0.75rem; border-radius: 6px; background: ${m.role === 'user' ? 'var(--primary-bg)' : 'var(--gray-100)'};">
                  <strong>${m.role === 'user' ? '👤 Patient' : (m.role === 'assistant' ? '🤖 AI Health Checker' : 'System')}:</strong> ${UI.escapeHtml(m.content)}
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Doctor Advice & Actions -->
        <div class="mt-6 pt-4" style="border-top: 1px solid var(--gray-200);">
          <h3 style="font-size: 1.1rem; margin-bottom: 0.75rem;">Doctor's Review & Advice</h3>
          
          <div class="form-group">
            <label class="form-label">Professional Medical Advice / Prescription Notes</label>
            <textarea id="doctor-advice-text" class="form-textarea" placeholder="Enter clinical guidance, OTC suggestions, follow-up advice or instructions...">${UI.escapeHtml(consultation.doctor_advice || '')}</textarea>
          </div>

          <div class="flex gap-3 mt-4" style="flex-wrap: wrap;">
            ${consultation.status === 'pending' ? `
              <button class="btn btn-success" onclick="Consultations.updateStatus(${consultation.id}, 'accepted')">
                Accept Case
              </button>
              <button class="btn btn-danger" onclick="Consultations.updateStatus(${consultation.id}, 'declined')">
                Decline Case
              </button>
            ` : (consultation.status === 'accepted' ? `
              <button class="btn btn-primary" onclick="Consultations.updateStatus(${consultation.id}, 'completed')">
                Complete Consultation & Send Advice
              </button>
            ` : `
              <button class="btn btn-secondary" onclick="Consultations.saveAdviceOnly(${consultation.id})">
                Update Advice
              </button>
            `)}
            <a href="/pages/doctor-dashboard.html" class="btn btn-secondary">Back to Queue</a>
          </div>
        </div>
      </div>
    `;
  },

  async updateStatus(id, newStatus) {
    const adviceText = document.getElementById('doctor-advice-text')?.value || '';
    const payload = {
      status: newStatus,
      doctor_advice: adviceText
    };

    if (!navigator.onLine) {
      await Offline.enqueue(`/api/consultations/${id}/status`, 'PUT', payload);
      UI.toast(`Status updated to ${newStatus} (Saved offline)`, 'info');
      setTimeout(() => window.location.href = '/pages/doctor-dashboard.html', 1500);
      return;
    }

    const res = await API.put(`/api/consultations/${id}/status`, payload);
    if (res.ok) {
      UI.toast(`Consultation marked as ${newStatus}! Patient notified.`, 'success');
      setTimeout(() => window.location.href = '/pages/doctor-dashboard.html', 1500);
    } else {
      UI.toast(res.error || 'Failed to update consultation', 'error');
    }
  },

  async saveAdviceOnly(id) {
    const adviceText = document.getElementById('doctor-advice-text')?.value || '';
    const res = await API.put(`/api/consultations/${id}/status`, { doctor_advice: adviceText });
    if (res.ok) {
      UI.toast('Doctor advice updated successfully!', 'success');
    } else {
      UI.toast(res.error || 'Failed to update advice', 'error');
    }
  }
};
