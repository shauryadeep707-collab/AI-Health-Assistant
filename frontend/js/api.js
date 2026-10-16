/**
 * API Helper Module for AI Health Assistant.
 * WHY this module: centralises all fetch calls so every page uses the same
 * pattern for CSRF tokens, error handling, and JSON parsing.
 */

const API = {
  csrfToken: null,

  /**
   * Fetch the CSRF token from the server (needed for POST/PUT/DELETE).
   * Called once on page load; the token is stored and reused.
   */
  async getCsrfToken() {
    if (this.csrfToken) return this.csrfToken;
    try {
      const res = await fetch('/api/auth/csrf');
      const data = await res.json();
      if (data.ok) {
        this.csrfToken = data.data.csrf_token;
      }
    } catch (e) {
      console.warn('Could not fetch CSRF token:', e);
    }
    return this.csrfToken;
  },

  /**
   * Make an API request with automatic CSRF and JSON handling.
   * @param {string} url - API endpoint (e.g. '/api/auth/login')
   * @param {object} options - fetch options (method, body, etc.)
   * @returns {object} Parsed JSON response
   */
  async request(url, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };

    // Add CSRF token for state-changing requests
    if (['POST', 'PUT', 'DELETE'].includes((options.method || 'GET').toUpperCase())) {
      const token = await this.getCsrfToken();
      if (token) {
        headers['X-CSRF-Token'] = token;
      }
    }

    try {
      const res = await fetch(url, { ...options, headers });
      const data = await res.json();
      return data;
    } catch (e) {
      // Network error - might be offline
      console.error('API request failed:', e);
      return { ok: false, error: 'Network error. You might be offline.' };
    }
  },

  // --- Convenience methods ---

  async get(url) {
    return this.request(url);
  },

  async post(url, body) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  async put(url, body) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  async delete(url) {
    return this.request(url, { method: 'DELETE' });
  },
};
