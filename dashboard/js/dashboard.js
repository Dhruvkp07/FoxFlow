/**
 * FoxFlow — Dashboard Page Logic
 */

let hourlyChart = null;
let refreshInterval = null;

// ── Initialize ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const now = new Date();
    document.getElementById('date-display').textContent =
        now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    initHourlyChart();
    refreshDashboard();
    refreshInterval = setInterval(refreshDashboard, 5000);
});

// ── Start / Stop Tracking ──────────────────────────────────
async function startTracking() {
    try {
        await API.post('/api/tracking/start');
        document.getElementById('btn-start-tracking').style.display = 'none';
        document.getElementById('btn-stop-tracking').style.display = '';
        document.getElementById('tracking-status').innerHTML =
            '<span class="status-dot active"></span> Tracking active';
        showToast('All trackers started!', 'success');
    } catch (e) {
        showToast('Failed to start tracking', 'error');
    }
}

async function stopTracking() {
    try {
        await API.post('/api/tracking/stop');
        document.getElementById('btn-start-tracking').style.display = '';
        document.getElementById('btn-stop-tracking').style.display = 'none';
        document.getElementById('tracking-status').innerHTML =
            '<span class="status-dot inactive"></span> Tracking inactive';
        showToast('Tracking stopped', 'info');
    } catch (e) {
        showToast('Failed to stop tracking', 'error');
    }
}

// ── Refresh Dashboard ──────────────────────────────────────
async function refreshDashboard() {
    try {
        const [tracking, focus, report, goals, pomodoro] = await Promise.all([
            API.get('/api/tracking/status'),
            API.get('/api/tracking/focus'),
            API.get('/api/reports/daily'),
            API.get('/api/features/goals'),
            API.get('/api/features/pomodoro/status'),
        ]);

        updateTrackingButtons(tracking);
        updateStats(tracking, focus, report, pomodoro);
        updateGauge(focus.current || 0);
        updateEyeData(tracking.eye || {});
        updateHourlyChart(focus.hourly || []);
        updateTopApps(report.top_apps || []);
        updateTopSites(report.top_websites || []);
        updateStreaks(goals || []);
    } catch (e) {
        console.error('Dashboard refresh error:', e);
    }
}

function updateTrackingButtons(tracking) {
    const isRunning = tracking.eye?.running || tracking.app?.running;
    document.getElementById('btn-start-tracking').style.display = isRunning ? 'none' : '';
    document.getElementById('btn-stop-tracking').style.display = isRunning ? '' : 'none';
    document.getElementById('tracking-status').innerHTML = isRunning
        ? '<span class="status-dot active"></span> Tracking active'
        : '<span class="status-dot inactive"></span> Tracking inactive';
}

function updateStats(tracking, focus, report, pomodoro) {
    const focusMins = report.eye_tracking?.focus_minutes || 0;
    document.getElementById('stat-focus-time').textContent = formatMinutes(focusMins);
    document.getElementById('stat-focus-score').textContent = Math.round(focus.current || 0);
    document.getElementById('stat-keystrokes').textContent = formatNumber(
        tracking.input?.total_keys || report.input?.keystrokes || 0
    );
    document.getElementById('stat-pomodoros').textContent = pomodoro.completed_sessions || report.pomodoros_completed || 0;
}

function updateGauge(score) {
    const circumference = 2 * Math.PI * 90; // ~565
    const offset = circumference - (score / 100) * circumference;
    document.getElementById('gauge-fill').style.strokeDashoffset = offset;
    document.getElementById('gauge-value').textContent = Math.round(score);

    const badge = document.getElementById('focus-badge');
    if (score >= 75) { badge.textContent = 'EXCELLENT'; badge.className = 'badge badge-success'; }
    else if (score >= 50) { badge.textContent = 'GOOD'; badge.className = 'badge badge-warning'; }
    else if (score >= 25) { badge.textContent = 'NEEDS WORK'; badge.className = 'badge badge-info'; }
    else { badge.textContent = 'LOW'; badge.className = 'badge badge-danger'; }
}

