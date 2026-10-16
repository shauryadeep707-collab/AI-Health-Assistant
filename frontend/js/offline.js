/**
 * Offline Sync and IndexedDB Outbox Module for AI Health Assistant.
 * Implements a FIFO Outbox Queue in IndexedDB for reliable offline write syncing.
 */

const Offline = {
  dbName: 'AIHealthAssistantDB',
  storeName: 'outbox',
  db: null,
  isSyncing: false,

  async init() {
    this.setupNetworkListeners();
    await this.initDB();
    this.updateOnlineStatusUI();
    if (navigator.onLine) {
      this.flushOutbox();
    }
  },

  initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          // Store outbox entries sorted by timestamp
          const store = db.createObjectStore(this.storeName, { keyPath: 'id', autoIncrement: true });
          store.createIndex('client_id', 'client_id', { unique: true });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
      request.onsuccess = (e) => {
        this.db = e.target.result;
        resolve(this.db);
      };
      request.onerror = (e) => {
        console.error('IndexedDB open error:', e);
        reject(e);
      };
    });
  },

  setupNetworkListeners() {
    window.addEventListener('online', () => {
      this.updateOnlineStatusUI();
      UI.toast('You are back online! Syncing saved changes...', 'info');
      this.flushOutbox();
    });

    window.addEventListener('offline', () => {
      this.updateOnlineStatusUI();
      UI.toast('You are offline. Changes will be saved locally and synced when connection resumes.', 'warning');
    });
  },

  updateOnlineStatusUI() {
    const banner = document.getElementById('offline-banner');
    if (banner) {
      if (navigator.onLine) {
        banner.classList.remove('visible');
      } else {
        banner.classList.add('visible');
      }
    }
  },

  /**
   * Enqueue a write operation into the IndexedDB FIFO Outbox.
   * @param {string} endpoint - API route (e.g. '/api/consultations')
   * @param {string} method - 'POST' | 'PUT'
   * @param {object} payload - Request payload containing a client_id
   */
  async enqueue(endpoint, method, payload) {
    if (!this.db) await this.initDB();
    if (!payload.client_id) {
      payload.client_id = UI.uuid();
    }

    const item = {
      endpoint,
      method,
      payload,
      timestamp: Date.now(),
      retries: 0
    };

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([this.storeName], 'readwrite');
      const store = tx.objectStore(this.storeName);
      const req = store.add(item);
      req.onsuccess = () => {
        UI.toast('Saved on this device, will sync when online', 'warning');
        resolve(payload.client_id);
      };
      req.onerror = (e) => reject(e);
    });
  },

  /**
   * Flush pending outbox items FIFO (oldest first).
   */
  async flushOutbox() {
    if (!navigator.onLine || this.isSyncing) return;
    if (!this.db) await this.initDB();

    this.isSyncing = true;
    const items = await this.getAllOutboxItems();

    for (const item of items) {
      try {
        let res;
        if (item.method === 'POST') {
          res = await API.post(item.endpoint, item.payload);
        } else if (item.method === 'PUT') {
          res = await API.put(item.endpoint, item.payload);
        }

        if (res && res.ok) {
          // Server confirmed item: safely remove from outbox
          await this.removeOutboxItem(item.id);
          console.log(`Synced outbox item ${item.id} successfully.`);
        } else {
          console.warn(`Sync retry failed for item ${item.id}:`, res ? res.error : 'Unknown');
        }
      } catch (err) {
        console.error('Error syncing outbox item:', err);
      }
    }

    this.isSyncing = false;
    const remaining = await this.getAllOutboxItems();
    if (remaining.length === 0 && items.length > 0) {
      UI.toast('All offline data synced with server! (Last synced just now)', 'success');
    }
  },

  getAllOutboxItems() {
    return new Promise((resolve) => {
      if (!this.db) return resolve([]);
      const tx = this.db.transaction([this.storeName], 'readonly');
      const store = tx.objectStore(this.storeName);
      const index = store.index('timestamp');
      const req = index.getAll(); // returns items sorted by timestamp (FIFO)
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => resolve([]);
    });
  },

  removeOutboxItem(id) {
    return new Promise((resolve) => {
      if (!this.db) return resolve();
      const tx = this.db.transaction([this.storeName], 'readwrite');
      const store = tx.objectStore(this.storeName);
      const req = store.delete(id);
      req.onsuccess = () => resolve();
      req.onerror = () => resolve();
    });
  }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  Offline.init();
});
