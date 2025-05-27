// Dashboard JavaScript functionality

// Global variables
let refreshInterval = null;
let statusChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupAutoRefresh();
});

function initializeDashboard() {
    // Initialize any interactive elements
    setupEventListeners();
    
    // Start periodic updates
    updateStatus();
}

function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function(e) {
            e.preventDefault();
            refreshDashboard();
        });
    }
    
    // Status badges click handlers
    document.querySelectorAll('.badge').forEach(badge => {
        badge.style.cursor = 'pointer';
        badge.addEventListener('click', function() {
            filterClientsByStatus(this.textContent.toLowerCase());
        });
    });
}

function refreshDashboard() {
    // Show loading state
    showLoadingState();
    
    // Refresh the page
    location.reload();
}

function showLoadingState() {
    const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
    if (refreshBtn) {
        const icon = refreshBtn.querySelector('i');
        if (icon) {
            icon.style.animation = 'spin 1s linear infinite';
        }
    }
}

function updateStatus() {
    // Update client status indicators
    updateClientStatusIndicators();
    
    // Update alerts
    refreshAlerts();
}

function updateClientStatusIndicators() {
    // Update time-ago indicators
    document.querySelectorAll('.time-ago').forEach(element => {
        const timeStr = element.getAttribute('data-time');
        if (timeStr) {
            const time = new Date(timeStr);
            const now = new Date();
            const diff = now - time;
            const minutes = Math.floor(diff / 60000);
            
            let timeAgoText = '';
            if (minutes < 1) {
                timeAgoText = 'Just now';
            } else if (minutes < 60) {
                timeAgoText = `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
            } else if (minutes < 1440) {
                const hours = Math.floor(minutes / 60);
                timeAgoText = `${hours} hour${hours > 1 ? 's' : ''} ago`;
            } else {
                const days = Math.floor(minutes / 1440);
                timeAgoText = `${days} day${days > 1 ? 's' : ''} ago`;
            }
            
            element.textContent = timeAgoText;
            
            // Update status based on last check-in time
            updateClientRowStatus(element, minutes);
        }
    });
}

function updateClientRowStatus(timeElement, minutesSinceLastCheckin) {
    const row = timeElement.closest('tr');
    if (row) {
        const statusBadge = row.querySelector('.badge');
        if (statusBadge && minutesSinceLastCheckin > 5) {
            // Mark as offline if no check-in for more than 5 minutes
            if (!statusBadge.classList.contains('bg-secondary')) {
                statusBadge.className = 'badge bg-secondary';
                statusBadge.textContent = 'Offline';
            }
        }
    }
}

function refreshAlerts() {
    // Fetch latest alerts
    fetch('/api/alerts')
        .then(response => response.json())
        .then(alerts => {
            updateAlertsDisplay(alerts);
        })
        .catch(error => {
            console.error('Error fetching alerts:', error);
        });
}

function updateAlertsDisplay(alerts) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = `
            <div class="text-muted text-center">
                <i data-feather="check" class="me-2"></i>
                No active alerts
            </div>
        `;
    } else {
        alertsContainer.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.severity === 'critical' ? 'danger' : 'warning'} alert-sm mb-2">
                <small>
                    <strong>${alert.client_name}</strong>: ${alert.message}
                    <br>
                    <span class="text-muted">${new Date(alert.created_at).toLocaleString()}</span>
                </small>
            </div>
        `).join('');
    }
    
    // Re-initialize Feather icons
    feather.replace();
}

function filterClientsByStatus(status) {
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const statusBadge = row.querySelector('.badge');
        if (statusBadge) {
            const rowStatus = statusBadge.textContent.toLowerCase();
            if (status === 'all' || rowStatus.includes(status)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

function setupAutoRefresh() {
    // Auto-refresh every 30 seconds for status updates
    refreshInterval = setInterval(function() {
        updateStatus();
    }, 30000);
    
    // Full page refresh every 5 minutes
    setInterval(function() {
        refreshDashboard();
    }, 300000);
}

// Utility functions
function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    let result = '';
    if (days > 0) result += `${days}d `;
    if (hours > 0) result += `${hours}h `;
    if (minutes > 0) result += `${minutes}m`;
    
    return result || '0m';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getStatusColor(status) {
    const colors = {
        'healthy': 'success',
        'warning': 'warning',
        'critical': 'danger',
        'offline': 'secondary',
        'unknown': 'secondary'
    };
    return colors[status] || 'secondary';
}

// Export functions for global use
window.refreshDashboard = refreshDashboard;
window.refreshAlerts = refreshAlerts;
window.filterClientsByStatus = filterClientsByStatus;

// CSS animation for spin effect
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
