// Traffic Signal Visualization Module

function initTrafficSignal() {
    fetchTrafficLanes();
    setInterval(updateTrafficSignal, 5000);
    setInterval(updateTrafficVehicles, 3000);
    setInterval(fetchTrafficLanes, 2000);
}

function renderTrafficLanes(lanesData) {
    lanesData.forEach(lane => {
        const [laneNo, totalVehicles, bigVehicles, smallVehicles, signalColor] = lane;
        updateTrafficSignalLight(laneNo, signalColor);
        renderTrafficVehicles(laneNo, bigVehicles, smallVehicles);
    });
    updateTrafficStats(lanesData);
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

function renderTrafficVehicles(laneNo, bigCount, smallCount) {
    const container = document.getElementById(`signal-vehicles-${laneNo}`);
    if (!container) return;
    
    container.innerHTML = '';
    
    const maxVehicles = 10;
    const totalVehicles = bigCount + smallCount;
    
    if (totalVehicles > maxVehicles) {
        const ratio = maxVehicles / totalVehicles;
        bigCount = Math.floor(bigCount * ratio);
        smallCount = maxVehicles - bigCount;
    }
    
    for (let i = 0; i < bigCount; i++) {
        const vehicle = document.createElement('div');
        vehicle.className = 'signal-vehicle signal-big-vehicle';
        vehicle.textContent = '🚚';
        container.appendChild(vehicle);
    }
    
    for (let i = 0; i < smallCount; i++) {
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
        const [laneNo, totalVehicles, bigVehicles, smallVehicles, signalColor] = lane;
        
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
                <span class="signal-stat-label">🚚 Big Vehicles:</span>
                <span class="signal-stat-value">${bigVehicles}</span>
            </div>
            <div class="signal-stat-row">
                <span class="signal-stat-label">🚗 Small Vehicles:</span>
                <span class="signal-stat-value">${smallVehicles}</span>
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

async function fetchTrafficLanes() {
    try {
        const response = await fetch('/api/lanes');
        const data = await response.json();
        renderTrafficLanes(data.lanes);
    } catch (error) {
        console.error('Error fetching traffic lanes:', error);
    }
}

async function updateTrafficSignal() {
    try {
        const response = await fetch('/api/update_signal');
        const data = await response.json();
        renderTrafficLanes(data.lanes);
    } catch (error) {
        console.error('Error updating traffic signal:', error);
    }
}

async function updateTrafficVehicles() {
    try {
        const response = await fetch('/api/update_vehicles');
        const data = await response.json();
        renderTrafficLanes(data.lanes);
    } catch (error) {
        console.error('Error updating traffic vehicles:', error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const trafficDetectionTab = document.querySelector('[data-tab="traffic-detection"]');
    if (trafficDetectionTab) {
        trafficDetectionTab.addEventListener('click', function() {
            setTimeout(initTrafficSignal, 100);
        });
    }
});