function updateEyeData(eye) {
    document.getElementById('eye-focused').textContent = formatTime(eye.focus_seconds || 0);
    document.getElementById('eye-away').textContent = formatTime(eye.away_seconds || 0);
}

// ── Hourly Chart ───────────────────────────────────────────
function initHourlyChart() {
    const ctx = document.getElementById('hourly-chart').getContext('2d');
    hourlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
            datasets: [{
                label: 'Focus Score',
                data: new Array(24).fill(0),
                backgroundColor: 'rgba(255, 152, 0, 0.4)',
                borderColor: '#ff9800',
                borderWidth: 1,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { color: '#8a8a9f', font: { size: 11 } },
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8a8a9f', font: { size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 12 },
                },
            },
        },
    });
}

function updateHourlyChart(hourly) {
    if (!hourlyChart) return;
    const data = new Array(24).fill(0);
    hourly.forEach(h => {
        if (h.hour >= 0 && h.hour < 24) data[h.hour] = h.score;
    });
    hourlyChart.data.datasets[0].data = data;
    hourlyChart.update('none');
}

// ── Top Apps List ──────────────────────────────────────────
function updateTopApps(apps) {
    const container = document.getElementById('top-apps-list');
    if (!apps.length) {
        container.innerHTML = '<div class="empty-state"><div class="icon">💻</div><p>No app data yet</p></div>';
        return;
    }
    const maxTime = apps[0]?.minutes || 1;
    container.innerHTML = apps.slice(0, 6).map(app => `
        <div class="list-item">
            <div class="list-item-left">
                <div class="list-item-icon">💻</div>
                <div>
                    <div class="list-item-name">${escapeHtml(app.name)}</div>
                    <div class="progress-bar" style="width:120px;">
                        <div class="progress-fill" style="width:${(app.minutes / maxTime * 100)}%"></div>
                    </div>
                </div>
            </div>
            <div class="list-item-value">${formatMinutes(app.minutes)}</div>
        </div>
    `).join('');
}

// ── Top Websites ───────────────────────────────────────────
function updateTopSites(sites) {
    const container = document.getElementById('top-sites-list');
    if (!sites.length) {
        container.innerHTML = '<div class="empty-state"><div class="icon">🌐</div><p>No website data yet</p></div>';
        return;
    }
    const maxTime = sites[0]?.minutes || 1;
    container.innerHTML = sites.slice(0, 6).map(site => `
        <div class="list-item">
            <div class="list-item-left">
                <div class="list-item-icon">🌐</div>
                <div>
                    <div class="list-item-name">${escapeHtml(site.domain)}</div>
                    <div class="progress-bar" style="width:120px;">
                        <div class="progress-fill blue" style="width:${(site.minutes / maxTime * 100)}%"></div>
                    </div>
                </div>
            </div>
            <div class="list-item-value">${formatMinutes(site.minutes)}</div>
        </div>
    `).join('');
}

// ── Streaks ────────────────────────────────────────────────
function updateStreaks(goals) {
    const container = document.getElementById('streaks-list');
    const activeGoals = goals.filter(g => g.active && g.streak_count > 0);
    if (!activeGoals.length) {
        container.innerHTML = '<div class="empty-state"><div class="icon">🎯</div><p>No active streaks. <a href="/goals">Set up goals</a> to start tracking!</p></div>';
        return;
    }
    container.innerHTML = activeGoals.map(g => `
        <div class="list-item">
            <div class="list-item-left">
                <span class="streak-badge"><span class="fire">🔥</span> ${g.streak_count} day${g.streak_count !== 1 ? 's' : ''}</span>
                <div>
                    <div class="list-item-name">${escapeHtml(g.title)}</div>
                    <div class="list-item-meta">Best: ${g.longest_streak} days</div>
                </div>
            </div>
            <div class="list-item-value">${g.current_value}/${g.target_value} ${g.target_unit || ''}</div>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}
