// RCD² Dashboard JavaScript

const API_BASE = '';  // Same origin
let driftChart = null;
let accuracyChart = null;
let apiKey = localStorage.getItem('rcd2_api_key');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 RCD² Dashboard Loading...');

    if (!apiKey) {
        requestApiKey();
    } else {
        initDashboard();
    }
});

function requestApiKey() {
    const key = prompt("🔐 Security Check: Please enter your RCD² API Key (default: dev-key-123):", "dev-key-123");
    if (key) {
        apiKey = key;
        localStorage.setItem('rcd2_api_key', key);
        initDashboard();
    } else {
        showError("API Key is required to access the dashboard.");
    }
}

function initDashboard() {
    initCharts();
    refreshMetrics();

    // Auto-refresh every 30 seconds
    setInterval(refreshMetrics, 30000);
}

// Helper for authenticated fetch
async function authFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
        ...options.headers
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('rcd2_api_key');
        showError("Authentication failed. Please reload and enter a valid API Key.");
        throw new Error("Unauthorized");
    }

    return response;
}

// Initialize charts
function initCharts() {
    const chartConfig = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#94a3b8'
                }
            }
        },
        scales: {
            y: {
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
            },
            x: {
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
            }
        }
    };

    // Drift chart
    const driftCtx = document.getElementById('driftChart').getContext('2d');
    driftChart = new Chart(driftCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Drift Score',
                data: [],
                borderColor: '#f5576c',
                backgroundColor: 'rgba(245, 87, 108, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: chartConfig
    });

    // Accuracy chart
    const accCtx = document.getElementById('accuracyChart').getContext('2d');
    accuracyChart = new Chart(accCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Model Accuracy',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...chartConfig,
            scales: {
                ...chartConfig.scales,
                y: {
                    ...chartConfig.scales.y,
                    min: 0,
                    max: 1
                }
            }
        }
    });
}

// Refresh all metrics
async function refreshMetrics() {
    try {
        await Promise.all([
            updateMetrics(),
            updateDriftStatus(),
            updateCharts(),
            updateEvents()
        ]);

        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
    } catch (error) {
        console.error('Error refreshing metrics:', error);
        showError('Failed to refresh metrics');
    }
}

// Update main metrics
async function updateMetrics() {
    try {
        const response = await fetch(`${API_BASE} /api/metrics`);
        const data = await response.json();

        // Champion model
        if (data.champion_model) {
            document.getElementById('championVersion').textContent = data.champion_model.version;
            document.getElementById('championAccuracy').textContent =
                (data.champion_model.accuracy * 100).toFixed(2) + '%';
            document.getElementById('championSamples').textContent =
                data.champion_model.training_samples.toLocaleString();
        }

        // Total models
        document.getElementById('totalModels').textContent = data.total_models || 0;

        // Retraining stats
        const stats = data.retraining_stats;
        document.getElementById('totalRetrains').textContent = stats.total_retrains || 0;
        document.getElementById('promotedCount').textContent = stats.successful_promotes || 0;
        document.getElementById('promotionRate').textContent =
            ((stats.promotion_rate || 0) * 100).toFixed(0) + '%';

    } catch (error) {
        console.error('Update metrics error:', error);
    }
}

// Update drift status
async function updateDriftStatus() {
    try {
        const response = await fetch(`${API_BASE} /api/drift`);
        const data = await response.json();

        const driftScore = data.drift_score || 0;
        const severity = data.severity || 'none';
        const driftType = data.drift_type || 'none';

        document.getElementById('driftScore').textContent = driftScore.toFixed(1);

        const severityBadge = document.getElementById('driftSeverity');
        severityBadge.textContent = severity;
        severityBadge.className = `severity - badge ${severity} `;

        document.getElementById('driftType').textContent = driftType.replace('_', ' ');

        // Update system status
        const statusIndicator = document.getElementById('systemStatus');
        const statusText = document.getElementById('statusText');

        if (severity === 'high') {
            statusIndicator.className = 'status error';
            statusText.textContent = 'DRIFT DETECTED';
        } else if (severity === 'moderate') {
            statusIndicator.className = 'status warning';
            statusText.textContent = 'MONITORING';
        } else {
            statusIndicator.className = 'status healthy';
            statusText.textContent = 'OPERATIONAL';
        }

    } catch (error) {
        console.error('Update drift status error:', error);
    }
}

// Update charts
async function updateCharts() {
    try {
        // Update drift timeline
        const driftResponse = await fetch(`${API_BASE} /api/metrics / drift_timeline ? limit = 20`);
        const driftData = await driftResponse.json();

        if (driftData.timeline && driftData.timeline.length > 0) {
            const labels = driftData.timeline.map(d => {
                const date = new Date(d.timestamp);
                return date.toLocaleTimeString();
            });
            const scores = driftData.timeline.map(d => d.drift_score);

            driftChart.data.labels = labels;
            driftChart.data.datasets[0].data = scores;
            driftChart.update('none');
        }

        // Update model timeline
        const modelResponse = await fetch(`${API_BASE} /api/metrics / model_timeline`);
        const modelData = await modelResponse.json();

        if (modelData.timeline && modelData.timeline.length > 0) {
            const labels = modelData.timeline.map(m => m.version);
            const accuracies = modelData.timeline.map(m => m.accuracy);

            accuracyChart.data.labels = labels;
            accuracyChart.data.datasets[0].data = accuracies;
            accuracyChart.update('none');
        }

    } catch (error) {
        console.error('Update charts error:', error);
    }
}

