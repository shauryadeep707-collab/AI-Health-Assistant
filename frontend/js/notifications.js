/**
 * In-app Notification Module for AI Health Assistant.
 * Polls every 10 seconds for unread notifications, updates badge count,
 * and handles notification dropdown actions.
 */

const Notifications = {
  pollInterval: null,

  startPolling() {
    this.fetchNotifications();
    if (!this.pollInterval) {
      this.pollInterval = setInterval(() => this.fetchNotifications(), 10000);
    }
  },

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  },

  async fetchNotifications() {
    if (!navigator.onLine) return;
    const res = await API.get('/api/notifications');
    if (res.ok && res.data) {
      this.renderBadge(res.data);
      this.renderDropdown(res.data);
    }
  },

  renderBadge(notifications) {
    const badge = document.getElementById('unread-count');
    if (!badge) return;
    const unreadCount = notifications.filter(n => !n.is_read).length;
    badge.textContent = unreadCount > 0 ? (unreadCount > 9 ? '9+' : unreadCount) : '';
    badge.setAttribute('data-count', unreadCount);
  },

  renderDropdown(notifications) {
    const dropdown = document.getElementById('notification-dropdown');
    if (!dropdown) return;

    if (notifications.length === 0) {
      dropdown.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--gray-500); font-size: 0.875rem;">No notifications yet.</div>';
      return;
    }

    dropdown.innerHTML = notifications.map(n => `
      <div class="notification-item ${n.is_read ? '' : 'unread'}" onclick="Notifications.handleClick(${n.id}, '${n.link || ''}')">
        <div>${UI.escapeHtml(n.text)}</div>
        <div class="notification-time">${UI.timeAgo(n.created_at)}</div>
      </div>
    `).join('');
  },

  toggleDropdown() {
    const dropdown = document.getElementById('notification-dropdown');
    if (dropdown) {
      dropdown.classList.toggle('open');
    }
  },

  async handleClick(id, link) {
    await API.post(`/api/notifications/${id}/read`, {});
    this.fetchNotifications();
    if (link) {
      window.location.href = link;
    }
  }
};
