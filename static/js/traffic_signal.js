// Traffic Signal Visualization Module

function initTrafficSignal() {
    // The simulation is now updated by the main script.js `updateDashboardData` function.
    // We call it once on initialization to load the initial state.
    updateSimulationWithData();
}

function updateTrafficSignalLight(laneNo, color) {
    const laneElement = document.getElementById(`signal-lane-${laneNo}`);
    if (!laneElement) return;
    
    const lights = laneElement.querySelectorAll('.signal-light');
    lights.forEach(light => light.classList.remove('active'));
    
    if (color === 'red') {
        lights[0].classList.add('active');
    } else if (color === 'yellow') {
        lights[1].classList.add('active');
    } else if (color === 'green') {
        lights[2].classList.add('active');
    }
}

function renderTrafficVehicles(laneNo, totalVehicles) {
    const container = document.getElementById(`signal-vehicles-${laneNo}`);
    if (!container) return;
    
    container.innerHTML = '';
    
    const maxVehicles = 10;
    let vehiclesToRender = Math.min(totalVehicles, maxVehicles);
    
    // For simplicity, we'll just render all as small vehicles (cars)
    for (let i = 0; i < vehiclesToRender; i++) {
        const vehicle = document.createElement('div');
        vehicle.className = 'signal-vehicle signal-small-vehicle';
        vehicle.textContent = '🚗';
        container.appendChild(vehicle);
    }
}

function updateTrafficStats(lanesData) {
    const statsContainer = document.getElementById('signal-stats-container');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = '';
    const directions = ['North', 'East', 'South', 'West'];
    
    lanesData.forEach((lane, index) => {
        const [laneNo, totalVehicles, signalColor] = lane;
        
        const statItem = document.createElement('div');
        statItem.className = 'signal-stat-item';
        
        statItem.innerHTML = `
            <h4>
                Lane ${laneNo} - ${directions[index] || 'Unknown'}
                <span class="signal-indicator signal-${signalColor}"></span>
            </h4>
            <div class="signal-stat-row">
                <span class="signal-stat-label">Total Vehicles:</span>
                <span class="signal-stat-value">${totalVehicles}</span>
            </div>
            <div class="signal-stat-row">
                <span class="signal-stat-label">Signal:</span>
                <span class="signal-stat-value" style="color: ${getTrafficSignalColor(signalColor)}">${signalColor.toUpperCase()}</span>
            </div>
        `;
        
        statsContainer.appendChild(statItem);
    });
}

function getTrafficSignalColor(signal) {
    switch(signal) {
        case 'red': return '#ff4757';
        case 'yellow': return '#ffa502';
        case 'green': return '#26de81';
        default: return '#333';
    }
}

function renderTrafficLanes(lanesData) {
    lanesData.forEach(lane => {
        const [laneNo, totalVehicles, signalColor] = lane;
        updateTrafficSignalLight(laneNo, signalColor);
        renderTrafficVehicles(laneNo, totalVehicles);
    });
    updateTrafficStats(lanesData);
}

/**
 * Fetches data from the /api/lanes endpoint and updates the simulation visuals.
 * This function is called by the main script.js to ensure data consistency
 * with the rest of the dashboard.
 */
async function updateSimulationWithData(lanesData) {
    if (!lanesData) {
        console.error("updateSimulationWithData called with no lane data.");
        return;
    }
    // The data is already in the correct format from the backend, so we can render it directly.
    renderTrafficLanes(lanesData);
}

// --- Initialization Logic ---

let simulationInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    const trafficDetectionTab = document.querySelector('[data-tab="traffic-detection"]');
    
    if (trafficDetectionTab) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === "class" && 
                    trafficDetectionTab.classList.contains('active') && 
                    !simulationInitialized) {
                    
                    console.log("Traffic Detection tab is active, initializing simulation.");
                    initTrafficSignal();
                    simulationInitialized = true;
                    observer.disconnect(); // Stop observing once initialized
                }
            });
        });

        observer.observe(trafficDetectionTab, { attributes: true });
    }
});