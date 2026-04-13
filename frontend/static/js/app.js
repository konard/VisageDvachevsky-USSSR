/**
 * СССР - Лица Эпохи
 * Main JavaScript — Enhanced Edition
 */

// ===== STATE =====
let allLeaders = [];
let currentView = 'grid';   // 'grid' | 'timeline'
let currentFilter = 'all';  // 'all' | 'early' | 'mid' | 'late'

// ===== DOM REFS =====
const leadersGrid      = document.getElementById('leadersGrid');
const timelineView     = document.getElementById('timelineView');
const timelineItems    = document.getElementById('timelineItems');
const loading          = document.getElementById('loading');
const noResults        = document.getElementById('noResults');
const searchInput      = document.getElementById('searchInput');
const searchBtn        = document.getElementById('searchBtn');
const clearSearchBtn   = document.getElementById('clearSearch');
const leaderModal      = document.getElementById('leaderModal');
const videoModal       = document.getElementById('videoModal');
const closeModal       = document.getElementById('closeModal');
const closeVideoModal  = document.getElementById('closeVideoModal');
const modalBody        = document.getElementById('modalBody');
const leaderVideo      = document.getElementById('leaderVideo');
const videoTitle       = document.getElementById('videoTitle');
const toast            = document.getElementById('toast');
const gridViewBtn      = document.getElementById('gridViewBtn');
const timelineViewBtn  = document.getElementById('timelineViewBtn');
const leaderCountEl    = document.getElementById('leaderCount');

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    loadLeaders();
    setupEventListeners();
});

// ===== LEADERS DATA LOADING =====
async function loadLeaders() {
    try {
        showLoading(true);
        const response = await fetch('/api/leaders');

        if (!response.ok) throw new Error('Failed to fetch leaders');

        allLeaders = await response.json();

        // Update count in header
        if (leaderCountEl) leaderCountEl.textContent = allLeaders.length;

        renderLeaders(allLeaders);
    } catch (error) {
        console.error('Error loading leaders:', error);
        showToast('Ошибка загрузки данных. Проверьте подключение.', 'error');
    } finally {
        showLoading(false);
    }
}

// ===== ERA CLASSIFICATION =====
function getEra(leader) {
    const year = leader.years_in_power_start || leader.birth_year;
    if (year < 1953) return 'early';
    if (year < 1985) return 'mid';
    return 'late';
}

function getEraLabel(era) {
    return { early: 'Ранняя эпоха', mid: 'Середина', late: 'Поздний СССР' }[era] || '';
}

// ===== RENDER LEADERS =====
function renderLeaders(leaders) {
    const filtered = filterLeaders(leaders, currentFilter);

    if (currentView === 'timeline') {
        renderTimeline(filtered);
    } else {
        renderGrid(filtered);
    }
}

function filterLeaders(leaders, filter) {
    if (filter === 'all') return leaders;
    return leaders.filter(l => getEra(l) === filter);
}

function renderGrid(leaders) {
    leadersGrid.innerHTML = '';
    timelineView.style.display = 'none';
    leadersGrid.style.display = '';

    if (leaders.length === 0) {
        noResults.style.display = 'block';
        return;
    }

    noResults.style.display = 'none';

    leaders.forEach((leader, idx) => {
        const card = createLeaderCard(leader, idx);
        leadersGrid.appendChild(card);
    });
}

function renderTimeline(leaders) {
    timelineItems.innerHTML = '';
    leadersGrid.style.display = 'none';
    timelineView.style.display = 'block';

    if (leaders.length === 0) {
        noResults.style.display = 'block';
        return;
    }

    noResults.style.display = 'none';

    // Sort by birth year for timeline
    const sorted = [...leaders].sort((a, b) => a.birth_year - b.birth_year);

    sorted.forEach(leader => {
        const item = createTimelineItem(leader);
        timelineItems.appendChild(item);
    });
}

