/**
 * Events chronology module — loads /api/timeline and renders cards
 * grouped by year. Clicking a leader chip opens the leader modal.
 */
(function () {
    const view    = document.getElementById('eventsView');
    const listEl  = document.getElementById('eventsList');
    if (!view || !listEl) return;

    const CATEGORY_LABELS = {
        politics: 'Политика', military: 'Армия', space: 'Космос',
        science:  'Наука',    culture:  'Культура', sports: 'Спорт',
        labor:    'Труд',
    };
    const MONTH_NAMES = ['', 'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                          'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'];

    let eventsCache = null;
    let loadInflight = null;

    async function ensureEvents() {
        if (eventsCache) return eventsCache;
        if (loadInflight) return loadInflight;
        loadInflight = fetch('/api/timeline')
            .then(resp => {
                if (!resp.ok) throw new Error(`Сервер вернул ${resp.status}`);
                return resp.json();
            })
            .then(data => {
                eventsCache = Array.isArray(data.events) ? data.events : [];
                return eventsCache;
            })
            .finally(() => { loadInflight = null; });
        return loadInflight;
    }

    function findLeader(id) {
        const all = Array.isArray(window.allLeaders) ? window.allLeaders : [];
        return all.find(l => l.id === id);
    }

    function renderEventList(events) {
        if (!events.length) {
            listEl.innerHTML = '<div class="events-empty">Хроника пока пуста.</div>';
            return;
        }

        // Group by year
        const byYear = new Map();
        events.forEach(ev => {
            if (!byYear.has(ev.year)) byYear.set(ev.year, []);
            byYear.get(ev.year).push(ev);
        });

        const html = Array.from(byYear.entries()).map(([year, items]) => `
            <section class="events-year-section">
                <h3 class="events-year-heading">${year}</h3>
                <div class="events-year-list">
                    ${items.map(renderEventCard).join('')}
                </div>
            </section>
        `).join('');

        listEl.innerHTML = html;

        listEl.querySelectorAll('[data-leader-id]').forEach(chip => {
            chip.addEventListener('click', () => {
                const id = parseInt(chip.dataset.leaderId, 10);
                if (typeof window.showLeaderDetails === 'function') {
                    window.showLeaderDetails(id);
                }
            });
        });
    }

    function renderEventCard(ev) {
        const monthLabel = ev.month && MONTH_NAMES[ev.month] ? MONTH_NAMES[ev.month] : '';
        const cat = ev.category || 'politics';
        const catLabel = CATEGORY_LABELS[cat] || 'Эпоха';
        const chips = Array.isArray(ev.leader_ids) ? ev.leader_ids.map(id => {
            const leader = findLeader(id);
            if (!leader) return '';
            return `<button type="button" class="event-leader-chip" data-leader-id="${id}" title="Открыть карточку ${escapeAttr(leader.name_ru)}">
                ${leader.portrait_url ? `<img class="event-leader-chip-img" src="${escapeAttr(leader.portrait_url)}" referrerpolicy="no-referrer" alt="">` : ''}
                <span>${escapeText(leader.name_ru)}</span>
            </button>`;
        }).join('') : '';

        return `
            <article class="event-card event-card-${cat}">
                <header class="event-card-head">
                    <span class="event-card-date">${monthLabel ? monthLabel + ' ' : ''}${ev.year}</span>
                    <span class="event-card-category category-${cat}">${escapeText(catLabel)}</span>
                </header>
                <h4 class="event-card-title">${escapeText(ev.title)}</h4>
                <p class="event-card-desc">${escapeText(ev.description)}</p>
                ${chips ? `<div class="event-card-chips">${chips}</div>` : ''}
            </article>
        `;
    }

    function escapeText(str) {
        return String(str ?? '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    function escapeAttr(str) {
        return String(str ?? '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    window.showEventsView = async function showEventsView() {
        try {
            const events = await ensureEvents();
            renderEventList(events);
        } catch (err) {
            listEl.innerHTML = `<div class="events-empty">Не удалось загрузить хронику: ${escapeText(err.message || 'ошибка')}.</div>`;
        }
    };
})();
