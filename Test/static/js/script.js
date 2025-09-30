function renderLanes(lanesData) {
    lanesData.forEach(lane => {
        const [laneNo, totalVehicles, bigVehicles, smallVehicles, signalColor] = lane;
        
        // Update traffic light
        updateTrafficLight(laneNo, signalColor);
        
        // Render vehicles
        renderVehicles(laneNo, bigVehicles, smallVehicles);
    });
    
    // Update stats panel
    updateStats(lanesData);
}

function updateTrafficLight(laneNo, color) {
    const laneElement = document.getElementById(`lane-${laneNo}`);
    if (!laneElement) return;
    
    const lights = laneElement.querySelectorAll('.light');
    lights.forEach(light => light.classList.remove('active'));
    
    if (color === 'red') {
        lights[0].classList.add('active');
    } else if (color === 'yellow') {
        lights[1].classList.add('active');
    } else if (color === 'green') {
        lights[2].classList.add('active');
    }
}

function renderVehicles(laneNo, bigCount, smallCount) {
    const container = document.getElementById(`vehicles-${laneNo}`);
    if (!container) return;
    
    container.innerHTML = '';
    
    // Limit vehicles to prevent overflow (max 10 vehicles total per lane)
    const maxVehicles = 10;
    const totalVehicles = bigCount + smallCount;
    
    if (totalVehicles > maxVehicles) {
        const ratio = maxVehicles / totalVehicles;
        bigCount = Math.floor(bigCount * ratio);
        smallCount = maxVehicles - bigCount;
    }
    
    // Render big vehicles
    for (let i = 0; i < bigCount; i++) {
        const vehicle = document.createElement('div');
        vehicle.className = 'vehicle big-vehicle';
        vehicle.textContent = '🚚';
        container.appendChild(vehicle);
    }
    
    // Render small vehicles
    for (let i = 0; i < smallCount; i++) {
        const vehicle = document.createElement('div');
        vehicle.className = 'vehicle small-vehicle';
        vehicle.textContent = '🚗';
        container.appendChild(vehicle);
    }
}

function updateStats(lanesData) {
    const statsContainer = document.getElementById('stats-container');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = '';
    
    const directions = ['North', 'East', 'South', 'West'];
    
    lanesData.forEach((lane, index) => {
        const [laneNo, totalVehicles, bigVehicles, smallVehicles, signalColor] = lane;
        
        const statItem = document.createElement('div');
        statItem.className = 'stat-item';
        
        statItem.innerHTML = `
            <h4>
                Lane ${laneNo} - ${directions[index] || 'Unknown'}
                <span class="signal-indicator signal-${signalColor}"></span>
            </h4>
            <div class="stat-row">
                <span class="stat-label">Total Vehicles:</span>
                <span class="stat-value">${totalVehicles}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">🚚 Big Vehicles:</span>
                <span class="stat-value">${bigVehicles}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">🚗 Small Vehicles:</span>
                <span class="stat-value">${smallVehicles}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Signal:</span>
                <span class="stat-value" style="color: ${getSignalColor(signalColor)}">${signalColor.toUpperCase()}</span>
            </div>
        `;
        
        statsContainer.appendChild(statItem);
    });
}

function getSignalColor(signal) {
    switch(signal) {
        case 'red': return '#ff4757';
        case 'yellow': return '#ffa502';
        case 'green': return '#26de81';
        default: return '#333';
    }
}

async function fetchLanes() {
    try {
        const response = await fetch('/api/lanes');
        const data = await response.json();
        renderLanes(data.lanes);
    } catch (error) {
        console.error('Error fetching lanes:', error);
    }
}

async function updateSignal() {
    try {
        const response = await fetch('/api/update_signal');
        const data = await response.json();
        renderLanes(data.lanes);
    } catch (error) {
        console.error('Error updating signal:', error);
    }
}

async function updateVehicles() {
    try {
        const response = await fetch('/api/update_vehicles');
        const data = await response.json();
        renderLanes(data.lanes);
    } catch (error) {
        console.error('Error updating vehicles:', error);
    }
}

// Initial load
fetchLanes();

// Auto-update signal every 5 seconds
setInterval(updateSignal, 5000);

// Auto-update vehicles every 3 seconds
setInterval(updateVehicles, 3000);

// Auto-refresh every 2 seconds
setInterval(fetchLanes, 2000);