// ===== CREATE LEADER CARD =====
function createLeaderCard(leader, idx) {
    const card = document.createElement('div');
    card.className = 'leader-card';
    card.style.setProperty('--card-index', idx);

    const era = getEra(leader);
    const eraLabel = getEraLabel(era);
    const yearsText = leader.death_year
        ? `${leader.birth_year} – ${leader.death_year}`
        : `${leader.birth_year} – настоящее время`;

    // Calculate years in power for quick fact
    let yearsInPower = '';
    if (leader.years_in_power) {
        const start = leader.years_in_power.start;
        const end   = leader.years_in_power.end || '1991';
        yearsInPower = `${start}–${end}`;
    } else if (leader.birth_year && leader.death_year) {
        yearsInPower = '—';
    }

    // Significance dots (out of 5)
    const significance = leader.historical_significance || 5;
    const sigDots = Array.from({ length: 5 }, (_, i) =>
        `<span class="sig-dot${i < Math.round(significance / 2) ? ' active' : ''}"></span>`
    ).join('');

    card.innerHTML = `
        <div class="leader-card-header">
            <div class="significance-dots">${sigDots}</div>
            <span class="era-badge era-${era}">${eraLabel}</span>
            <h2 class="leader-name">${leader.name_ru}</h2>
            <p class="leader-years">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity:0.7;vertical-align:-2px">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                ${yearsText}
            </p>
        </div>
        <div class="leader-card-body">
            <p class="leader-position">${leader.position}</p>
            <p class="leader-achievements">${truncateText(leader.achievements, 140)}</p>
        </div>
        <div class="leader-quick-facts">
            <div class="quick-fact">
                <span class="quick-fact-icon">🏛️</span>
                <span class="quick-fact-label">Родина</span>
                <span class="quick-fact-value">${leader.birth_place ? leader.birth_place.split('(')[0].trim() : '—'}</span>
            </div>
            <div class="quick-fact">
                <span class="quick-fact-icon">⚡</span>
                <span class="quick-fact-label">Власть</span>
                <span class="quick-fact-value">${yearsInPower || '—'}</span>
            </div>
            <div class="quick-fact">
                <span class="quick-fact-icon">📖</span>
                <span class="quick-fact-label">Эпоха</span>
                <span class="quick-fact-value">${eraLabel}</span>
            </div>
        </div>
        <div class="leader-card-footer">
            <button class="btn btn-primary" onclick="showLeaderDetails(${leader.id})">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                Подробнее
            </button>
            <button class="btn btn-secondary" onclick="playVideo(${leader.video_id}, '${escapeAttr(leader.name_ru)}')">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                Видео
            </button>
        </div>
    `;

    return card;
}

// ===== CREATE TIMELINE ITEM =====
function createTimelineItem(leader) {
    const item = document.createElement('div');
    item.className = 'timeline-item';

    const yearsInPower = leader.years_in_power
        ? `${leader.years_in_power.start}–${leader.years_in_power.end || '1991'}`
        : `${leader.birth_year}–${leader.death_year || 'н.в.'}`;

    item.innerHTML = `
        <div class="timeline-card" onclick="showLeaderDetails(${leader.id})">
            <div class="timeline-year">${yearsInPower}</div>
            <div class="timeline-name">${leader.name_ru}</div>
            <div class="timeline-position">${leader.position}</div>
        </div>
        <div class="timeline-dot"></div>
        <div style="width:calc(50% - 40px)"></div>
    `;

    return item;
}

