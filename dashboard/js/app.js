/**
 * FoxFlow — Core App Module
 * Navigation, utilities, and shared functionality.
 */

const API = {
    get: async (url) => {
        const res = await fetch(url);
        return res.json();
    },
    post: async (url, data = {}) => {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },
    put: async (url, data = {}) => {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },
    delete: async (url) => {
        const res = await fetch(url, { method: 'DELETE' });
        return res.json();
    },
};

// ── Navigation ─────────────────────────────────────────────
function initNavigation() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// ── Toast Notifications ────────────────────────────────────
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ── Utilities ──────────────────────────────────────────────
function formatTime(seconds) {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    const h = Math.floor(seconds / 3600);
    const m = Math.round((seconds % 3600) / 60);
    return `${h}h ${m}m`;
}

function formatMinutes(minutes) {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const h = Math.floor(minutes / 60);
    const m = Math.round(minutes % 60);
    return `${h}h ${m}m`;
}

function formatPercent(value) {
    return `${Math.round(value)}%`;
}

function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

// ── Sidebar template ───────────────────────────────────────
function getSidebarHTML() {
    return `
    <div class="sidebar-brand">
        <div class="brand-icon">🦊</div>
        <div>
            <div class="brand-name">FoxFlow</div>
            <div class="brand-tag">Productivity Intelligence</div>
        </div>
    </div>
    <nav class="sidebar-nav">
        <div class="nav-section">Overview</div>
        <a href="/" class="nav-link" id="nav-dashboard">
            <span class="icon">📊</span> Dashboard
        </a>
        <a href="/reports" class="nav-link" id="nav-reports">
            <span class="icon">📈</span> Reports
        </a>
        <a href="/ai-insights" class="nav-link" id="nav-ai">
            <span class="icon">🤖</span> AI Insights
        </a>

        <div class="nav-section">Tools</div>
        <a href="/pomodoro" class="nav-link" id="nav-pomodoro">
            <span class="icon">🍅</span> Pomodoro
        </a>
        <a href="/goals" class="nav-link" id="nav-goals">
            <span class="icon">🎯</span> Goals & Streaks
        </a>
        <a href="/blocker" class="nav-link" id="nav-blocker">
            <span class="icon">🚫</span> Site Blocker
        </a>

        <div class="nav-section">System</div>
        <a href="/settings" class="nav-link" id="nav-settings">
            <span class="icon">⚙️</span> Settings
        </a>
    </nav>`;
}

// ── Initialize ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.innerHTML = getSidebarHTML();
    }
    initNavigation();
});
