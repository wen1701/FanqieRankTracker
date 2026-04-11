document.addEventListener('DOMContentLoaded', () => {
    const categoryList = document.getElementById('category-list');
    const waterfall = document.getElementById('books-waterfall');
    const updateDate = document.getElementById('update-date');
    const categoryTitle = document.getElementById('current-category-title');
    const trendStats = document.getElementById('trend-stats');
    const aiContent = document.getElementById('ai-content');
    const trendPanel = document.getElementById('trend-panel');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');

    let allData = null;
    let typingTimer = null;

    // ========== Copy Toast ==========
    const copyToast = document.createElement('div');
    copyToast.className = 'copy-toast';
    copyToast.textContent = '✅ 书本信息已复制';
    document.body.appendChild(copyToast);
    let toastTimer = null;

    function showCopyToast() {
        if (toastTimer) clearTimeout(toastTimer);
        copyToast.classList.add('show');
        toastTimer = setTimeout(() => copyToast.classList.remove('show'), 1800);
    }

    function copyBookInfo(e, book) {
        e.preventDefault();
        e.stopPropagation();
        const text = `${book.title}\n作者：${book.author}\n阅读量：${book.reads}\n链接：${book.url || '无'}`;
        navigator.clipboard.writeText(text).then(() => {
            const btn = e.currentTarget;
            btn.classList.add('copied');
            btn.textContent = '✅ 已复制';
            showCopyToast();
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.textContent = '📋 复制信息';
            }, 1500);
        }).catch(() => {
            // Fallback for older browsers
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            showCopyToast();
        });
    }

    // ========== Mobile menu ==========
    let overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
    });

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
    });

    // ========== Load Data ==========
    fetch('data/latest_ranks.json')
        .then(r => {
            if (!r.ok) throw new Error('Network error');
            return r.json();
        })
        .then(data => {
            allData = data;
            const prevInfo = data.prev_date ? ` (对比 ${data.prev_date})` : '';
            updateDate.textContent = `${data.date}${prevInfo}`;
            renderCategories();
            if (data.categories.length > 0) {
                selectCategory(data.categories[0].name);
            }
        })
        .catch(err => {
            console.error(err);
            waterfall.innerHTML = '<p style="color:#f87171;padding:20px;">数据加载失败，请刷新重试。</p>';
        });

    // ========== Render sidebar categories ==========
    function renderCategories() {
        categoryList.innerHTML = '';
        allData.categories.forEach((cat, i) => {
            const li = document.createElement('li');
            li.dataset.category = cat.name;

            const nameSpan = document.createElement('span');
            nameSpan.textContent = cat.name;
            li.appendChild(nameSpan);

            // New entry badge
            const trend = cat.trend || {};
            if (trend.new_count > 0) {
                const badge = document.createElement('span');
                badge.className = 'cat-badge new';
                badge.textContent = `+${trend.new_count}`;
                li.appendChild(badge);
            }

            if (i === 0) li.classList.add('active');

            li.addEventListener('click', () => {
                document.querySelectorAll('#category-list li').forEach(el => el.classList.remove('active'));
                li.classList.add('active');
                selectCategory(cat.name);
                // Close mobile sidebar
                sidebar.classList.remove('open');
                overlay.classList.remove('show');
            });

            categoryList.appendChild(li);
        });
    }

    // ========== Select a category ==========
    function selectCategory(categoryName) {
        categoryTitle.textContent = categoryName;
        const cat = allData.categories.find(c => c.name === categoryName);
        if (!cat) return;
        renderTrend(cat);
        renderBooks(cat);
    }

    // ========== Build a url->rank lookup for previous day ==========
    function buildPrevRankMap(categoryName) {
        // We infer prev rank from trend data
        // Actually, the trend data already has this info baked in.
        // For the card badges we need to know if a book is new or changed rank.
        const cat = allData.categories.find(c => c.name === categoryName);
        if (!cat || !cat.trend) return {};

        const map = {};
        // Mark new books
        (cat.trend.new_books || []).forEach(title => {
            map[title] = 'new';
        });
        // Risers
        (cat.trend.top_risers || []).forEach(r => {
            map[r.title] = r.change;
        });
        // Fallers
        (cat.trend.top_fallers || []).forEach(f => {
            map[f.title] = f.change;
        });
        return map;
    }

    // ========== Render Trend Panel ==========
    function renderTrend(cat) {
        const trend = cat.trend || {};
        trendStats.innerHTML = '';

        // Stat chips
        const chips = [];

        if (trend.new_count > 0) {
            chips.push({ icon: '🆕', text: `${trend.new_count} 本新上榜`, cls: 'new-entry' });
        }
        if (trend.dropped_count > 0) {
            chips.push({ icon: '📉', text: `${trend.dropped_count} 本掉出`, cls: 'down' });
        }
        if (trend.top_risers && trend.top_risers.length > 0) {
            trend.top_risers.forEach(r => {
                chips.push({ icon: '📈', text: `${r.title} ${r.change}`, cls: 'up' });
            });
        }
        if (trend.reads_growth && trend.reads_growth.length > 0) {
            chips.push({ icon: '🔥', text: `${trend.reads_growth[0].title} ${trend.reads_growth[0].growth}`, cls: 'up' });
        }

        if (chips.length === 0) {
            chips.push({ icon: '📊', text: '榜单无明显变动', cls: '' });
        }

        chips.forEach(chip => {
            const el = document.createElement('span');
            el.className = `stat-chip ${chip.cls}`;
            el.textContent = `${chip.icon} ${chip.text}`;
            trendStats.appendChild(el);
        });

        // AI Summary with typewriter effect
        const summary = trend.summary || '';
        typewriterEffect(summary);
    }

    // ========== Simple Markdown renderer ==========
    function renderMarkdown(text) {
        let html = escapeHtml(text);
        // Headers: ### h3, ## h2 (rare in summaries but support it)
        html = html.replace(/^### (.+)$/gm, '<strong style="font-size:0.95rem">$1</strong>');
        html = html.replace(/^## (.+)$/gm, '<strong style="font-size:1rem">$1</strong>');
        // Bold: **text**
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic: *text*
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        // Book titles: 《》 highlight
        html = html.replace(/《(.+?)》/g, '<span style="color:var(--accent);font-weight:500">《$1》</span>');
        // Unordered lists: - item or * item
        html = html.replace(/^[-*] (.+)$/gm, '<span style="display:block;padding-left:1em;text-indent:-0.6em">• $1</span>');
        // Numbered lists: 1. item
        html = html.replace(/^(\d+)\. (.+)$/gm, '<span style="display:block;padding-left:1em;text-indent:-0.6em">$1. $2</span>');
        return html;
    }

    // ========== Typewriter effect ==========
    function typewriterEffect(text) {
        // Cancel any previous animation
        if (typingTimer) {
            clearTimeout(typingTimer);
            typingTimer = null;
        }

        aiContent.innerHTML = '';

        if (!text) {
            aiContent.innerHTML = '<span class="ai-loading">暂无分析数据</span>';
            return;
        }

        let index = 0;
        const speed = 25; // ms per char

        function type() {
            if (index < text.length) {
                // During typing, show escaped plain text with cursor
                const displayed = text.substring(0, index + 1);
                aiContent.innerHTML = escapeHtml(displayed) + '<span class="cursor"></span>';
                index++;
                typingTimer = setTimeout(type, speed);
            } else {
                // Done typing — render full markdown
                aiContent.innerHTML = renderMarkdown(text);
            }
        }

        type();
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
    }

    // ========== Render Books (Waterfall) ==========
    function renderBooks(cat) {
        waterfall.innerHTML = '';
        const books = cat.books || [];

        if (books.length === 0) {
            waterfall.innerHTML = '<p style="color:var(--text-muted);padding:20px;">该分类暂无书籍。</p>';
            return;
        }

        const changeMap = buildPrevRankMap(cat.name);
        const fragment = document.createDocumentFragment();

        books.forEach((book, index) => {
            const rank = index + 1;
            const card = document.createElement('a');
            card.href = book.url && book.url !== '#' ? book.url : 'javascript:void(0)';
            if (book.url && book.url !== '#') card.target = '_blank';
            card.rel = 'noopener';
            card.className = 'book-card';

            // Rank badge class
            let rankCls = '';
            if (rank === 1) rankCls = 'rank-1';
            else if (rank === 2) rankCls = 'rank-2';
            else if (rank === 3) rankCls = 'rank-3';

            // Change indicator
            let changeHtml = '';
            const change = changeMap[book.title];
            if (change === 'new') {
                changeHtml = '<span class="book-change new">NEW</span>';
            } else if (change && change.startsWith('+')) {
                changeHtml = `<span class="book-change up">↑${change}</span>`;
            } else if (change && change.startsWith('-')) {
                changeHtml = `<span class="book-change down">↓${change.replace('-', '')}</span>`;
            }

            // Cover
            const coverHtml = book.cover
                ? `<div class="book-cover"><img src="${book.cover}" alt="${escapeAttr(book.title)}" loading="lazy"></div>`
                : `<div class="book-cover"><div class="no-cover">暂无封面</div></div>`;

            card.innerHTML = `
                <span class="book-rank ${rankCls}">${rank}</span>
                ${changeHtml}
                ${coverHtml}
                <div class="book-info">
                    <h3 class="book-title" title="${escapeAttr(book.title)}">${escapeHtml(book.title)}</h3>
                    <div class="book-meta">
                        <span class="book-author">✍️ ${escapeHtml(book.author)}</span>
                        <span class="book-reads">🔥 ${escapeHtml(book.reads)}</span>
                    </div>
                    <p class="book-intro">${escapeHtml(book.intro)}</p>
                    <button class="book-copy-btn" type="button">📋 复制信息</button>
                </div>
            `;

            // Bind copy button
            const copyBtn = card.querySelector('.book-copy-btn');
            copyBtn.addEventListener('click', (e) => copyBookInfo(e, book));

            fragment.appendChild(card);
        });

        waterfall.appendChild(fragment);
    }

    function escapeAttr(str) {
        return (str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
});