// Update events list
async function updateEvents() {
    try {
        const response = await fetch(`${API_BASE} /api/retrain / history ? limit = 5`);
        const data = await response.json();

        const eventsList = document.getElementById('eventsList');

        if (data.history && data.history.length > 0) {
            eventsList.innerHTML = data.history.map(event => `
    < div class="event-item" >
                    <span class="event-time">${new Date(event.timestamp).toLocaleString()}</span>
                    <span class="event-description">
                        <strong>${event.reason}</strong> - 
                        ${event.promoted ? '✅ Promoted' : '⚠️ Not promoted'} 
                        (${event.new_version})
                        - Improvement: ${(event.improvement * 100).toFixed(2)}%
                    </span>
                </div >
    `).join('');
        } else {
            eventsList.innerHTML = '<div class="event-item"><span>No recent events</span></div>';
        }

    } catch (error) {
        console.error('Update events error:', error);
    }
}

// Test prediction
async function testPrediction() {
    try {
        const features = [
            (Math.random() * 2 - 1).toFixed(3),
            (Math.random() * 2 - 1).toFixed(3),
            (Math.random() * 2 - 1).toFixed(3)
        ].map(Number);

        const response = await fetch(`${API_BASE} /api/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ features })
        });

        const data = await response.json();

        showModal(`
    < h2 > Prediction Result</h2 >
            <p><strong>Features:</strong> [${features.join(', ')}]</p>
            <p><strong>Prediction:</strong> ${data.prediction}</p>
            <p><strong>Probability:</strong> ${data.probability.map(p => (p * 100).toFixed(1) + '%').join(', ')}</p>
            <p><strong>Model Version:</strong> ${data.model_version}</p>
`);

    } catch (error) {
        showError('Prediction failed: ' + error.message);
    }
}

// Ingest sample data
async function ingestSampleData() {
    try {
        const features = [
            (Math.random() * 2 - 1),
            (Math.random() * 2 - 1),
            (Math.random() * 2 - 1)
        ];
        const label = Math.random() > 0.5 ? 1 : 0;

        const response = await fetch(`${API_BASE} /api/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ features, label })
        });

        const data = await response.json();

        showSuccess(`Data ingested! Window size: ${data.current_window_size} `);

        // Refresh metrics after a short delay
        setTimeout(refreshMetrics, 1000);

    } catch (error) {
        showError('Ingestion failed: ' + error.message);
    }
}

// Check drift
async function checkDrift() {
    try {
        await updateDriftStatus();
        showSuccess('Drift check completed!');
    } catch (error) {
        showError('Drift check failed: ' + error.message);
    }
}

// Trigger retraining
async function triggerRetrain() {
    if (!confirm('Are you sure you want to trigger retraining? This may take a few moments.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE} /api/force_retrain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                drift_score: 75.0,
                reason: 'manual_trigger_from_dashboard'
            })
        });

        const data = await response.json();

        if (data.success) {
            showModal(`
    < h2 > Retraining Complete ✅</h2 >
                <p><strong>New Version:</strong> ${data.version}</p>
                <p><strong>Old Accuracy:</strong> ${(data.old_accuracy * 100).toFixed(2)}%</p>
                <p><strong>New Accuracy:</strong> ${(data.new_accuracy * 100).toFixed(2)}%</p>
                <p><strong>Improvement:</strong> ${(data.improvement * 100).toFixed(2)}%</p>
                <p><strong>Promoted:</strong> ${data.promoted ? 'Yes ✅' : 'No ⚠️'}</p>
                <p><strong>Duration:</strong> ${data.duration_seconds.toFixed(2)}s</p>
`);

            setTimeout(refreshMetrics, 2000);
        } else {
            showError('Retraining failed: ' + data.reason);
        }

    } catch (error) {
        showError('Retraining failed: ' + error.message);
    }
}

// Show models
async function showModels() {
    try {
        const response = await fetch(`${API_BASE} /api/model / list`);
        const data = await response.json();

        const modelsHtml = data.models.map(m => `
    < div style = "border: 1px solid #334155; padding: 15px; margin: 10px 0; border-radius: 8px;" >
                <h3>${m.version} ${m.champion ? '👑' : ''} ${m.promoted ? '✅' : ''}</h3>
                <p><strong>Accuracy:</strong> ${(m.accuracy * 100).toFixed(2)}%</p>
                <p><strong>Drift Score:</strong> ${m.drift_score.toFixed(2)}</p>
                <p><strong>Created:</strong> ${new Date(m.created_at).toLocaleString()}</p>
                <p><strong>Samples:</strong> ${m.training_samples}</p>
            </div >
    `).join('');

        showModal(`
    < h2 > Model Registry(${data.count} models)</h2 >
        ${modelsHtml}
`);

    } catch (error) {
        showError('Failed to load models: ' + error.message);
    }
}

// Modal functions
function showModal(content) {
    document.getElementById('modalBody').innerHTML = content;
    document.getElementById('modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

// Toast notifications
function showSuccess(message) {
    alert('✅ ' + message);  // Simple version, can be enhanced with toast library
}

function showError(message) {
    alert('❌ ' + message);
}

// Close modal on outside click
window.onclick = function (event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) {
        closeModal();
    }
};
