// This file handles fetching data and rendering charts for the Insights tab.

// Store chart instances to prevent re-creation and allow updates.
const charts = {};

document.addEventListener('DOMContentLoaded', () => {
    const refreshButton = document.getElementById('refresh-insights-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            console.log('Refreshing insights...');
            fetchAndRenderInsights();
        });
    }
});

/**
 * Fetches data from the API and renders all charts.
 * Can be used for both initialization and refreshing.
 */
async function fetchAndRenderInsights() {
    try {
        const response = await fetch(`/api/insights-data?cache_bust=${new Date().getTime()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (Object.keys(data).length === 0) {
            document.getElementById('insights-content').innerHTML = '<p class="no-data-message">No data available in the database yet. Let the system run for a few cycles.</p>';
            return;
        }

        // Render all charts with the fetched data
        renderBarChart('avgVehiclesChart', 'Average Vehicles Per Lane', data.avg_vehicles_per_lane);
        renderPieChart('actionReasonChart', 'Action Reasons Distribution', data.action_reason_counts);
        renderBarChart('avgGreenTimeChart', 'Average Green Time Per Lane (s)', data.avg_green_time_per_lane);
        renderLineChart('rewardOverTimeChart', 'Average Reward Over Time', data.reward_over_time);

    } catch (error) {
        console.error('Error fetching or rendering insights data:', error);
        document.getElementById('insights-content').innerHTML = `<p class="no-data-message">Error loading insights. Check the console for details.</p>`;
    }
}

/**
 * Generic function to render a bar chart.
 * @param {string} canvasId - The ID of the canvas element.
 * @param {string} label - The chart's title label.
 * @param {object} data - The data object {label: value, ...}.
 */
function renderBarChart(canvasId, label, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (charts[canvasId]) charts[canvasId].destroy(); // Destroy old chart if it exists

    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: label,
                data: Object.values(data),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

/**
 * Generic function to render a pie chart.
 * @param {string} canvasId - The ID of the canvas element.
 * @param {string} label - The chart's title label.
 * @param {object} data - The data object {label: value, ...}.
 */
function renderPieChart(canvasId, label, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (charts[canvasId]) charts[canvasId].destroy();

    charts[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: label,
                data: Object.values(data),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(153, 102, 255, 0.6)'
                ],
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

/**
 * Generic function to render a line chart.
 * @param {string} canvasId - The ID of the canvas element.
 * @param {string} label - The chart's title label.
 * @param {object} data - The data object {timestamps: [...], rewards: [...]}.
 */
function renderLineChart(canvasId, label, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (charts[canvasId]) charts[canvasId].destroy();

    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps,
            datasets: [{
                label: label,
                data: data.rewards,
                fill: false,
                borderColor: 'rgba(75, 192, 192, 1)',
                tension: 0.1
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}