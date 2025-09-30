// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Update dashboard data periodically
    updateDashboardData();
    setInterval(updateDashboardData, 3000); // Update every 3 seconds

    // Update traffic light timers
    updateTrafficLights();
    setInterval(updateTrafficLights, 1000); // Update every second
});

// Function to update dashboard data
async function updateDashboardData() {
    try {
        const response = await fetch('/api/dashboard-data');
        const data = await response.json();
        
        // Update vehicle statistics in Live Camera tab
        const totalVehiclesElem = document.querySelector('#live-camera #total-vehicles');
        const avgSpeedElem = document.querySelector('#live-camera #avg-speed');
        
        if (totalVehiclesElem) totalVehiclesElem.textContent = data.total_vehicles;
        if (avgSpeedElem) avgSpeedElem.textContent = data.avg_speed;
        
        // Update vehicle statistics in Manageable Components tab
        const totalVehiclesCompElem = document.querySelector('#manageable-components #total-vehicles');
        const avgSpeedCompElem = document.getElementById('avg-speed-comp');
        const avgCongestionElem = document.getElementById('avg-congestion');
        
        if (totalVehiclesCompElem) totalVehiclesCompElem.textContent = data.total_vehicles;
        if (avgSpeedCompElem) avgSpeedCompElem.textContent = data.avg_speed;
        if (avgCongestionElem) avgCongestionElem.textContent = data.avg_congestion + '%';
        
        // Update alerts
        if (data.recent_alerts && data.recent_alerts.length > 0) {
            const alertTypeElem = document.getElementById('recent_alerts_type');
            const alertMessageElem = document.getElementById('recent_alerts_message');
            const alertTimeElem = document.getElementById('recent_alerts_time');
            
            if (alertTypeElem) alertTypeElem.textContent = data.recent_alerts[0].type;
            if (alertMessageElem) alertMessageElem.textContent = data.recent_alerts[0].message;
            if (alertTimeElem) alertTimeElem.textContent = data.recent_alerts[0].time;
            
            if (data.recent_alerts.length > 1) {
                const warningTypeElem = document.getElementById('recent_warning_type');
                const warningMessageElem = document.getElementById('recent_warning_message');
                const warningTimeElem = document.getElementById('recent_warning_time');
                
                if (warningTypeElem) warningTypeElem.textContent = data.recent_alerts[1].type;
                if (warningMessageElem) warningMessageElem.textContent = data.recent_alerts[1].message;
                if (warningTimeElem) warningTimeElem.textContent = data.recent_alerts[1].time;
            }
        }
        
        // Update lane data
        const laneResponse = await fetch('/api/lane-feeds');
        const laneData = await laneResponse.json();
        
        laneData.forEach((lane, index) => {
            const laneNum = index + 1;
            
            // Update camera feed stats (in Live Camera tab)
            const cameraVehiclesElem = document.querySelector(`#live-camera #lane${laneNum}-vehicles`);
            const cameraSpeedElem = document.querySelector(`#live-camera #lane${laneNum}-speed`);
            const cameraTrafficElem = document.querySelector(`#live-camera #lane${laneNum}-traffic`);
            
            if (cameraVehiclesElem) cameraVehiclesElem.textContent = lane.vehicles;
            if (cameraSpeedElem) cameraSpeedElem.textContent = lane.speed;
            if (cameraTrafficElem) {
                cameraTrafficElem.textContent = lane.traffic + '%';
                
                // Update traffic level classes
                cameraTrafficElem.className = 'value';
                if (lane.traffic > 70) {
                    cameraTrafficElem.classList.add('traffic-high');
                } else if (lane.traffic > 40) {
                    cameraTrafficElem.classList.add('traffic-medium');
                } else {
                    cameraTrafficElem.classList.add('traffic-low');
                }
            }
            
            // Update Lane Usage & Performance section (in Manageable Components tab)
            const laneVehiclesElem = document.querySelector(`#manageable-components .lane-item:nth-child(${laneNum}) .lane-stat:nth-child(1) .value`);
            const laneSpeedElem = document.querySelector(`#manageable-components .lane-item:nth-child(${laneNum}) .lane-stat:nth-child(2) .value`);
            const laneTrafficElem = document.querySelector(`#manageable-components .lane-item:nth-child(${laneNum}) .lane-stat:nth-child(3) .value`);
            const laneStatusElem = document.querySelector(`#manageable-components .lane-item:nth-child(${laneNum}) .status-badge`);
            
            if (laneVehiclesElem) laneVehiclesElem.textContent = lane.vehicles;
            if (laneSpeedElem) laneSpeedElem.textContent = lane.speed;
            if (laneTrafficElem) laneTrafficElem.textContent = lane.traffic + '%';
            
            if (laneStatusElem) {
                laneStatusElem.textContent = lane.status;
                // Update status badge classes
                laneStatusElem.className = 'status-badge';
                if (lane.status === 'WARNING') {
                    laneStatusElem.classList.add('warning');
                } else if (lane.status === 'ACTIVE') {
                    laneStatusElem.classList.add('active');
                } else if (lane.status === 'ERROR') {
                    laneStatusElem.classList.add('error');
                }
            }
        });

        //lane alerts
        
        // Update vehicle distribution bars
        const distribution = data.vehicle_distribution;
        const barCars = document.querySelector('.bar-cars');
        const barTrucks = document.querySelector('.bar-trucks');
        const barBuses = document.querySelector('.bar-buses');
        const barBikes = document.querySelector('.bar-bikes');
        
        if (barCars) {
            barCars.style.width = distribution.cars + '%';
            barCars.parentElement.nextElementSibling.textContent = distribution.cars + '%';
        }
        if (barTrucks) {
            barTrucks.style.width = distribution.trucks + '%';
            barTrucks.parentElement.nextElementSibling.textContent = distribution.trucks + '%';
        }
        if (barBuses) {
            barBuses.style.width = distribution.buses + '%';
            barBuses.parentElement.nextElementSibling.textContent = distribution.buses + '%';
        }
        if (barBikes) {
            barBikes.style.width = distribution.bikes + '%';
            barBikes.parentElement.nextElementSibling.textContent = distribution.bikes + '%';
        }
        
    } catch (error) {
        console.error('Error updating dashboard data:', error);
    }
}

// Function to update traffic light timers
function updateTrafficLights() {
    const lights = document.querySelectorAll('.light.active .timer');
    lights.forEach(timer => {
        let currentTime = parseInt(timer.textContent);
        if (currentTime > 0) {
            timer.textContent = currentTime - 1;
        }
    });
    
    // Update mini intersection timers
    const miniTimers = document.querySelectorAll('.intersection-timer');
    miniTimers.forEach(timer => {
        let currentTime = parseInt(timer.textContent.replace('s', ''));
        if (currentTime > 0) {
            timer.textContent = (currentTime - 1) + 's';
        }
    });
}

// Emergency controls
document.addEventListener('click', function(e) {
    if (e.target.closest('.emergency-btn')) {
        if (confirm('Are you sure you want to stop all traffic signals? This will activate emergency mode.')) {
            showNotification('Emergency mode activated. All signals stopped.', 'warning');
        }
    }
    
    if (e.target.closest('.priority-btn')) {
        showNotification('Priority vehicle override activated.', 'info');
    }
});

// Show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}