/**
 * Authentication module for AI Health Assistant.
 * Handles login, registration, logout, session checking, and UI updates.
 */

const Auth = {
  currentUser: null,

  async getCurrentUser() {
    const res = await API.get('/api/auth/me');
    if (res.ok && res.data) {
      this.currentUser = res.data;
      return this.currentUser;
    }
    this.currentUser = null;
    return null;
  },

  async login(email, password) {
    const res = await API.post('/api/auth/login', { email, password });
    if (res.ok) {
      this.currentUser = res.data;
      return { success: true, user: res.data };
    }
    return { success: false, error: res.error || 'Login failed' };
  },

  async register(userData) {
    const res = await API.post('/api/auth/register', userData);
    if (res.ok) {
      this.currentUser = res.data;
      return { success: true, user: res.data };
    }
    return { success: false, error: res.error || 'Registration failed' };
  },

  async logout() {
    await API.post('/api/auth/logout', {});
    this.currentUser = null;
    window.location.href = '/pages/login.html';
  },

  async requireAuth(allowedRoles = []) {
    const user = await this.getCurrentUser();
    if (!user) {
      window.location.href = `/pages/login.html?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;
      return null;
    }
    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
      UI.toast('Access denied: Unauthorized role', 'error');
      if (user.role === 'doctor') {
        window.location.href = '/pages/doctor-dashboard.html';
      } else if (user.role === 'admin') {
        window.location.href = '/pages/admin.html';
      } else {
        window.location.href = '/pages/patient-dashboard.html';
      }
      return null;
    }
    return user;
  },

  setupNavbar(user) {
    const navLinks = document.getElementById('nav-links');
    if (!navLinks) return;

    const currentPath = (window.location.pathname || '').toLowerCase();
    const isActive = (target) => {
      if (target === '/' || target === '/index.html') {
        return (currentPath === '/' || currentPath.endsWith('/index.html') || currentPath === '') ? 'active' : '';
      }
      return currentPath.includes(target.toLowerCase()) ? 'active' : '';
    };

    if (!user) {
      navLinks.innerHTML = `
        <li><a href="/" class="${isActive('/')}">Home</a></li>
        <li><a href="/pages/symptom-check.html" class="${isActive('symptom-check')}">Symptom Checker</a></li>
        <li><a href="/pages/facial-care.html" class="${isActive('facial-care')}">✨ Facial Care</a></li>
        <li><a href="/pages/care-roadmap.html" class="${isActive('care-roadmap')}">🗺️ Care Roadmap</a></li>
        <li><a href="/pages/self-care.html" class="${isActive('self-care')}">Self-Care &amp; Meds</a></li>
        <li><a href="/pages/doctors.html" class="${isActive('doctors')}">Find Doctors</a></li>
        <li><a href="/pages/login.html" class="${isActive('login')}">Login</a></li>
        <li><a href="/pages/register.html" class="btn btn-primary btn-sm ${isActive('register')}" style="color: white;">Get Started</a></li>
      `;
      return;
    }

    if (user.role === 'patient') {
      navLinks.innerHTML = `
        <li><a href="/pages/patient-dashboard.html" class="${isActive('patient-dashboard')}">Dashboard</a></li>
        <li><a href="/pages/symptom-check.html" class="btn btn-primary btn-sm ${isActive('symptom-check')}" style="color: white;">🩺 Check Symptoms</a></li>
        <li><a href="/pages/facial-care.html" class="${isActive('facial-care')}">✨ Facial Care</a></li>
        <li><a href="/pages/care-roadmap.html" class="${isActive('care-roadmap')}">🗺️ Care Roadmap</a></li>
        <li><a href="/pages/self-care.html" class="${isActive('self-care')}">Self-Care Guide</a></li>
        <li><a href="/pages/doctors.html" class="${isActive('doctors')}">Find Doctors</a></li>
        <li><a href="/pages/consultations.html" class="${isActive('consultations')}">My Consultations</a></li>
        <li><a href="/pages/profile.html" class="${isActive('profile')}">Profile</a></li>
        <li>
          <button id="notification-btn" class="notification-bell" onclick="Notifications.toggleDropdown()" title="Notifications">
            🔔<span id="unread-count" class="notification-badge" data-count="0"></span>
          </button>
          <div id="notification-dropdown" class="notification-dropdown"></div>
        </li>
        <li><button onclick="Auth.logout()" class="btn btn-secondary btn-sm" title="Log out">Logout (${UI.escapeHtml(user.name)})</button></li>
      `;
    } else if (user.role === 'doctor') {
      navLinks.innerHTML = `
        <li><a href="/pages/doctor-dashboard.html" class="${isActive('doctor-dashboard') || isActive('doctor-consultation')}">Doctor Dashboard</a></li>
        <li><a href="/pages/doctors.html" class="${isActive('doctors')}">Doctor Directory</a></li>
        <li><a href="/pages/self-care.html" class="${isActive('self-care')}">Medicine Catalog</a></li>
        <li><a href="/pages/profile.html" class="${isActive('profile')}">Profile &amp; Availability</a></li>
        <li>
          <button id="notification-btn" class="notification-bell" onclick="Notifications.toggleDropdown()" title="Notifications">
            🔔<span id="unread-count" class="notification-badge" data-count="0"></span>
          </button>
          <div id="notification-dropdown" class="notification-dropdown"></div>
        </li>
        <li><button onclick="Auth.logout()" class="btn btn-secondary btn-sm" title="Log out">Logout (Dr. ${UI.escapeHtml(user.name)})</button></li>
      `;
    } else if (user.role === 'admin') {
      navLinks.innerHTML = `
        <li><a href="/pages/admin.html" class="${isActive('admin')}">Admin Portal</a></li>
        <li><a href="/pages/doctors.html" class="${isActive('doctors')}">Doctor Registry</a></li>
        <li><a href="/pages/self-care.html" class="${isActive('self-care')}">Medicine Catalog</a></li>
        <li><a href="/pages/profile.html" class="${isActive('profile')}">Profile</a></li>
        <li><button onclick="Auth.logout()" class="btn btn-secondary btn-sm" title="Log out">Logout (${UI.escapeHtml(user.name)})</button></li>
      `;
    }

    // Start notification polling if logged in
    Notifications.startPolling();
  }
};
