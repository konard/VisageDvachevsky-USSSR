/**
 * СССР - Лица Эпохи
 * Main JavaScript — Enhanced Edition
 */

// ===== STATE =====
let allLeaders = [];
let currentView = 'grid';   // 'grid' | 'timeline'
let currentFilter = 'all';  // 'all' | 'early' | 'mid' | 'late'
const VIDEO_PLACEHOLDER_TEXT = 'Архивный ролик готовится';

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
const chatModal        = document.getElementById('chatModal');
const closeModal       = document.getElementById('closeModal');
const closeVideoModal  = document.getElementById('closeVideoModal');
const closeChatModal   = document.getElementById('closeChatModal');
const modalBody        = document.getElementById('modalBody');
const leaderVideo      = document.getElementById('leaderVideo');
const videoTitle       = document.getElementById('videoTitle');
const toast            = document.getElementById('toast');
const gridViewBtn      = document.getElementById('gridViewBtn');
const timelineViewBtn  = document.getElementById('timelineViewBtn');
const leaderCountEl    = document.getElementById('leaderCount');

// Chat refs
const chatLog          = document.getElementById('chatLog');
const chatInput        = document.getElementById('chatInput');
const chatForm         = document.getElementById('chatForm');
const chatSendBtn      = document.getElementById('chatSendBtn');
const chatStatusEl     = document.getElementById('chatStatus');
const chatModelLabel   = document.getElementById('chatModelLabel');
const chatLeaderName   = document.getElementById('chatLeaderName');
const chatLeaderRole   = document.getElementById('chatLeaderRole');
const chatLeaderPortraitFrame = document.getElementById('chatLeaderPortraitFrame');
const chatWarning      = document.getElementById('chatWarning');

