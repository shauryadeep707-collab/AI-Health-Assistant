/**
 * Self-Care & Medicine Guide Module for AI Health Assistant.
 * Provides interactive search, side effects inquiry, and direct online pharmacy links.
 */

const SelfCare = {
  currentCategory: 'all',
  medicines: [],
  isLoading: false,
  searchDebounceTimer: null,

  async init() {
    const user = await Auth.getUser();
    Auth.setupNavbar(user);

    // Read URL params
    const params = new URLSearchParams(window.location.search);
    const categoryParam = params.get('category');
    const queryParam = params.get('q') || params.get('query');
    const productParam = params.get('product');

    if (categoryParam) {
      this.currentCategory = categoryParam.toLowerCase();
      this.highlightActiveCategory(this.currentCategory);
    }

    const searchInput = document.getElementById('selfcare-search-input');
    if (searchInput && queryParam) {
      searchInput.value = queryParam;
    }

    // Load initial medicines
    await this.loadMedicines();

    // If query or product was passed, auto-trigger ask query
    if (queryParam || productParam) {
      await this.askSideEffects(queryParam || `Side effects of ${productParam}`, productParam);
    }

    this.bindEvents();
  },

  bindEvents() {
    const searchInput = document.getElementById('selfcare-search-input');
    if (searchInput) {
      // Attach AI Autocomplete & Spelling Auto-Correction
      if (typeof AIAutocomplete !== 'undefined') {
        AIAutocomplete.attach(searchInput, {
          popDirection: 'down',
          onSelect: (selectedText) => {
            this.handleSearchInput(selectedText);
            this.askSideEffects(selectedText);
          }
        });
      }

      searchInput.addEventListener('input', (e) => {
        clearTimeout(this.searchDebounceTimer);
        const query = e.target.value.trim();
        this.searchDebounceTimer = setTimeout(() => {
          this.handleSearchInput(query);
        }, 300);
      });

      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const query = searchInput.value.trim();
          if (query) {
            this.askSideEffects(query);
          }
        }
      });
    }

    // Category filter pills
    document.querySelectorAll('.selfcare-category-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        const cat = e.target.getAttribute('data-category');
        this.selectCategory(cat);
      });
    });
  },

  highlightActiveCategory(category) {
    document.querySelectorAll('.selfcare-category-pill').forEach(pill => {
      const cat = pill.getAttribute('data-category');
      if (cat === category) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });
  },

  async selectCategory(category) {
    this.currentCategory = category;
    this.highlightActiveCategory(category);

    const searchInput = document.getElementById('selfcare-search-input');
    const q = searchInput ? searchInput.value.trim() : '';

    if (q) {
      await this.handleSearchInput(q);
    } else {
      await this.loadMedicines();
    }
  },

  async loadMedicines() {
    this.setLoading(true);
    const container = document.getElementById('medicines-list');
    if (!container) return;

    try {
      let endpoint = '/api/medicines';
      if (this.currentCategory && this.currentCategory !== 'all') {
        endpoint = `/api/medicines/${encodeURIComponent(this.currentCategory)}`;
      }

      const res = await API.get(endpoint);
      if (res.ok && Array.isArray(res.data)) {
        this.medicines = res.data;
        this.renderMedicines(this.medicines);
      } else {
        container.innerHTML = '<div class="card p-6 text-center text-muted">No remedies found for this category.</div>';
      }
    } catch (err) {
      console.error('Error loading medicines:', err);
      container.innerHTML = '<div class="card p-6 text-center text-error">Failed to load medicine guide. Please try again.</div>';
    } finally {
      this.setLoading(false);
    }
  },

  async handleSearchInput(query) {
    if (!query) {
      await this.loadMedicines();
      return;
    }

    this.setLoading(true);
    try {
      let endpoint = `/api/medicines/search?q=${encodeURIComponent(query)}`;
      if (this.currentCategory && this.currentCategory !== 'all') {
        endpoint += `&category=${encodeURIComponent(this.currentCategory)}`;
      }

      const res = await API.get(endpoint);
      if (res.ok && Array.isArray(res.data)) {
        this.renderMedicines(res.data);
      }
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      this.setLoading(false);
    }
  },

  async askSideEffects(query, productName = null) {
    if (!query) return;

    const answerContainer = document.getElementById('ai-answer-container');
    if (!answerContainer) return;

    answerContainer.style.display = 'block';
    answerContainer.innerHTML = `
      <div class="ai-answer-panel">
        <div class="flex items-center gap-3">
          <div class="spinner" style="width: 24px; height: 24px; border-width: 3px;"></div>
          <div>
            <strong>Analyzing Clinical Side Effects &amp; Safety Profile...</strong>
            <div class="text-xs text-muted">Checking verified OTC pharmaceutical catalog and warnings for "${UI.escapeHtml(query)}"</div>
          </div>
        </div>
      </div>
    `;

    // Scroll smoothly to answer panel
    answerContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    try {
      const res = await fetch(`/api/medicines/ask?q=${encodeURIComponent(query)}&product=${encodeURIComponent(productName || '')}`);
      const data = await res.json();

      if (data.ok && data.answer) {
        this.renderAnswer(data);
      } else {
        answerContainer.innerHTML = `
          <div class="ai-answer-panel">
            <h4>No Exact Product Found</h4>
            <p class="text-sm text-muted mt-2">${UI.escapeHtml(data.error || 'Please ask about common self-care medicines like Paracetamol, Ibuprofen, Cetirizine, Gelusil, ORS, or Cough Lozenges.')}</p>
          </div>
        `;
      }
    } catch (err) {
      console.error('Error asking side effects:', err);
      answerContainer.innerHTML = `
        <div class="ai-answer-panel">
          <p class="text-sm text-error">Unable to consult clinical knowledge base at this moment. Please try again.</p>
        </div>
      `;
    }
  },

  renderAnswer(data) {
    const answerContainer = document.getElementById('ai-answer-container');
    if (!answerContainer) return;

    const matched = data.matched_medicines || [];
    const primaryMed = matched[0];

    // Simple markdown to HTML formatter for the clinical response
    let formattedText = UI.escapeHtml(data.answer)
      .replace(/^### (.*$)/gim, '<h3 style="color: var(--primary); font-size: 1.25rem; margin-bottom: 0.75rem;">$1</h3>')
      .replace(/^#### (.*$)/gim, '<h4 style="color: var(--gray-800); font-size: 1rem; margin-top: 1rem; margin-bottom: 0.5rem;">$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    answerContainer.innerHTML = `
      <div class="ai-answer-panel">
        <div class="flex items-center justify-between mb-3" style="flex-wrap: wrap; gap: 0.5rem;">
          <div class="flex items-center gap-2">
            <span style="font-size: 1.5rem;">🛡️</span>
            <div>
              <span class="badge" style="background: #e0f2fe; color: #0369a1; font-weight: 700;">AI Side Effects &amp; Safety Advisor</span>
              <span class="text-xs text-muted ml-2">Verified OTC Clinical Guidance</span>
            </div>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('ai-answer-container').style.display='none'">✕ Dismiss</button>
        </div>

        <div class="p-3" style="background: #f8fafc; border-radius: 8px; font-size: 0.95rem; line-height: 1.6; color: var(--gray-800);">
          ${formattedText}
        </div>

        ${matched.length > 0 ? `
          <div class="direct-buy-section mt-4" style="background: white; padding: 1.25rem; border-radius: 8px; border: 1px solid #bae6fd;">
            <div class="direct-buy-title mb-3">
              <span>🛒 <strong>Direct Purchase &amp; Lab Booking Links (${matched.length} Recommended Products / Tests):</strong></span>
              <span class="text-xs text-muted">Verified pharmacy links with home delivery</span>
            </div>
            <div class="grid-2" style="gap: 1rem;">
              ${matched.map(item => `
                <div class="p-3" style="background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                  <div class="flex items-center justify-between mb-1" style="flex-wrap: wrap; gap: 4px;">
                    <strong style="font-size: 0.88rem; color: var(--gray-900);">${UI.escapeHtml(item.name)}</strong>
                    <span class="badge" style="background: #ecfdf5; color: #065f46; font-size: 0.75rem; font-weight: 700;">${UI.escapeHtml(item.price_estimate || '₹500 - ₹600')}</span>
                  </div>
                  <div class="text-xs text-muted mb-2">${UI.escapeHtml(item.purpose || '')}</div>
                  <div class="direct-buy-buttons">
                    <a href="${(item.buy_links && item.buy_links.tata_1mg) || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-1mg" style="padding: 4px 8px; font-size: 0.75rem;">
                      🛒 Tata 1mg
                    </a>
                    <a href="${(item.buy_links && item.buy_links.apollo) || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-apollo" style="padding: 4px 8px; font-size: 0.75rem;">
                      🏥 Apollo
                    </a>
                    <a href="${(item.buy_links && item.buy_links.netmeds) || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-netmeds" style="padding: 4px 8px; font-size: 0.75rem;">
                      💊 Netmeds
                    </a>
                    <a href="${(item.buy_links && item.buy_links.pharmeasy) || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-pharmeasy" style="padding: 4px 8px; font-size: 0.75rem;">
                      📦 PharmEasy
                    </a>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  },

  renderMedicines(medicines) {
    const container = document.getElementById('medicines-list');
    const countBadge = document.getElementById('results-count');
    if (!container) return;

    if (countBadge) {
      countBadge.textContent = `${medicines.length} remedies available`;
    }

    if (!medicines || medicines.length === 0) {
      container.innerHTML = `
        <div class="card p-6 text-center text-muted" style="grid-column: 1 / -1;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
          <h4>No matching medicines or self-care products found</h4>
          <p class="text-sm mt-1">Try another keyword (e.g. "fever", "paracetamol", "cough", "antacid", "pain").</p>
        </div>
      `;
      return;
    }

    container.innerHTML = medicines.map((m, idx) => {
      const se = m.side_effects || {};
      const common = Array.isArray(se.common) ? se.common : [];
      const serious = Array.isArray(se.serious) ? se.serious : [];
      const management = se.management || 'Take with water as directed.';
      const buyLinks = m.buy_links || {};
      const categoryTag = (m.category || 'general').replace('_', ' ');

      return `
        <div class="medicine-card" id="med-card-${idx}">
          <div class="medicine-header">
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="badge" style="background: #f1f5f9; color: var(--gray-700); text-transform: uppercase; font-size: 0.7rem; font-weight: 700;">
                  ${UI.escapeHtml(categoryTag)}
                </span>
                <span class="badge" style="background: #e0f2fe; color: #0284c7; font-size: 0.7rem; font-weight: 600;">
                  ✓ Non-Prescription OTC
                </span>
              </div>
              <h3 class="medicine-name">${UI.escapeHtml(m.name)}</h3>
            </div>
            <div class="medicine-price-badge">
              <span>🏷️</span> ${UI.escapeHtml(m.price_estimate || '₹25 – ₹50')}
            </div>
          </div>

          <div class="medicine-purpose">🎯 ${UI.escapeHtml(m.purpose || '')}</div>
          <p class="text-sm text-muted mb-3" style="line-height: 1.5;">${UI.escapeHtml(m.general_info || '')}</p>

          <!-- Safe Dosage Instruction -->
          <div class="p-2 mb-3" style="background: #f8fafc; border-radius: 6px; font-size: 0.85rem; border-left: 3px solid var(--primary);">
            <strong>Dosage &amp; Directions:</strong> ${UI.escapeHtml(m.dosage_guide || 'Follow package instructions carefully.')}
          </div>

          <!-- Structured Side Effects -->
          <div class="side-effects-container">
            <div class="se-section-title" style="color: var(--gray-700);">
              <span>⚡ Common Side Effects (Usually Mild):</span>
            </div>
            <div class="se-tags-wrapper">
              ${common.length > 0 ? common.map(c => `
                <span class="se-tag se-tag-common">✓ ${UI.escapeHtml(c)}</span>
              `).join('') : '<span class="text-xs text-muted">Rarely reported at recommended dosage.</span>'}
            </div>

            <div class="se-section-title" style="color: var(--error);">
              <span>🚨 Serious Red-Flag Warnings (Seek Doctor If Occurs):</span>
            </div>
            <div class="se-tags-wrapper">
              ${serious.length > 0 ? serious.map(s => `
                <span class="se-tag se-tag-serious">⚠️ ${UI.escapeHtml(s)}</span>
              `).join('') : '<span class="text-xs text-muted">Discontinue if allergic rash or facial swelling develops.</span>'}
            </div>

            <div class="se-management-box">
              <strong>💡 How to manage &amp; avoid side effects:</strong> ${UI.escapeHtml(management)}
            </div>
          </div>

          <!-- Precautions & Contraindications -->
          <div class="text-xs mb-3" style="color: var(--gray-700); line-height: 1.4;">
            ${(m.precautions && m.precautions.length) ? `
              <div style="margin-bottom: 4px;">
                <strong>Precautions:</strong> ${UI.escapeHtml(m.precautions.slice(0, 2).join(' • '))}
              </div>
            ` : ''}
            ${(m.avoid_if && m.avoid_if.length) ? `
              <div style="color: var(--error);">
                <strong>Avoid if:</strong> ${UI.escapeHtml(m.avoid_if.join(', '))}
              </div>
            ` : ''}
          </div>

          <!-- Direct Buy Buttons -->
          <div class="direct-buy-section">
            <div class="direct-buy-title">
              <span>🛒 <strong>Direct Buy Online (Verified Pharmacies):</strong></span>
              <button class="btn btn-secondary btn-sm" style="font-size: 0.75rem; padding: 2px 8px;" onclick="SelfCare.askSideEffects('What are the side effects and safety tips for ${UI.escapeHtml(m.search_term || m.name)}?', '${UI.escapeHtml(m.name)}')">
                💬 Ask Side Effects
              </button>
            </div>
            <div class="direct-buy-buttons">
              <a href="${buyLinks.tata_1mg || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-1mg" title="Search & Buy on Tata 1mg">
                🛒 Tata 1mg
              </a>
              <a href="${buyLinks.apollo || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-apollo" title="Search & Buy on Apollo Pharmacy">
                🏥 Apollo
              </a>
              <a href="${buyLinks.netmeds || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-netmeds" title="Search & Buy on Netmeds">
                💊 Netmeds
              </a>
              <a href="${buyLinks.pharmeasy || '#'}" target="_blank" rel="noopener noreferrer" class="pharmacy-buy-btn btn-pharmeasy" title="Search & Buy on PharmEasy">
                📦 PharmEasy
              </a>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  setLoading(loading) {
    this.isLoading = loading;
    const loader = document.getElementById('selfcare-loader');
    if (loader) {
      loader.style.display = loading ? 'block' : 'none';
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  SelfCare.init();
});
