/**
 * Connections graph — force-directed layout on a 2D canvas without
 * third-party dependencies. Renders /api/connections payload.
 */
(function () {
    const view      = document.getElementById('graphView');
    const canvas    = document.getElementById('graphCanvas');
    const legendEl  = document.getElementById('graphLegend');
    const tooltip   = document.getElementById('graphTooltip');
    if (!view || !canvas) return;

    const ctx = canvas.getContext('2d');
    const ratio = window.devicePixelRatio || 1;

    const CATEGORY_COLORS = {
        politics: '#c41e3a', military: '#ffd700', space: '#3a99ff',
        science:  '#7ddc3a', culture:  '#ff6ad5', sports: '#ff8c00',
        labor:    '#b88a00',
    };

    const LINK_STYLES = {
        successor: { color: '#c41e3a', dash: [],         label: 'преемник' },
        colleague: { color: '#5e8bd6', dash: [],         label: 'соратник' },
        mentor:    { color: '#ffd700', dash: [],         label: 'наставник' },
        student:   { color: '#ffaf3a', dash: [6, 4],     label: 'ученик' },
        team:      { color: '#7ddc3a', dash: [],         label: 'команда' },
        rival:     { color: '#ff5577', dash: [8, 4],     label: 'оппонент' },
        family:    { color: '#ff6ad5', dash: [],         label: 'семья' },
        commander: { color: '#a98d57', dash: [],         label: 'подчинение' },
    };

    let nodes = [];
    let edges = [];
    let nodeById = new Map();
    let linkTypes = {};
    let animationFrame = null;
    let dragging = null;
    let hover = null;
    let dataLoaded = false;
    let loadInflight = null;

    function resizeCanvas() {
        const wrap = canvas.parentElement;
        if (!wrap) return;
        const width  = Math.max(640, wrap.clientWidth);
        const height = 560;
        canvas.style.width  = width  + 'px';
        canvas.style.height = height + 'px';
        canvas.width  = Math.round(width  * ratio);
        canvas.height = Math.round(height * ratio);
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    async function loadData() {
        if (dataLoaded) return;
        if (loadInflight) return loadInflight;
        loadInflight = fetch('/api/connections')
            .then(resp => {
                if (!resp.ok) throw new Error(`Сервер вернул ${resp.status}`);
                return resp.json();
            })
            .then(payload => {
                const incomingNodes = Array.isArray(payload.nodes) ? payload.nodes : [];
                const incomingEdges = Array.isArray(payload.edges) ? payload.edges : [];
                linkTypes = payload.link_types || {};

                resizeCanvas();
                const w = canvas.clientWidth;
                const h = canvas.clientHeight;

                nodes = incomingNodes.map((n, i) => {
                    const angle = (i / incomingNodes.length) * Math.PI * 2;
                    return {
                        ...n,
                        x: w / 2 + Math.cos(angle) * Math.min(w, h) * 0.32,
                        y: h / 2 + Math.sin(angle) * Math.min(w, h) * 0.32,
                        vx: 0, vy: 0,
                    };
                });
                nodeById = new Map(nodes.map(n => [n.id, n]));
                edges = incomingEdges.filter(e => nodeById.has(e.source) && nodeById.has(e.target));

                renderLegend();
                dataLoaded = true;
                startSimulation();
            })
            .finally(() => { loadInflight = null; });
        return loadInflight;
    }

    function renderLegend() {
        if (!legendEl) return;
        const items = Object.keys(linkTypes).map(key => {
            const style = LINK_STYLES[key] || { color: '#888', dash: [], label: key };
            return `<span class="legend-item">
                <svg class="legend-swatch" width="34" height="10" aria-hidden="true">
                    <line x1="0" y1="5" x2="34" y2="5" stroke="${style.color}" stroke-width="3" ${style.dash.length ? `stroke-dasharray="${style.dash.join(' ')}"` : ''}/>
                </svg>
                <span class="legend-label">${escapeText(linkTypes[key])}</span>
            </span>`;
        }).join('');
        legendEl.innerHTML = items;
    }

    // Tiny Verlet-style simulation: repulsion + spring + centering.
    function simulationStep() {
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        const centerX = w / 2;
        const centerY = h / 2;
        const repulsion = 5600;
        const springLength = 140;
        const springK = 0.015;
        const damping = 0.85;
        const centerPull = 0.0035;

        // Pairwise repulsion
        for (let i = 0; i < nodes.length; i++) {
            const a = nodes[i];
            for (let j = i + 1; j < nodes.length; j++) {
                const b = nodes[j];
                const dx = a.x - b.x;
                const dy = a.y - b.y;
                const distSq = dx * dx + dy * dy + 0.01;
                const dist = Math.sqrt(distSq);
                const force = repulsion / distSq;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                a.vx += fx; a.vy += fy;
                b.vx -= fx; b.vy -= fy;
            }
        }

        // Spring along edges
        edges.forEach(e => {
            const a = nodeById.get(e.source);
            const b = nodeById.get(e.target);
            if (!a || !b) return;
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
            const displacement = dist - springLength;
            const fx = (dx / dist) * displacement * springK;
            const fy = (dy / dist) * displacement * springK;
            a.vx += fx; a.vy += fy;
            b.vx -= fx; b.vy -= fy;
        });

        // Gentle pull to center
        nodes.forEach(n => {
            n.vx += (centerX - n.x) * centerPull;
            n.vy += (centerY - n.y) * centerPull;
            n.vx *= damping;
            n.vy *= damping;
            if (n !== dragging) {
                n.x += n.vx;
                n.y += n.vy;
            }
            // Clamp inside canvas with padding
            const pad = 28;
            if (n.x < pad) { n.x = pad; n.vx = 0; }
            if (n.x > w - pad) { n.x = w - pad; n.vx = 0; }
            if (n.y < pad) { n.y = pad; n.vy = 0; }
            if (n.y > h - pad) { n.y = h - pad; n.vy = 0; }
        });
    }

    function draw() {
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        ctx.clearRect(0, 0, w, h);

        // Background grid (subtle)
        ctx.save();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
        ctx.lineWidth = 1;
        const grid = 40;
        for (let x = 0; x < w; x += grid) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        }
        for (let y = 0; y < h; y += grid) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }
        ctx.restore();

        // Edges
        edges.forEach(e => {
            const a = nodeById.get(e.source);
            const b = nodeById.get(e.target);
            if (!a || !b) return;
            const style = LINK_STYLES[e.type] || { color: '#888', dash: [] };
            ctx.save();
            ctx.lineWidth = 2;
            ctx.strokeStyle = style.color;
            if (style.dash.length) ctx.setLineDash(style.dash);
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
            ctx.restore();
        });

        // Nodes
        nodes.forEach(n => {
            const color = CATEGORY_COLORS[n.category] || '#999';
            const r = (hover && hover.id === n.id) ? 18 : 14;

            ctx.save();
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 3, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
            ctx.fill();

            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#0a0a18';
            ctx.stroke();

            ctx.font = '11px "Tahoma", "MS Sans Serif", sans-serif';
            ctx.fillStyle = '#fff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            const label = shortLabel(n.name_ru);
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.9)';
            ctx.lineWidth = 3;
            ctx.strokeText(label, n.x, n.y + r + 4);
            ctx.fillText(label, n.x, n.y + r + 4);
            ctx.restore();
        });
    }

    function shortLabel(name) {
        if (!name) return '';
        const parts = name.split(' ');
        if (parts.length >= 3) return parts[parts.length - 1] + ' ' + parts[0][0] + '.';
        return name;
    }

    function startSimulation() {
        let frames = 0;
        function loop() {
            simulationStep();
            draw();
            frames += 1;
            // Run continuously while view is active; stop after 600 frames
            // to avoid burning CPU once layout stabilises.
            if (frames < 600 && view.style.display !== 'none') {
                animationFrame = requestAnimationFrame(loop);
            } else {
                animationFrame = null;
            }
        }
        if (animationFrame) cancelAnimationFrame(animationFrame);
        animationFrame = requestAnimationFrame(loop);
    }

    function nodeAt(x, y) {
        for (let i = nodes.length - 1; i >= 0; i--) {
            const n = nodes[i];
            const dx = n.x - x;
            const dy = n.y - y;
            if (dx * dx + dy * dy <= 20 * 20) return n;
        }
        return null;
    }

    function eventToCanvas(evt) {
        const rect = canvas.getBoundingClientRect();
        return { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
    }

    canvas.addEventListener('pointerdown', evt => {
        const { x, y } = eventToCanvas(evt);
        const n = nodeAt(x, y);
        if (n) {
            dragging = n;
            canvas.setPointerCapture(evt.pointerId);
        }
    });

    canvas.addEventListener('pointermove', evt => {
        const { x, y } = eventToCanvas(evt);
        if (dragging) {
            dragging.x = x;
            dragging.y = y;
            dragging.vx = 0;
            dragging.vy = 0;
            if (!animationFrame) startSimulation();
        } else {
            const n = nodeAt(x, y);
            hover = n;
            canvas.style.cursor = n ? 'pointer' : 'grab';
            if (tooltip) {
                if (n) {
                    const incident = edges.filter(e => e.source === n.id || e.target === n.id).length;
                    tooltip.innerHTML = `<strong>${escapeText(n.name_ru)}</strong><br>${escapeText(categoryLabel(n.category))} • связей: ${incident}`;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (x + 16) + 'px';
                    tooltip.style.top  = (y + 16) + 'px';
                } else {
                    tooltip.style.display = 'none';
                }
            }
        }
    });

    canvas.addEventListener('pointerup', evt => {
        if (dragging) {
            try { canvas.releasePointerCapture(evt.pointerId); } catch (_) {}
            dragging = null;
        }
    });

    canvas.addEventListener('click', evt => {
        const { x, y } = eventToCanvas(evt);
        const n = nodeAt(x, y);
        if (n && typeof window.showLeaderDetails === 'function') {
            window.showLeaderDetails(n.id);
        }
    });

    canvas.addEventListener('pointerleave', () => {
        hover = null;
        if (tooltip) tooltip.style.display = 'none';
    });

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

    window.addEventListener('resize', () => {
        if (view.style.display === 'none') return;
        resizeCanvas();
        startSimulation();
    });

    window.showGraphView = async function showGraphView() {
        try {
            await loadData();
            resizeCanvas();
            startSimulation();
        } catch (err) {
            ctx.save();
            ctx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
            ctx.fillStyle = '#fff';
            ctx.font = '14px "Tahoma", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Не удалось загрузить граф: ' + (err.message || 'ошибка'),
                         canvas.clientWidth / 2, canvas.clientHeight / 2);
            ctx.restore();
        }
    };
})();
