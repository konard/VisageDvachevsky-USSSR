/**
 * Граф связей — force-directed layout на 2D canvas без сторонних
 * зависимостей. Оформление выполнено в советской парадной эстетике:
 * кремовая «бумага», красно-золотая палитра, портреты-медальоны в
 * двойной обводке, направленные стрелки на эстафете «преемник/ученик»,
 * лёгкий эффект «затемнения соседей» при наведении.
 *
 * Источник данных: /api/connections.
 */
(function () {
    const view      = document.getElementById('graphView');
    const canvas    = document.getElementById('graphCanvas');
    const legendEl  = document.getElementById('graphLegend');
    const tooltip   = document.getElementById('graphTooltip');
    if (!view || !canvas) return;

    const ctx = canvas.getContext('2d');
    const ratio = window.devicePixelRatio || 1;

    // Палитра — выдержана в духе советского плаката: красный кумач,
    // золото, типографская бумага, индиго, бронза, оливковый.
    const PAPER         = '#f5ead0';
    const PAPER_DEEP    = '#e8d9a8';
    const INK           = '#221a10';
    const INK_SOFT      = '#5b3a14';
    const GOLD          = '#caa12c';
    const GOLD_DEEP     = '#8b6b14';
    const RED           = '#bf1322';
    const RED_DEEP      = '#7a0d18';

    // Цвет «медальона» по сфере деятельности.
    const CATEGORY_COLORS = {
        politics: '#bf1322', // кумач
        military: '#8b6b14', // тёмное золото
        space:    '#1d3a8a', // индиго
        science:  '#3d7666', // приглушённый малахит
        culture:  '#9a2c40', // винный
        sports:   '#c25b2a', // охра
        labor:    '#6e4f1a', // бронза
    };

    // Стиль связи: цвет, пунктир, стрелка (true → отношение направленное),
    // подпись в легенде. Жирные сплошные линии для родственных уз,
    // пунктир — для оппозиций, стрелки — для эстафеты и наставничества.
    const LINK_STYLES = {
        successor: { color: '#bf1322', dash: [],          arrow: true,  label: 'преемник' },
        colleague: { color: '#1d3a8a', dash: [],          arrow: false, label: 'соратник' },
        mentor:    { color: '#8b6b14', dash: [],          arrow: true,  label: 'наставник' },
        student:   { color: '#caa12c', dash: [7, 5],      arrow: true,  label: 'ученик' },
        team:      { color: '#3d7666', dash: [],          arrow: false, label: 'команда' },
        rival:     { color: '#7a0d18', dash: [3, 5],      arrow: false, label: 'оппонент' },
        family:    { color: '#9a2c40', dash: [],          arrow: false, label: 'семья' },
        commander: { color: '#5b3a14', dash: [10, 4, 2, 4], arrow: true, label: 'подчинение' },
    };

    let nodes = [];
    let edges = [];
    let nodeById = new Map();
    let adjacency = new Map();    // id -> Set(id) соседей для подсветки
    let linkTypes = {};
    let animationFrame = null;
    let dragging = null;
    let hover = null;
    let dataLoaded = false;
    let loadInflight = null;
    let portraitCache = new Map(); // id -> HTMLImageElement | 'loading'
    let lastDrawTime = 0;
    let burstAngle = 0;            // плавно вращающийся «сноп» лучей фона

    function resizeCanvas() {
        const wrap = canvas.parentElement;
        if (!wrap) return;
        const width  = Math.max(640, wrap.clientWidth);
        const height = 600;
        canvas.style.width  = width  + 'px';
        canvas.style.height = height + 'px';
        canvas.width  = Math.round(width  * ratio);
        canvas.height = Math.round(height * ratio);
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    function preloadPortrait(node) {
        if (!node.portrait_url) return;
        if (portraitCache.has(node.id)) return;
        const img = new Image();
        img.decoding = 'async';
        img.onload  = () => { portraitCache.set(node.id, img); };
        img.onerror = () => { portraitCache.set(node.id, null); };
        portraitCache.set(node.id, 'loading');
        img.src = node.portrait_url;
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

                // Карта соседства — нужна, чтобы при наведении показывать
                // только связанные рёбра в полную силу, остальные приглушать.
                adjacency = new Map(nodes.map(n => [n.id, new Set()]));
                edges.forEach(e => {
                    adjacency.get(e.source).add(e.target);
                    adjacency.get(e.target).add(e.source);
                });

                nodes.forEach(preloadPortrait);

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
            const style = LINK_STYLES[key] || { color: '#888', dash: [], label: key, arrow: false };
            const dashAttr = style.dash.length ? `stroke-dasharray="${style.dash.join(' ')}"` : '';
            const arrowMark = style.arrow ? `
                <polygon points="36,1 44,5 36,9" fill="${style.color}" />
            ` : '';
            return `<span class="legend-item">
                <svg class="legend-swatch" width="48" height="10" aria-hidden="true">
                    <line x1="2" y1="5" x2="${style.arrow ? 36 : 46}" y2="5"
                          stroke="${style.color}" stroke-width="3" ${dashAttr}
                          stroke-linecap="round"/>
                    ${arrowMark}
                </svg>
                <span class="legend-label">${escapeText(linkTypes[key])}</span>
            </span>`;
        }).join('');
        legendEl.innerHTML = items;
    }

    // Verlet-style симуляция: расталкивание + пружины + центрирование.
    function simulationStep() {
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        const centerX = w / 2;
        const centerY = h / 2;
        const repulsion = 7200;
        const springLength = 150;
        const springK = 0.018;
        const damping = 0.86;
        const centerPull = 0.0032;

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

        nodes.forEach(n => {
            n.vx += (centerX - n.x) * centerPull;
            n.vy += (centerY - n.y) * centerPull;
            n.vx *= damping;
            n.vy *= damping;
            if (n !== dragging) {
                n.x += n.vx;
                n.y += n.vy;
            }
            const pad = 36;
            if (n.x < pad) { n.x = pad; n.vx = 0; }
            if (n.x > w - pad) { n.x = w - pad; n.vx = 0; }
            if (n.y < pad) { n.y = pad; n.vy = 0; }
            if (n.y > h - pad) { n.y = h - pad; n.vy = 0; }
        });
    }

    // -------------------- Отрисовка фона --------------------
    function drawBackground(w, h) {
        // Бумажный фон.
        const paperGrad = ctx.createLinearGradient(0, 0, 0, h);
        paperGrad.addColorStop(0, '#f8efd2');
        paperGrad.addColorStop(1, '#ead8a4');
        ctx.fillStyle = paperGrad;
        ctx.fillRect(0, 0, w, h);

        // Конический «сноп» лучей в центре — конструктивистский акцент.
        const cx = w / 2;
        const cy = h / 2;
        const rayCount = 24;
        const maxR = Math.hypot(w, h) * 0.62;
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(burstAngle);
        for (let i = 0; i < rayCount; i++) {
            const a0 = (i / rayCount) * Math.PI * 2;
            const a1 = a0 + (Math.PI * 2) / rayCount;
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.arc(0, 0, maxR, a0, a1);
            ctx.closePath();
            ctx.fillStyle = i % 2 === 0
                ? 'rgba(191, 19, 34, 0.05)'
                : 'rgba(202, 161, 44, 0.05)';
            ctx.fill();
        }
        ctx.restore();

        // Радиальное золотое сияние в центре.
        const glow = ctx.createRadialGradient(cx, cy, 30, cx, cy, Math.min(w, h) * 0.6);
        glow.addColorStop(0, 'rgba(202, 161, 44, 0.25)');
        glow.addColorStop(0.7, 'rgba(245, 234, 208, 0)');
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, w, h);

        // Мелкая «бумажная» сетка — еле заметная клетка как у архивной
        // папки, помогает «зацепить» взгляд на больших пустотах.
        ctx.save();
        ctx.strokeStyle = 'rgba(122, 13, 24, 0.06)';
        ctx.lineWidth = 1;
        const grid = 48;
        for (let x = grid; x < w; x += grid) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        }
        for (let y = grid; y < h; y += grid) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }
        ctx.restore();

        // Угловые «уголки папки» — четыре золотые скобки.
        drawCornerBracket(20, 20, 0);
        drawCornerBracket(w - 20, 20, Math.PI / 2);
        drawCornerBracket(w - 20, h - 20, Math.PI);
        drawCornerBracket(20, h - 20, -Math.PI / 2);
    }

    function drawCornerBracket(x, y, rot) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(rot);
        ctx.strokeStyle = GOLD_DEEP;
        ctx.lineWidth = 3;
        ctx.lineCap = 'square';
        ctx.beginPath();
        ctx.moveTo(0, 28); ctx.lineTo(0, 0); ctx.lineTo(28, 0);
        ctx.stroke();
        // тонкий внутренний штрих
        ctx.strokeStyle = RED_DEEP;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(5, 24); ctx.lineTo(5, 5); ctx.lineTo(24, 5);
        ctx.stroke();
        ctx.restore();
    }

    // -------------------- Отрисовка рёбер --------------------
    function drawEdges() {
        edges.forEach(e => {
            const a = nodeById.get(e.source);
            const b = nodeById.get(e.target);
            if (!a || !b) return;
            const style = LINK_STYLES[e.type] || { color: INK_SOFT, dash: [], arrow: false };

            const incident = hover &&
                (e.source === hover.id || e.target === hover.id);
            const dim = hover && !incident;

            ctx.save();
            ctx.globalAlpha = dim ? 0.18 : 1;

            // Подложка-«дублирующая» полоса под линией — даёт ощущение
            // напечатанного на бумаге следа.
            ctx.lineWidth = incident ? 5.5 : 4;
            ctx.strokeStyle = 'rgba(34, 26, 16, 0.18)';
            ctx.lineCap = 'round';
            ctx.beginPath();
            ctx.moveTo(a.x + 1, a.y + 1.5);
            ctx.lineTo(b.x + 1, b.y + 1.5);
            ctx.stroke();

            // Основная линия.
            ctx.lineWidth = incident ? 3.2 : 2.2;
            ctx.strokeStyle = style.color;
            if (style.dash.length) ctx.setLineDash(style.dash);
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();

            // Стрелка для направленных отношений.
            if (style.arrow) {
                drawArrow(a, b, style.color, incident ? 12 : 9);
            }
            ctx.restore();
        });
    }

    function drawArrow(from, to, color, size) {
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const len = Math.sqrt(dx * dx + dy * dy) || 1;
        // Отступ, чтобы стрелка не «вонзалась» в портрет узла.
        const inset = 26;
        const tx = to.x - (dx / len) * inset;
        const ty = to.y - (dy / len) * inset;
        const angle = Math.atan2(dy, dx);
        ctx.save();
        ctx.translate(tx, ty);
        ctx.rotate(angle);
        ctx.setLineDash([]);
        ctx.fillStyle = color;
        ctx.strokeStyle = INK;
        ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(-size, -size * 0.55);
        ctx.lineTo(-size * 0.6, 0);
        ctx.lineTo(-size, size * 0.55);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        ctx.restore();
    }

    // -------------------- Отрисовка узлов --------------------
    function drawNodes() {
        nodes.forEach(n => {
            const isHover = hover && hover.id === n.id;
            const isNeighbour = hover && adjacency.has(hover.id) &&
                adjacency.get(hover.id).has(n.id);
            const dim = hover && !isHover && !isNeighbour;

            const color = CATEGORY_COLORS[n.category] || INK_SOFT;
            const baseR = 22;
            const r = isHover ? baseR + 4 : baseR;

            ctx.save();
            ctx.globalAlpha = dim ? 0.32 : 1;

            // «Печать»-тень.
            ctx.beginPath();
            ctx.arc(n.x + 2.5, n.y + 3, r + 3, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(34, 26, 16, 0.35)';
            ctx.fill();

            // Внешнее золотое кольцо.
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 4, 0, Math.PI * 2);
            ctx.fillStyle = GOLD;
            ctx.fill();
            ctx.lineWidth = 1.4;
            ctx.strokeStyle = GOLD_DEEP;
            ctx.stroke();

            // Внутреннее цветное кольцо по категории.
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 1.5, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();

            // Маска под портрет.
            ctx.save();
            ctx.beginPath();
            ctx.arc(n.x, n.y, r - 1, 0, Math.PI * 2);
            ctx.closePath();
            ctx.clip();

            const portrait = portraitCache.get(n.id);
            if (portrait && portrait !== 'loading' && portrait.naturalWidth) {
                // Лёгкая «архивная» обработка: чуть сепия + контраст.
                ctx.filter = 'sepia(0.28) contrast(1.05) saturate(0.92) brightness(0.97)';
                const side = (r - 1) * 2;
                ctx.drawImage(portrait, n.x - r + 1, n.y - r + 1, side, side);
                ctx.filter = 'none';
            } else {
                // Запасной вариант: цветной диск с инициалом.
                ctx.fillStyle = color;
                ctx.fillRect(n.x - r, n.y - r, r * 2, r * 2);
                ctx.fillStyle = '#f5ead0';
                ctx.font = '700 18px "Russo One", "Oswald", sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(initialsOf(n.name_ru), n.x, n.y + 1);
            }
            ctx.restore();

            // Перекрывающее «звезда»-кольцо: красная окантовка с риской.
            ctx.lineWidth = isHover ? 2.6 : 1.8;
            ctx.strokeStyle = isHover ? RED : RED_DEEP;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r - 0.5, 0, Math.PI * 2);
            ctx.stroke();

            // Маленькая красная звезда на 12 часов — единый «штамп архива».
            drawTinyStar(n.x, n.y - r - 3, 4.5, isHover ? RED : RED_DEEP);

            // Подпись под медальоном.
            const label = shortLabel(n.name_ru);
            ctx.font = isHover
                ? '700 12.5px "PT Serif", Georgia, serif'
                : '600 11.5px "PT Serif", Georgia, serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            // Кремовый «гало» под текстом для читаемости.
            ctx.lineWidth = 4;
            ctx.strokeStyle = 'rgba(245, 234, 208, 0.95)';
            ctx.strokeText(label, n.x, n.y + r + 8);
            ctx.fillStyle = INK;
            ctx.fillText(label, n.x, n.y + r + 8);
            ctx.restore();
        });
    }

    function drawTinyStar(cx, cy, r, color) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(-Math.PI / 2);
        ctx.beginPath();
        for (let i = 0; i < 10; i++) {
            const angle = (i * Math.PI) / 5;
            const radius = i % 2 === 0 ? r : r * 0.45;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#1a1006';
        ctx.lineWidth = 0.6;
        ctx.stroke();
        ctx.restore();
    }

    function initialsOf(name) {
        const parts = String(name || '').trim().split(/\s+/);
        if (parts.length >= 2) {
            return (parts[0][0] || '') + (parts[parts.length - 1][0] || '');
        }
        return (parts[0] || '?').slice(0, 2);
    }

    function shortLabel(name) {
        if (!name) return '';
        const parts = name.split(' ');
        if (parts.length >= 3) return parts[parts.length - 1] + ' ' + parts[0][0] + '.';
        return name;
    }

    function draw() {
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        ctx.clearRect(0, 0, w, h);
        drawBackground(w, h);
        drawEdges();
        drawNodes();
    }

    function startSimulation() {
        let frames = 0;
        function loop(ts) {
            if (lastDrawTime) {
                const dt = ts - lastDrawTime;
                // Сноп лучей вращается ОЧЕНЬ медленно, чтобы создать жизнь
                // без отвлечения внимания.
                burstAngle += dt * 0.00002;
            }
            lastDrawTime = ts;
            simulationStep();
            draw();
            frames += 1;
            // Продолжаем плавную «дышащую» отрисовку (лучи + хвостик
            // симуляции). Через 900 кадров переходим в режим «по запросу»:
            // обновляем только при наведении/перетаскивании.
            if ((frames < 900 || hover || dragging) && view.style.display !== 'none') {
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
            if (dx * dx + dy * dy <= 26 * 26) return n;
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
            const changed = (n && (!hover || hover.id !== n.id)) ||
                            (!n && hover);
            hover = n;
            canvas.style.cursor = n ? 'pointer' : 'grab';
            if (tooltip) {
                if (n) {
                    const incident = edges.filter(e => e.source === n.id || e.target === n.id).length;
                    tooltip.innerHTML = `
                        <span class="graph-tooltip-stamp">★</span>
                        <strong class="graph-tooltip-name">${escapeText(n.name_ru)}</strong>
                        <span class="graph-tooltip-row">
                            <em>сфера:</em> ${escapeText(categoryLabel(n.category))}
                        </span>
                        <span class="graph-tooltip-row">
                            <em>связей:</em> ${incident}
                        </span>
                        <span class="graph-tooltip-foot">клик — карточка</span>
                    `;
                    tooltip.style.display = 'block';
                    // Прижимаем тултип к канвасу, чтобы не вылезал за края.
                    const w = canvas.clientWidth;
                    const tooltipW = 220;
                    const leftRaw = x + 18;
                    const left = leftRaw + tooltipW > w ? x - tooltipW - 18 : leftRaw;
                    tooltip.style.left = Math.max(8, left) + 'px';
                    tooltip.style.top  = Math.max(8, y - 16) + 'px';
                } else {
                    tooltip.style.display = 'none';
                }
            }
            if (changed && !animationFrame) startSimulation();
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
            ctx.fillStyle = INK;
            ctx.font = '14px "PT Serif", Georgia, serif';
            ctx.textAlign = 'center';
            ctx.fillText('Не удалось загрузить граф: ' + (err.message || 'ошибка'),
                         canvas.clientWidth / 2, canvas.clientHeight / 2);
            ctx.restore();
        }
    };
})();
