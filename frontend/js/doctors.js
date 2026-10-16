/**
 * Doctors Module for AI Health Assistant.
 * Handles nearby doctor directory, Leaflet map integration,
 * specialization filters, and consultation request modal with consent.
 */

const Doctors = {
  doctors: [],
  map: null,
  markers: [],
  userLocation: { lat: 30.3165, lng: 78.0322 }, // Dehradun default center
  selectedDoctor: null,
  assessmentId: null,

  async init() {
    const user = await Auth.requireAuth(['patient']);
    if (!user) return;
    Auth.setupNavbar(user);

    const params = new URLSearchParams(window.location.search);
    this.assessmentId = params.get('assessment_id');
    const category = params.get('category');

    // Pre-select specialization if category provided
    if (category) {
      const specMap = {
        fever: 'General Physician',
        cold_cough: 'General Physician',
        headache: 'Neurologist',
        sore_throat: 'ENT Specialist',
        stomach: 'Gastroenterologist'
      };
      const select = document.getElementById('filter-specialization');
      if (select && specMap[category]) {
        select.value = specMap[category];
      }
    }

    this.initMap();
    this.setupListeners();
    this.requestLocation();
  },

  initMap() {
    const mapElement = document.getElementById('doctor-map');
    if (!mapElement || typeof L === 'undefined') return;

    // Initialize Leaflet map centered at Dehradun
    this.map = L.map('doctor-map').setView([this.userLocation.lat, this.userLocation.lng], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);
  },

  requestLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.userLocation = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude
          };
          if (this.map) {
            this.map.setView([this.userLocation.lat, this.userLocation.lng], 13);
            L.circleMarker([this.userLocation.lat, this.userLocation.lng], {
              radius: 8,
              color: '#0891b2',
              fillColor: '#22d3ee',
              fillOpacity: 0.8
            }).addTo(this.map).bindPopup('Your Current Location');
          }
          this.fetchDoctors();
        },
        (err) => {
          console.warn('Geolocation denied or unavailable:', err);
          this.fetchDoctors(); // Fallback to default coordinates
        }
      );
    } else {
      this.fetchDoctors();
    }
  },

  setupListeners() {
    const filterBtn = document.getElementById('filter-submit');
    if (filterBtn) {
      filterBtn.addEventListener('click', () => this.fetchDoctors());
    }

    const modalForm = document.getElementById('consultation-form');
    if (modalForm) {
      modalForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitConsultationRequest();
      });
    }
  },

  async fetchDoctors() {
    const listContainer = document.getElementById('doctors-list');
    if (listContainer) UI.showLoading(listContainer, 3);

    const spec = document.getElementById('filter-specialization')?.value || '';
    const city = document.getElementById('filter-city')?.value || '';
    const radius = document.getElementById('filter-radius')?.value || 50;

    const query = new URLSearchParams({
      lat: this.userLocation.lat,
      lng: this.userLocation.lng,
      radius_km: radius,
      specialization: spec,
      city: city
    });

    const res = await API.get(`/api/doctors/nearby?${query.toString()}`);
    if (res.ok && res.data) {
      this.doctors = res.data;
      this.renderDoctorsList();
      this.renderMapMarkers();
    } else {
      if (listContainer) UI.showEmpty(listContainer, '🔍', 'No doctors found matching filters');
    }
  },

  renderDoctorsList() {
    const container = document.getElementById('doctors-list');
    if (!container) return;

    if (this.doctors.length === 0) {
      UI.showEmpty(container, '👨‍⚕️', 'No available doctors found nearby', 'Try widening your search radius or clearing specialization filters.');
      return;
    }

    container.innerHTML = this.doctors.map(doc => `
      <div class="doctor-card">
        <div class="doctor-avatar">
          ${doc.name.replace('Dr. ', '').charAt(0)}
        </div>
        <div class="doctor-info">
          <div class="flex justify-between items-center">
            <h4 class="doctor-name">${UI.escapeHtml(doc.name)}</h4>
            ${doc.distance_km !== null ? `<span class="doctor-distance">📍 ${doc.distance_km} km</span>` : ''}
          </div>
          <div class="doctor-specialization">${UI.escapeHtml(doc.specialization)}</div>
          <div class="doctor-details">
            🏥 ${UI.escapeHtml(doc.clinic_name || 'Clinic')} &bull; ${UI.escapeHtml(doc.city || 'Dehradun')}
          </div>
          <div class="doctor-details">
            ⭐ ${doc.experience_years || 5}+ yrs exp &bull; ₹${doc.fee || 500} consultation fee
          </div>
          <div class="doctor-details text-xs" style="color: var(--success); font-weight: 500;">
            🕒 Available: ${UI.escapeHtml(doc.available_days || 'Mon-Fri')} (${doc.available_from || '09:00'} - ${doc.available_to || '17:00'})
          </div>
          <div class="mt-4 flex gap-2">
            <button class="btn btn-primary btn-sm" onclick="Doctors.openRequestModal(${doc.id})">
              Request Consultation
            </button>
            <button class="btn btn-secondary btn-sm" onclick="Doctors.focusDoctorOnMap(${doc.lat}, ${doc.lng}, '${UI.escapeHtml(doc.name)}')">
              View on Map
            </button>
          </div>
        </div>
      </div>
    `).join('');
  },

  renderMapMarkers() {
    if (!this.map || typeof L === 'undefined') return;

    // Clear existing markers
    this.markers.forEach(m => this.map.removeLayer(m));
    this.markers = [];

    this.doctors.forEach(doc => {
      if (doc.lat && doc.lng) {
        const marker = L.marker([doc.lat, doc.lng]).addTo(this.map);
        marker.bindPopup(`
          <strong>${UI.escapeHtml(doc.name)}</strong><br>
          ${UI.escapeHtml(doc.specialization)}<br>
          <em>${UI.escapeHtml(doc.clinic_name || '')}</em><br>
          <button class="btn btn-primary btn-sm mt-2" onclick="Doctors.openRequestModal(${doc.id})">Consult</button>
        `);
        this.markers.push(marker);
      }
    });
  },

  focusDoctorOnMap(lat, lng, name) {
    if (this.map && lat && lng) {
      this.map.setView([lat, lng], 15);
      const marker = this.markers.find(m => {
        const pos = m.getLatLng();
        return Math.abs(pos.lat - lat) < 0.0001 && Math.abs(pos.lng - lng) < 0.0001;
      });
      if (marker) marker.openPopup();
    }
  },

  openRequestModal(doctorId) {
    this.selectedDoctor = this.doctors.find(d => d.id === doctorId);
    if (!this.selectedDoctor) return;

    const modal = document.getElementById('consultation-modal');
    const doctorNameSpan = document.getElementById('modal-doctor-name');
    const specSpan = document.getElementById('modal-doctor-spec');

    if (doctorNameSpan) doctorNameSpan.textContent = this.selectedDoctor.name;
    if (specSpan) specSpan.textContent = `${this.selectedDoctor.specialization} (${this.selectedDoctor.clinic_name || ''})`;

    UI.showModal(modal);
  },

  closeModal() {
    const modal = document.getElementById('consultation-modal');
    if (modal) UI.hideModal(modal);
  },

  async submitConsultationRequest() {
    if (!this.selectedDoctor) return;

    const consentBox = document.getElementById('modal-consent');
    if (!consentBox || !consentBox.checked) {
      UI.toast('Please check the consent box to share your summary with the doctor', 'warning');
      return;
    }

    if (!this.assessmentId) {
      UI.toast('Please complete a symptom check assessment first', 'warning');
      window.location.href = '/pages/symptom-check.html';
      return;
    }

    const clientId = UI.uuid();
    const payload = {
      client_id: clientId,
      doctor_id: this.selectedDoctor.id,
      assessment_id: parseInt(this.assessmentId),
      consent_given: true
    };

    if (!navigator.onLine) {
      await Offline.enqueue('/api/consultations', 'POST', payload);
      this.closeModal();
      UI.toast('Consultation request saved offline! It will be sent to the doctor when reconnected.', 'info');
      setTimeout(() => {
        window.location.href = '/pages/consultations.html';
      }, 1500);
      return;
    }

    const res = await API.post('/api/consultations', payload);
    if (res.ok) {
      this.closeModal();
      UI.toast('Consultation request submitted! The doctor has been notified.', 'success');
      setTimeout(() => {
        window.location.href = '/pages/consultations.html';
      }, 1500);
    } else {
      UI.toast(res.error || 'Failed to submit consultation request', 'error');
    }
  }
};