// ===== SHOW LEADER DETAILS MODAL =====
async function showLeaderDetails(leaderId) {
    try {
        const leader = allLeaders.find(l => l.id === leaderId);
        if (!leader) return;

        // Render skeleton first
        leaderModal.classList.add('active');
        modalBody.innerHTML = buildModalSkeleton();

        // Fetch AI-generated facts in parallel
        let facts = [];
        try {
            const factsResponse = await fetch(`/api/leaders/${leaderId}/facts`);
            const factsData = await factsResponse.json();
            facts = factsData.facts || [];
        } catch (_) {
            // Facts are optional — don't block modal
        }

        const era = getEra(leader);
        const eraLabel = getEraLabel(era);

        const yearsText = leader.death_year
            ? `${leader.birth_year} – ${leader.death_year}`
            : `${leader.birth_year} – настоящее время`;

        const significance = leader.historical_significance || 5;
        const sigPercent = Math.round((significance / 10) * 100);

        modalBody.innerHTML = `
            <div class="modal-header">
                <div class="modal-header-top">
                    <div style="flex:1">
                        <h2 class="modal-title">${leader.name_ru}</h2>
                        <p class="modal-subtitle">${leader.name_en}</p>
                    </div>
                    <span class="modal-era-badge">${eraLabel}</span>
                </div>
                ${leader.short_description ? `<p class="modal-description">${leader.short_description}</p>` : ''}
                <div class="modal-significance">
                    <span class="modal-significance-label">Историческое значение</span>
                    <div class="sig-bar">
                        <div class="sig-bar-fill" style="width:${sigPercent}%"></div>
                    </div>
                    <span style="font-size:0.8rem;opacity:0.75">${significance}/10</span>
                </div>
            </div>
            <div class="modal-body">
                <!-- Biographical Data -->
                <div class="info-section">
                    <h3 class="section-title">
                        <span class="section-icon">🗓️</span>
                        Биографические данные
                    </h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Годы жизни</div>
                            <div class="info-value">${yearsText}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Место рождения</div>
                            <div class="info-value">${leader.birth_place || '—'}</div>
                        </div>
                        ${leader.death_place ? `
                        <div class="info-item">
                            <div class="info-label">Место смерти</div>
                            <div class="info-value">${leader.death_place}</div>
                        </div>
                        ` : ''}
                        ${leader.years_in_power ? `
                        <div class="info-item">
                            <div class="info-label">Годы у власти</div>
                            <div class="info-value">${leader.years_in_power.start} – ${leader.years_in_power.end || '1991'}</div>
                        </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Position -->
                <div class="info-section">
                    <h3 class="section-title">
                        <span class="section-icon">🎖️</span>
                        Должность
                    </h3>
                    <div class="biography-text">${leader.position}</div>
                </div>

                ${leader.biography ? `
                <!-- Biography -->
                <div class="info-section">
                    <h3 class="section-title">
                        <span class="section-icon">📜</span>
                        Биография
                    </h3>
                    <p class="biography-text">${leader.biography}</p>
                </div>
                ` : ''}

                <!-- Achievements -->
                <div class="info-section">
                    <h3 class="section-title">
                        <span class="section-icon">🏆</span>
                        Основные достижения
                    </h3>
                    <p class="biography-text">${leader.achievements}</p>
                </div>

                ${leader.legacy ? `
                <!-- Legacy -->
                <div class="info-section">
                    <h3 class="section-title">
                        <span class="section-icon">🌟</span>
                        Историческое наследие
                    </h3>
                    <p class="legacy-text">${leader.legacy}</p>
                </div>
                ` : ''}

                ${facts.length > 0 ? `
                <!-- Interesting Facts -->
                <div class="info-section">
                    <h3 class="section-title">
                        <span class="section-icon">💡</span>
                        Интересные факты
                    </h3>
                    <ul class="facts-list">
                        ${facts.map(fact => `<li>${fact}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}

                <!-- Video Section -->
                <div class="info-section">
                    <div class="video-section">
                        <p style="margin-bottom:16px;color:#555;font-size:0.95rem;">Смотрите архивные записи о деятельности этого лидера</p>
                        <button class="btn btn-primary btn-video" onclick="playVideo(${leader.video_id}, '${escapeAttr(leader.name_ru)}')">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="5 3 19 12 5 21 5 3"></polygon>
                            </svg>
                            Смотреть видео: ${leader.name_ru}
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Trigger significance bar animation
        requestAnimationFrame(() => {
            const fill = modalBody.querySelector('.sig-bar-fill');
            if (fill) fill.style.width = sigPercent + '%';
        });

    } catch (error) {
        console.error('Error loading leader details:', error);
        showToast('Ошибка загрузки данных о лидере', 'error');
        leaderModal.classList.remove('active');
    }
}

