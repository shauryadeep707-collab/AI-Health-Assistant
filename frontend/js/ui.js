/**
 * UI Utility Module for AI Health Assistant.
 * WHY: common UI operations (toasts, modals, navigation, loading states)
 * are shared across all pages, so they live here.
 */

const UI = {
  /**
   * Show a toast notification.
   * @param {string} message - Text to display
   * @param {string} type - 'success' | 'error' | 'warning' | 'info'
   */
  toast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message; // textContent for safety (never innerHTML)

    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(50px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  /**
   * Navigate to a page.
   * @param {string} path - Path like '/pages/login.html'
   */
  navigate(path) {
    window.location.href = path;
  },

  /**
   * Show a loading skeleton in a container.
   * @param {HTMLElement} container - Element to fill with skeletons
   * @param {number} count - Number of skeleton cards to show
   */
  showLoading(container, count = 3) {
    container.innerHTML = '';
    for (let i = 0; i < count; i++) {
      const skeleton = document.createElement('div');
      skeleton.className = 'skeleton skeleton-card';
      container.appendChild(skeleton);
    }
  },

  /**
   * Show an empty state message.
   * @param {HTMLElement} container - Element to show the empty state in
   * @param {string} icon - Emoji or icon character
   * @param {string} title - Main message
   * @param {string} hint - Secondary message
   */
  showEmpty(container, icon = '📋', title = 'Nothing here yet', hint = '') {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">${icon}</div>
        <div class="empty-state-text">${UI.escapeHtml(title)}</div>
        ${hint ? `<div class="empty-state-hint">${UI.escapeHtml(hint)}</div>` : ''}
      </div>
    `;
  },

  /**
   * Escape HTML to prevent XSS when inserting into innerHTML.
   * WHY: some UI helpers use innerHTML for structure, so we escape user data.
   * For user-generated content, prefer textContent directly.
   */
  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  },

  /**
   * Show/hide a modal overlay.
   */
  showModal(modalElement) {
    modalElement.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  },

  hideModal(modalElement) {
    modalElement.style.display = 'none';
    document.body.style.overflow = '';
  },

  /**
   * Format a timestamp into a human-readable relative time.
   */
  timeAgo(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
  },

  /**
   * Create a risk badge HTML string.
   */
  riskBadge(level) {
    const icons = { low: '✅', medium: '⚠️', urgent: '🚨' };
    const labels = { low: 'Low Risk', medium: 'Medium Risk', urgent: 'Urgent' };
    const icon = icons[level] || '❓';
    const label = labels[level] || level;
    return `<span class="risk-badge risk-badge-${UI.escapeHtml(level)}">${icon} ${UI.escapeHtml(label)}</span>`;
  },

  /**
   * Create a status badge HTML string.
   */
  statusBadge(status) {
    const labels = {
      pending: '⏳ Pending',
      accepted: '✅ Accepted',
      declined: '❌ Declined',
      completed: '✔️ Completed'
    };
    const label = labels[status] || status;
    return `<span class="status-badge status-${UI.escapeHtml(status)}">${UI.escapeHtml(label)}</span>`;
  },

  /**
   * Toggle mobile navigation menu.
   */
  toggleMenu() {
    const nav = document.querySelector('.navbar-nav');
    if (nav) nav.classList.toggle('open');
  },

  /**
   * Create an accordion item.
   */
  createAccordion(title, items) {
    const div = document.createElement('div');
    div.className = 'accordion-item';
    div.innerHTML = `
      <button class="accordion-header" onclick="this.classList.toggle('open'); this.nextElementSibling.classList.toggle('open')">
        ${UI.escapeHtml(title)}
      </button>
      <div class="accordion-body">
        <ul>
          ${items.map(item => `<li>${UI.escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
    `;
    return div;
  },

  /**
   * Generate a UUID v4 for client_id (offline sync).
   * WHY: each write gets a unique client_id so retries are idempotent.
   */
  uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }
};
