/**
 * TTS audio guide — speaks the open leader's biography aloud via
 * the browser SpeechSynthesis API. Prefers a Russian voice when one
 * is installed locally.
 */
(function () {
    const synth = window.speechSynthesis;
    if (!synth) return;

    let voicesCache = [];
    function loadVoices() {
        voicesCache = synth.getVoices();
    }
    loadVoices();
    if (typeof synth.addEventListener === 'function') {
        synth.addEventListener('voiceschanged', loadVoices);
    }

    function pickRussianVoice() {
        if (!voicesCache.length) loadVoices();
        return voicesCache.find(v => /ru[-_]/i.test(v.lang))
            || voicesCache.find(v => /russian/i.test(v.name))
            || null;
    }

    let activeUtterance = null;
    let activeButton = null;

    function setButtonState(button, state) {
        if (!button) return;
        button.classList.remove('btn-tts-idle', 'btn-tts-active');
        button.classList.add(state === 'speaking' ? 'btn-tts-active' : 'btn-tts-idle');
        const label = button.querySelector('.btn-tts-label');
        if (label) label.textContent = state === 'speaking' ? 'Остановить озвучку' : 'Озвучить биографию';
    }

    function stopSpeaking() {
        if (synth.speaking || synth.pending) synth.cancel();
        if (activeButton) setButtonState(activeButton, 'idle');
        activeUtterance = null;
        activeButton = null;
    }

    function speakBiography(button, text) {
        if (!text || !text.trim()) {
            window.showToast?.('Текст биографии пуст', 'warn');
            return;
        }
        if (activeButton === button && (synth.speaking || synth.pending)) {
            stopSpeaking();
            return;
        }
        stopSpeaking();

        const utt = new SpeechSynthesisUtterance(text);
        utt.lang = 'ru-RU';
        utt.rate = 0.95;
        utt.pitch = 1.0;
        const voice = pickRussianVoice();
        if (voice) utt.voice = voice;

        utt.onstart = () => setButtonState(button, 'speaking');
        utt.onend   = () => { if (activeUtterance === utt) { activeUtterance = null; setButtonState(button, 'idle'); } };
        utt.onerror = () => { setButtonState(button, 'idle'); window.showToast?.('Озвучка прервана', 'error'); };

        activeUtterance = utt;
        activeButton = button;
        setButtonState(button, 'speaking');
        synth.speak(utt);

        if (!voice) {
            window.showToast?.('Русский голос не найден — используется системный', 'warn');
        }
    }

    function buildTextFromModal(modalBody) {
        if (!modalBody) return '';
        const parts = [];
        const title = modalBody.querySelector('.modal-title');
        if (title) parts.push(title.textContent.trim());
        const desc = modalBody.querySelector('.modal-description');
        if (desc) parts.push(desc.textContent.trim());

        modalBody.querySelectorAll('.info-section').forEach(section => {
            const heading = section.querySelector('.section-title');
            const body = section.querySelector('.biography-text, .legacy-text');
            if (heading && body) {
                const hText = heading.textContent.trim();
                const bText = body.textContent.trim();
                if (bText) parts.push(hText + '. ' + bText);
            }
        });

        return parts.filter(Boolean).join('. ');
    }

    function attachButton(modalBody) {
        if (!modalBody) return;
        if (modalBody.querySelector('.btn-tts')) return;

        const headerTop = modalBody.querySelector('.modal-header-top');
        const header = modalBody.querySelector('.modal-header');
        const host = headerTop?.parentElement || header || modalBody;

        const wrapper = document.createElement('div');
        wrapper.className = 'modal-tts-wrap';
        const supportNote = pickRussianVoice() ? '' : '<small class="tts-hint">Русский голос не установлен в системе.</small>';
        wrapper.innerHTML = `
            <button type="button" class="btn btn-tts btn-tts-idle">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                </svg>
                <span class="btn-tts-label">Озвучить биографию</span>
            </button>
            ${supportNote}
        `;
        host.appendChild(wrapper);

        wrapper.querySelector('.btn-tts').addEventListener('click', evt => {
            const text = buildTextFromModal(modalBody);
            speakBiography(evt.currentTarget, text);
        });
    }

    // The leader modal is rebuilt each time it opens. Watch for content
    // changes inside it and attach the button after each render.
    const modalBody = document.getElementById('modalBody');
    if (modalBody) {
        const observer = new MutationObserver(() => {
            if (modalBody.querySelector('.modal-header-top')) {
                attachButton(modalBody);
            }
        });
        observer.observe(modalBody, { childList: true, subtree: false });
    }

    // Stop speaking if user closes the modal.
    const leaderModal = document.getElementById('leaderModal');
    if (leaderModal) {
        const closeObserver = new MutationObserver(() => {
            if (!leaderModal.classList.contains('active')) stopSpeaking();
        });
        closeObserver.observe(leaderModal, { attributes: true, attributeFilter: ['class'] });
    }

    // Stop speaking on navigation away.
    window.addEventListener('beforeunload', stopSpeaking);
})();
