/**
 * Quiz module — «Кто на портрете?»
 * Pulls a random question from /api/quiz, tracks score, streak, best in localStorage.
 */
(function () {
    const QUIZ_BEST_KEY = 'usssr.quiz.best';
    const QUIZ_LAST_LEADER_KEY = 'usssr.quiz.lastLeader';

    let session = { score: 0, streak: 0, best: 0 };
    let activeQuestion = null;
    let answered = false;

    const modal       = document.getElementById('quizModal');
    const closeBtn    = document.getElementById('closeQuizModal');
    const body        = document.getElementById('quizBody');
    const scoreEl     = document.getElementById('quizScore');
    const streakEl    = document.getElementById('quizStreak');
    const bestEl      = document.getElementById('quizBest');
    const launchBtn   = document.getElementById('openQuizBtn');

    if (!modal || !launchBtn) return;

    function loadBest() {
        const raw = parseInt(localStorage.getItem(QUIZ_BEST_KEY) || '0', 10);
        session.best = Number.isFinite(raw) ? raw : 0;
        renderScores();
    }

    function persistBest() {
        try { localStorage.setItem(QUIZ_BEST_KEY, String(session.best)); } catch (_) {}
    }

    function renderScores() {
        if (scoreEl)  scoreEl.textContent  = session.score;
        if (streakEl) streakEl.textContent = session.streak;
        if (bestEl)   bestEl.textContent   = session.best;
    }

    function openQuiz() {
        modal.classList.add('active');
        fetchQuestion();
    }

    function closeQuiz() {
        modal.classList.remove('active');
    }

    async function fetchQuestion() {
        body.innerHTML = '<div class="quiz-loading">Готовлю вопрос…</div>';
        answered = false;
        try {
            // Try multiple times to avoid repeating the same leader twice in a row.
            const lastId = parseInt(localStorage.getItem(QUIZ_LAST_LEADER_KEY) || '-1', 10);
            let data = null;
            for (let i = 0; i < 4; i++) {
                const resp = await fetch('/api/quiz', { cache: 'no-store' });
                if (!resp.ok) {
                    let payload = null;
                    try { payload = await resp.json(); } catch (_) { /* ignore */ }
                    throw new Error((payload && payload.error) || `Ошибка сервера (${resp.status})`);
                }
                data = await resp.json();
                if (!data.question || data.question.leader_id !== lastId) break;
            }
            activeQuestion = data;
            try { localStorage.setItem(QUIZ_LAST_LEADER_KEY, String(data.question.leader_id)); } catch (_) {}
            renderQuestion(data);
        } catch (err) {
            body.innerHTML = `
                <div class="quiz-error">
                    <p>Не удалось получить вопрос: ${escapeText(err.message || 'Неизвестная ошибка')}.</p>
                    <button class="btn btn-primary quiz-retry-btn" type="button">Повторить</button>
                </div>
            `;
            body.querySelector('.quiz-retry-btn')?.addEventListener('click', fetchQuestion);
        }
    }

    function renderQuestion(data) {
        const q = data.question;
        const lifespan = q.birth_year
            ? `${q.birth_year}${q.death_year ? ' – ' + q.death_year : ' – н.в.'}`
            : '';
        const initial = String(q.leader_id).charAt(0);
        const portraitMarkup = q.portrait_url
            ? `<img class="quiz-portrait" src="${escapeAttr(q.portrait_url)}" alt="Портрет личности" referrerpolicy="no-referrer" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'quiz-portrait quiz-portrait-placeholder',textContent:'?'}))">`
            : `<div class="quiz-portrait quiz-portrait-placeholder">?</div>`;

        body.innerHTML = `
            <div class="quiz-portrait-frame">
                ${portraitMarkup}
                <div class="quiz-portrait-hint">
                    ${lifespan ? `<span class="quiz-hint-pill">${escapeText(lifespan)}</span>` : ''}
                    ${q.category ? `<span class="quiz-hint-pill quiz-hint-category">${escapeText(categoryLabel(q.category))}</span>` : ''}
                </div>
            </div>
            <div class="quiz-options" id="quizOptions">
                ${data.options.map(opt => `
                    <button type="button" class="quiz-option" data-id="${opt.id}">
                        <span class="quiz-option-bullet">●</span>
                        <span class="quiz-option-name">${escapeText(opt.name_ru)}</span>
                    </button>
                `).join('')}
            </div>
            ${q.achievements_hint ? `<div class="quiz-achievements-hint">Подсказка: ${escapeText(q.achievements_hint)}</div>` : ''}
            <div class="quiz-feedback" id="quizFeedback"></div>
            <div class="quiz-actions" id="quizActions" style="display:none">
                <button type="button" class="btn btn-primary" id="quizNextBtn">Следующий вопрос →</button>
            </div>
        `;

        body.querySelectorAll('.quiz-option').forEach(btn => {
            btn.addEventListener('click', () => handleAnswer(parseInt(btn.dataset.id, 10), btn));
        });
    }

    function handleAnswer(chosenId, button) {
        if (answered || !activeQuestion) return;
        answered = true;

        const correctId = activeQuestion.answer_id;
        const optionEls = body.querySelectorAll('.quiz-option');
        optionEls.forEach(el => {
            const id = parseInt(el.dataset.id, 10);
            el.disabled = true;
            if (id === correctId) el.classList.add('quiz-option-correct');
            if (id === chosenId && id !== correctId) el.classList.add('quiz-option-wrong');
        });

        const feedback = document.getElementById('quizFeedback');
        const actions  = document.getElementById('quizActions');

        if (chosenId === correctId) {
            session.score  += 1;
            session.streak += 1;
            if (session.streak > session.best) {
                session.best = session.streak;
                persistBest();
            }
            feedback.innerHTML = `<span class="quiz-feedback-ok">Верно! Это <strong>${escapeText(correctName())}</strong>.</span>`;
        } else {
            session.streak = 0;
            feedback.innerHTML = `<span class="quiz-feedback-bad">Мимо. Правильный ответ — <strong>${escapeText(correctName())}</strong>.</span>`;
        }

        renderScores();
        actions.style.display = '';
        document.getElementById('quizNextBtn')?.addEventListener('click', fetchQuestion);
    }

    function correctName() {
        if (!activeQuestion) return '';
        const opt = activeQuestion.options.find(o => o.id === activeQuestion.answer_id);
        return opt ? opt.name_ru : '';
    }

    function categoryLabel(category) {
        const map = {
            politics: 'Политика', military: 'Армия', space: 'Космос',
            science:  'Наука',    culture:  'Культура', sports: 'Спорт',
            labor:    'Труд',
        };
        return map[category] || 'Эпоха';
    }

    function escapeText(str) {
        return String(str ?? '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function escapeAttr(str) {
        return String(str ?? '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    launchBtn.addEventListener('click', openQuiz);
    if (closeBtn) closeBtn.addEventListener('click', closeQuiz);
    modal.addEventListener('click', e => { if (e.target === modal) closeQuiz(); });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && modal.classList.contains('active')) closeQuiz();
    });

    loadBest();
})();