// Chat state
const chatHistoryByLeader = new Map(); // leaderId -> [{role, content}]
let currentChatLeader = null;
let chatHealthState = { available: null, model: null };
let chatRequestInflight = false;

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

        const payload = await response.json();
        allLeaders = normalizeLeadersResponse(payload);

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
    const portrait = leader.portrait_url || '';
    const fallbackInitial = escapeHtml(leader.name_ru.charAt(0));

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
            <div class="leader-portrait-frame">
                ${portrait
                    ? `<img class="leader-portrait" src="${escapeAttr(portrait)}" alt="${escapeAttr(leader.name_ru)}" loading="lazy" referrerpolicy="no-referrer" onerror="handlePortraitError(this, '${fallbackInitial}')">`
                    : `<div class="leader-portrait leader-portrait-placeholder">${fallbackInitial}</div>`}
            </div>
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
            ${leader.short_description ? `<p class="leader-summary">${leader.short_description}</p>` : ''}
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
                Хроника
            </button>
            <button class="btn btn-chat" onclick="openChat(${leader.id})" title="Поговорить с этой фигурой через локальную LLM">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                Диалог
            </button>
        </div>
        <div class="leader-video-strip">
            <span class="video-strip-label">Видеоархив</span>
            <span class="video-strip-value">${VIDEO_PLACEHOLDER_TEXT}</span>
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
            facts = normalizeFactsResponse(factsData);
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
                    ${leader.portrait_url ? `<img class="modal-portrait" src="${escapeAttr(leader.portrait_url)}" alt="${escapeAttr(leader.name_ru)}" loading="lazy" referrerpolicy="no-referrer" onerror="handlePortraitError(this, '${escapeHtml(leader.name_ru.charAt(0))}')">` : ''}
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
                            Смотреть плейсхолдер: ${leader.name_ru}
                        </button>
                    </div>
                </div>

                <!-- Dialogue Section -->
                <div class="info-section">
                    <h3 class="section-title">
                        <span class="section-icon">💬</span>
                        Диалог с фигурой (Ollama)
                    </h3>
                    <p style="margin:0 0 14px;color:#444;font-size:0.95rem;">
                        Локальная нейросеть отыгрывает роль ${escapeHtml(leader.name_ru)}. Беседа строго о его эпохе, биографии и деятельности.
                    </p>
                    <button class="btn btn-chat btn-video" onclick="openChat(${leader.id})">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        Открыть диалог
                    </button>
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
        showToast(`Видеоархив для «${leaderName}» пока не загружен`, 'warn');
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
        let response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

        if (!response.ok && response.status === 404) {
            response = await fetch(`/api/leaders/search?q=${encodeURIComponent(query)}`);
        }

        if (!response.ok) throw new Error('Search failed');

        const data = await response.json();
        const results = normalizeSearchResponse(data);
        renderLeaders(results);

        if (results.length === 0) {
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

// ===== CHAT WITH LEADER (Ollama) =====
async function openChat(leaderId) {
    const leader = allLeaders.find(l => l.id === leaderId);
    if (!leader) {
        showToast('Лидер не найден', 'error');
        return;
    }

    currentChatLeader = leader;

    // Close other modals
    leaderModal.classList.remove('active');
    videoModal.classList.remove('active');

    // Populate header
    chatLeaderName.textContent = leader.name_ru;
    chatLeaderRole.textContent = leader.position || '';
    renderChatPortrait(leader);

    // Render history (or greeting)
    renderChatHistory(leaderId, leader);

    // Show modal
    chatModal.classList.add('active');
    chatInput.value = '';
    chatInput.focus();

    // Probe Ollama health
    await refreshChatHealth();
}

function renderChatHistory(leaderId, leader) {
    const history = chatHistoryByLeader.get(leaderId) || [];
    chatLog.innerHTML = '';

    if (history.length === 0) {
        appendChatBubble({
            role: 'system',
            content: `Беседа с фигурой «${leader.name_ru}». Задавайте вопросы только о его эпохе, биографии и деятельности.`,
        });
    } else {
        history.forEach(msg => appendChatBubble(msg));
    }
    scrollChatToBottom();
}

function appendChatBubble({ role, content, error = false }) {
    const wrap = document.createElement('div');
    let cls = 'chat-msg';
    if (role === 'user') cls += ' chat-msg-user';
    else if (role === 'assistant') cls += ' chat-msg-assistant';
    else if (role === 'system') cls += ' chat-msg-system';
    if (error) cls += ' chat-msg-error';
    wrap.className = cls;

    const roleLabel = document.createElement('div');
    roleLabel.className = 'chat-msg-role';
    if (role === 'user') roleLabel.textContent = 'Вы';
    else if (role === 'assistant') roleLabel.textContent = currentChatLeader ? currentChatLeader.name_ru : 'Лидер';
    else roleLabel.textContent = 'Система';

    const body = document.createElement('div');
    body.className = 'chat-msg-body';
    body.textContent = content;

    wrap.appendChild(roleLabel);
    wrap.appendChild(body);
    chatLog.appendChild(wrap);
    return wrap;
}

function appendTypingIndicator() {
    const wrap = document.createElement('div');
    wrap.className = 'chat-msg chat-msg-assistant';
    wrap.id = 'chatTypingIndicator';
    wrap.innerHTML = `
        <div class="chat-msg-role">${currentChatLeader ? escapeHtml(currentChatLeader.name_ru) : 'Лидер'} печатает…</div>
        <div class="chat-typing"><span></span><span></span><span></span></div>
    `;
    chatLog.appendChild(wrap);
    scrollChatToBottom();
    return wrap;
}

function removeTypingIndicator() {
    const el = document.getElementById('chatTypingIndicator');
    if (el) el.remove();
}

function scrollChatToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

async function sendChatMessage(event) {
    if (event) event.preventDefault();
    if (!currentChatLeader) return;
    if (chatRequestInflight) return;

    const message = chatInput.value.trim();
    if (!message) return;

    const leaderId = currentChatLeader.id;
    const history = chatHistoryByLeader.get(leaderId) || [];

    // Optimistically render the user message
    appendChatBubble({ role: 'user', content: message });
    chatInput.value = '';
    chatInput.style.height = '';
    scrollChatToBottom();

    chatRequestInflight = true;
    chatSendBtn.disabled = true;
    chatInput.disabled = true;
    appendTypingIndicator();

    try {
        const resp = await fetch(`/api/leaders/${leaderId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                history,
            }),
        });

        removeTypingIndicator();

        if (!resp.ok) {
            let payload = null;
            try { payload = await resp.json(); } catch (_) { /* ignore */ }
            const msg = (payload && payload.error)
                ? payload.error
                : `Ошибка сервера (${resp.status})`;

            appendChatBubble({
                role: 'assistant',
                content: msg,
                error: true,
            });

            if (resp.status === 503) {
                setChatStatus('offline', payload?.error || 'Ollama недоступен');
            }
            return;
        }

        const data = await resp.json();
        if (Array.isArray(data.history)) {
            chatHistoryByLeader.set(leaderId, data.history);
        } else {
            const updated = history.concat([
                { role: 'user', content: message },
                { role: 'assistant', content: data.reply || '' },
            ]);
            chatHistoryByLeader.set(leaderId, updated);
        }

        appendChatBubble({
            role: 'assistant',
            content: data.reply || '(пустой ответ)',
        });

        if (data.off_topic) {
            showChatWarning('Запрос вне темы — фигура отвечает только о своей эпохе.');
        } else {
            hideChatWarning();
        }

        if (data.model) {
            chatHealthState.model = data.model;
            updateChatModelLabel();
        }
        setChatStatus('online');
    } catch (err) {
        removeTypingIndicator();
        appendChatBubble({
            role: 'assistant',
            content: 'Не удалось связаться с сервером. Проверьте подключение и Ollama.',
            error: true,
        });
        setChatStatus('offline', 'Ошибка сети');
    } finally {
        scrollChatToBottom();
        chatRequestInflight = false;
        chatSendBtn.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

async function refreshChatHealth() {
    setChatStatus('checking');
    try {
        const resp = await fetch('/api/chat/health');
        const data = await resp.json();
        chatHealthState = {
            available: !!data.available,
            model: data.model || null,
            model_present: !!data.model_present,
            models: data.models || [],
        };
        updateChatModelLabel();

        if (!data.available) {
            setChatStatus('offline', data.error || 'Ollama не отвечает');
            showChatWarning(
                'Локальная модель Ollama недоступна. Установите Ollama и запустите её: '
                + '<code>ollama serve</code>, затем <code>ollama pull '
                + escapeHtml(data.model || 'llama3.1:8b') + '</code>.'
            );
        } else if (data.model && data.model_present === false) {
            setChatStatus('offline', `модель ${data.model} не загружена`);
            showChatWarning(
                `Модель <code>${escapeHtml(data.model)}</code> не найдена. Выполните: `
                + `<code>ollama pull ${escapeHtml(data.model)}</code>.`
            );
        } else {
            setChatStatus('online');
            hideChatWarning();
        }
    } catch (err) {
        chatHealthState = { available: false, model: null };
        setChatStatus('offline', 'health endpoint недоступен');
        showChatWarning('Сервер недоступен. Запустите backend и Ollama.');
    }
}

function setChatStatus(state, detail = '') {
    chatStatusEl.classList.remove('online', 'offline', 'checking');
    chatStatusEl.classList.add(state);
    let label = state;
    if (state === 'online') label = 'онлайн';
    else if (state === 'offline') label = 'офлайн';
    else if (state === 'checking') label = 'проверка…';
    chatStatusEl.textContent = detail ? `${label} — ${detail}` : label;
}

function updateChatModelLabel() {
    if (chatHealthState.model) {
        chatModelLabel.textContent = `модель: ${chatHealthState.model}`;
    } else {
        chatModelLabel.textContent = '';
    }
}

function showChatWarning(html) {
    chatWarning.innerHTML = html;
    chatWarning.style.display = '';
}

function hideChatWarning() {
    chatWarning.style.display = 'none';
    chatWarning.innerHTML = '';
}

function closeChat() {
    chatModal.classList.remove('active');
    removeTypingIndicator();
}

function renderChatPortrait(leader) {
    if (!chatLeaderPortraitFrame) return;
    chatLeaderPortraitFrame.innerHTML = '';
    const initial = (leader.name_ru || '?').charAt(0);

    if (leader.portrait_url) {
        const img = document.createElement('img');
        img.className = 'chat-header-portrait';
        img.src = leader.portrait_url;
        img.alt = leader.name_ru;
        img.referrerPolicy = 'no-referrer';
        img.loading = 'lazy';
        img.onerror = () => replaceChatPortraitWithPlaceholder(initial);
        chatLeaderPortraitFrame.appendChild(img);
    } else {
        replaceChatPortraitWithPlaceholder(initial);
    }
}

function replaceChatPortraitWithPlaceholder(initial) {
    if (!chatLeaderPortraitFrame) return;
    chatLeaderPortraitFrame.innerHTML = '';
    const ph = document.createElement('div');
    ph.className = 'chat-header-portrait chat-header-portrait-placeholder';
    ph.textContent = initial;
    chatLeaderPortraitFrame.appendChild(ph);
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
    if (closeChatModal) closeChatModal.addEventListener('click', closeChat);
    leaderModal.addEventListener('click', e => {
        if (e.target === leaderModal) leaderModal.classList.remove('active');
    });
    videoModal.addEventListener('click', e => {
        if (e.target === videoModal) closeVideo();
    });
    if (chatModal) {
        chatModal.addEventListener('click', e => {
            if (e.target === chatModal) closeChat();
        });
    }
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            leaderModal.classList.remove('active');
            closeVideo();
            closeChat();
        }
    });

    // Chat form
    if (chatForm) {
        chatForm.addEventListener('submit', sendChatMessage);
    }
    if (chatInput) {
        chatInput.addEventListener('keydown', e => {
            // Cmd/Ctrl+Enter or plain Enter (without Shift) sends
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

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

function normalizeLeadersResponse(payload) {
    if (Array.isArray(payload)) {
        return payload;
    }

    if (Array.isArray(payload?.data)) {
        return payload.data;
    }

    return [];
}

function normalizeFactsResponse(payload) {
    if (Array.isArray(payload?.facts)) {
        return payload.facts;
    }

    if (Array.isArray(payload?.data?.facts)) {
        return payload.data.facts;
    }

    return [];
}

function normalizeSearchResponse(payload) {
    if (Array.isArray(payload?.results)) {
        return payload.results;
    }

    if (Array.isArray(payload?.data)) {
        return payload.data;
    }

    return [];
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

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function handlePortraitError(img, fallbackText) {
    const fallback = document.createElement('div');
    fallback.className = img.classList.contains('modal-portrait')
        ? 'modal-portrait modal-portrait-placeholder'
        : 'leader-portrait leader-portrait-placeholder';
    fallback.textContent = fallbackText;
    img.replaceWith(fallback);
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
window.handlePortraitError = handlePortraitError;
window.openChat          = openChat;
