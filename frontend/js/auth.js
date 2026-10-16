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

    if (!user) {
      navLinks.innerHTML = `
        <li><a href="/">Home</a></li>
        <li><a href="/pages/login.html">Login</a></li>
        <li><a href="/pages/register.html" class="btn btn-primary btn-sm" style="color: white;">Get Started</a></li>
      `;
      return;
    }

    if (user.role === 'patient') {
      navLinks.innerHTML = `
        <li><a href="/pages/patient-dashboard.html">Dashboard</a></li>
        <li><a href="/pages/symptom-check.html" class="btn btn-primary btn-sm" style="color: white;">Check Symptoms</a></li>
        <li><a href="/pages/doctors.html">Find Doctors</a></li>
        <li><a href="/pages/consultations.html">My Consultations</a></li>
        <li><a href="/pages/profile.html">Profile</a></li>
        <li>
          <button id="notification-btn" class="notification-bell" onclick="Notifications.toggleDropdown()">
            🔔<span id="unread-count" class="notification-badge" data-count="0"></span>
          </button>
          <div id="notification-dropdown" class="notification-dropdown"></div>
        </li>
        <li><button onclick="Auth.logout()" class="btn btn-secondary btn-sm">Logout (${UI.escapeHtml(user.name)})</button></li>
      `;
    } else if (user.role === 'doctor') {
      navLinks.innerHTML = `
        <li><a href="/pages/doctor-dashboard.html">Doctor Dashboard</a></li>
        <li><a href="/pages/profile.html">Profile & Availability</a></li>
        <li>
          <button id="notification-btn" class="notification-bell" onclick="Notifications.toggleDropdown()">
            🔔<span id="unread-count" class="notification-badge" data-count="0"></span>
          </button>
          <div id="notification-dropdown" class="notification-dropdown"></div>
        </li>
        <li><button onclick="Auth.logout()" class="btn btn-secondary btn-sm">Logout (Dr. ${UI.escapeHtml(user.name)})</button></li>
      `;
    } else if (user.role === 'admin') {
      navLinks.innerHTML = `
        <li><a href="/pages/admin.html">Admin Portal</a></li>
        <li><button onclick="Auth.logout()" class="btn btn-secondary btn-sm">Logout (${UI.escapeHtml(user.name)})</button></li>
      `;
    }

    // Start notification polling if logged in
    Notifications.startPolling();
  }
};