function buildModalSkeleton() {
    return `
        <div class="modal-header" style="min-height:180px;display:flex;align-items:center;justify-content:center">
            <div style="text-align:center;color:rgba(255,255,255,0.7)">
                <div class="spinner" style="margin:0 auto 16px;border-top-color:#ffd700"></div>
                <p style="font-size:0.95rem">Загрузка данных...</p>
            </div>
        </div>
    `;
}

// ===== PLAY VIDEO =====
function playVideo(videoId, leaderName) {
    const videoSource = leaderVideo.querySelector('source');
    videoSource.src = `/videos/${videoId}.mp4`;
    leaderVideo.load();

    if (videoTitle) videoTitle.textContent = leaderName;

    // Close leader modal if open
    leaderModal.classList.remove('active');

    // Open video modal
    videoModal.classList.add('active');

    leaderVideo.play().catch(() => {
        showToast(`Видео для «${leaderName}» пока недоступно`, 'warn');
        videoModal.classList.remove('active');
    });
}

// ===== SEARCH =====
async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        renderLeaders(allLeaders);
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

        if (!response.ok) throw new Error('Search failed');

        const data = await response.json();
        renderLeaders(data.results);

        if (data.results.length === 0) {
            noResults.style.display = 'block';
        }
    } catch (error) {
        console.error('Error searching:', error);
        showToast('Ошибка поиска', 'error');
    } finally {
        showLoading(false);
    }
}

function resetSearch() {
    searchInput.value = '';
    if (clearSearchBtn) clearSearchBtn.style.display = 'none';
    renderLeaders(allLeaders);
    noResults.style.display = 'none';
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Search
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') handleSearch();
    });
    searchInput.addEventListener('input', () => {
        if (clearSearchBtn) {
            clearSearchBtn.style.display = searchInput.value ? 'flex' : 'none';
        }
    });
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', resetSearch);
    }

    // Close modals
    closeModal.addEventListener('click', () => leaderModal.classList.remove('active'));
    closeVideoModal.addEventListener('click', closeVideo);
    leaderModal.addEventListener('click', e => {
        if (e.target === leaderModal) leaderModal.classList.remove('active');
    });
    videoModal.addEventListener('click', e => {
        if (e.target === videoModal) closeVideo();
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            leaderModal.classList.remove('active');
            closeVideo();
        }
    });

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderLeaders(currentSearchResults());
        });
    });

    // View toggle
    if (gridViewBtn) {
        gridViewBtn.addEventListener('click', () => {
            currentView = 'grid';
            gridViewBtn.classList.add('active');
            timelineViewBtn.classList.remove('active');
            renderLeaders(currentSearchResults());
        });
    }

    if (timelineViewBtn) {
        timelineViewBtn.addEventListener('click', () => {
            currentView = 'timeline';
            timelineViewBtn.classList.add('active');
            gridViewBtn.classList.remove('active');
            renderLeaders(currentSearchResults());
        });
    }
}

function closeVideo() {
    videoModal.classList.remove('active');
    leaderVideo.pause();
    leaderVideo.currentTime = 0;
}

/** Returns the currently relevant leaders array (filtered by search if active) */
function currentSearchResults() {
    return allLeaders; // for now just use all; search applies via handleSearch
}

// ===== TOAST NOTIFICATIONS =====
let toastTimer = null;

function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast toast-${type} visible`;

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove('visible');
    }, 3200);
}

// ===== UTILITY =====
function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text || '';
    return text.substring(0, maxLength).trimEnd() + '…';
}

function escapeAttr(str) {
    return String(str).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
    leadersGrid.style.display = show ? 'none' : (currentView === 'grid' ? 'grid' : 'none');
    if (!show && currentView === 'timeline') {
        timelineView.style.display = 'block';
    }
}

// ===== GLOBAL EXPOSURE =====
window.showLeaderDetails = showLeaderDetails;
window.playVideo         = playVideo;
window.resetSearch       = resetSearch;
