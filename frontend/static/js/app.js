/**
 * USSR Leaders Platform - Main JavaScript
 */

// Global state
let allLeaders = [];

// DOM Elements
const leadersGrid = document.getElementById('leadersGrid');
const loading = document.getElementById('loading');
const noResults = document.getElementById('noResults');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const leaderModal = document.getElementById('leaderModal');
const videoModal = document.getElementById('videoModal');
const closeModal = document.getElementById('closeModal');
const closeVideoModal = document.getElementById('closeVideoModal');
const modalBody = document.getElementById('modalBody');
const leaderVideo = document.getElementById('leaderVideo');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadLeaders();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    closeModal.addEventListener('click', () => {
        leaderModal.classList.remove('active');
    });

    closeVideoModal.addEventListener('click', () => {
        videoModal.classList.remove('active');
        leaderVideo.pause();
    });

    // Close modals on background click
    leaderModal.addEventListener('click', (e) => {
        if (e.target === leaderModal) {
            leaderModal.classList.remove('active');
        }
    });

    videoModal.addEventListener('click', (e) => {
        if (e.target === videoModal) {
            videoModal.classList.remove('active');
            leaderVideo.pause();
        }
    });

    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            leaderModal.classList.remove('active');
            videoModal.classList.remove('active');
            leaderVideo.pause();
        }
    });
}

// Load all leaders
async function loadLeaders() {
    try {
        showLoading(true);
        const response = await fetch('/api/leaders');

        if (!response.ok) {
            throw new Error('Failed to fetch leaders');
        }

        allLeaders = await response.json();
        displayLeaders(allLeaders);
    } catch (error) {
        console.error('Error loading leaders:', error);
        showError('Ошибка загрузки данных. Пожалуйста, обновите страницу.');
    } finally {
        showLoading(false);
    }
}

// Display leaders in grid
function displayLeaders(leaders) {
    leadersGrid.innerHTML = '';

    if (leaders.length === 0) {
        noResults.style.display = 'block';
        return;
    }

    noResults.style.display = 'none';

    leaders.forEach(leader => {
        const card = createLeaderCard(leader);
        leadersGrid.appendChild(card);
    });
}

// Create leader card element
function createLeaderCard(leader) {
    const card = document.createElement('div');
    card.className = 'leader-card';

    const yearsText = leader.death_year
        ? `${leader.birth_year} - ${leader.death_year}`
        : `${leader.birth_year} - настоящее время`;

    card.innerHTML = `
        <div class="leader-card-header">
            <h2 class="leader-name">${leader.name_ru}</h2>
            <p class="leader-years">${yearsText}</p>
        </div>
        <div class="leader-card-body">
            <p class="leader-position">${leader.position}</p>
            <p class="leader-achievements">${truncateText(leader.achievements, 150)}</p>
        </div>
        <div class="leader-card-footer">
            <button class="btn btn-primary" onclick="showLeaderDetails(${leader.id})">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                    <path d="M2 17l10 5 10-5"></path>
                    <path d="M2 12l10 5 10-5"></path>
                </svg>
                Подробнее
            </button>
            <button class="btn btn-secondary" onclick="playVideo(${leader.video_id}, '${leader.name_ru}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                Видео
            </button>
        </div>
    `;

    return card;
}

// Show leader details modal
async function showLeaderDetails(leaderId) {
    try {
        const leader = allLeaders.find(l => l.id === leaderId);
        if (!leader) return;

        // Fetch AI-generated facts
        const factsResponse = await fetch(`/api/leaders/${leaderId}/facts`);
        const factsData = await factsResponse.json();
        const facts = factsData.facts || [];

        const yearsText = leader.death_year
            ? `${leader.birth_year} - ${leader.death_year}`
            : `${leader.birth_year} - настоящее время`;

        modalBody.innerHTML = `
            <div class="modal-header">
                <h2 class="modal-title">${leader.name_ru}</h2>
                <p class="modal-subtitle">${leader.name_en}</p>
                ${leader.short_description ? `<p class="modal-description">${leader.short_description}</p>` : ''}
            </div>
            <div class="modal-body">
                <div class="info-section">
                    <h3>Биографические данные</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Годы жизни</div>
                            <div class="info-value">${yearsText}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Место рождения</div>
                            <div class="info-value">${leader.birth_place}</div>
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
                            <div class="info-value">${leader.years_in_power.start} - ${leader.years_in_power.end}</div>
                        </div>
                        ` : ''}
                    </div>
                </div>

                <div class="info-section">
                    <h3>Должность</h3>
                    <p>${leader.position}</p>
                </div>

                ${leader.biography ? `
                <div class="info-section">
                    <h3>Биография</h3>
                    <p class="biography-text">${leader.biography}</p>
                </div>
                ` : ''}

                <div class="info-section">
                    <h3>Основные достижения</h3>
                    <p>${leader.achievements}</p>
                </div>

                ${leader.legacy ? `
                <div class="info-section">
                    <h3>Историческое наследие</h3>
                    <p class="legacy-text">${leader.legacy}</p>
                </div>
                ` : ''}

                ${facts.length > 0 ? `
                <div class="info-section">
                    <h3>Интересные факты</h3>
                    <ul class="facts-list">
                        ${facts.map(fact => `<li>${fact}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}

                <div class="info-section video-section">
                    <button class="btn btn-primary btn-video" onclick="playVideo(${leader.video_id}, '${leader.name_ru}')" style="width: 100%; justify-content: center;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                        </svg>
                        Смотреть видео: ${leader.name_ru} о себе
                    </button>
                </div>
            </div>
        `;

        leaderModal.classList.add('active');
    } catch (error) {
        console.error('Error loading leader details:', error);
        showError('Ошибка загрузки данных о лидере');
    }
}

// Play leader video
function playVideo(videoId, leaderName) {
    const videoSource = leaderVideo.querySelector('source');
    videoSource.src = `/videos/${videoId}.mp4`;
    leaderVideo.load();

    // Close leader modal if open
    leaderModal.classList.remove('active');

    // Open video modal
    videoModal.classList.add('active');

    // Play video
    leaderVideo.play().catch(error => {
        console.error('Error playing video:', error);
        showError(`Видео для ${leaderName} пока недоступно. Пожалуйста, убедитесь, что файл ${videoId}.mp4 находится в папке videos.`);
        videoModal.classList.remove('active');
    });
}

// Handle search
async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        displayLeaders(allLeaders);
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

        if (!response.ok) {
            throw new Error('Search failed');
        }

        const data = await response.json();
        displayLeaders(data.results);
    } catch (error) {
        console.error('Error searching:', error);
        showError('Ошибка поиска');
    } finally {
        showLoading(false);
    }
}

// Utility functions
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
    leadersGrid.style.display = show ? 'none' : 'grid';
}

function showError(message) {
    // Simple error display - can be enhanced with a toast notification
    alert(message);
}

// Make functions globally available
window.showLeaderDetails = showLeaderDetails;
window.playVideo = playVideo;
