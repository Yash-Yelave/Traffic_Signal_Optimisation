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
    setInterval(updateDashboardData, 5000); // Update every 5 seconds

    // Update traffic light timers
    updateTrafficLights();
    setInterval(updateTrafficLights, 1000); // Update every second
});

// Function to update dashboard data
async function updateDashboardData() {
    try {
        const response = await fetch('/api/dashboard-data');
        const data = await response.json();
        
        // Update vehicle statistics
        document.getElementById('total-vehicles').textContent = data.total_vehicles;
        document.getElementById('avg-speed').textContent = data.avg_speed;
        document.getElementById('total-vehicles-comp').textContent = data.total_vehicles;
        document.getElementById('avg-speed-comp').textContent = data.avg_speed;
        document.getElementById('avg-congestion').textContent = data.avg_congestion + '%';
        
        // Update lane data
        const laneResponse = await fetch('/api/lane-feeds');
        const laneData = await laneResponse.json();
        
        laneData.forEach((lane, index) => {
            const laneNum = index + 1;
            const vehiclesEl = document.getElementById(`lane${laneNum}-vehicles`);
            const speedEl = document.getElementById(`lane${laneNum}-speed`);
            const trafficEl = document.getElementById(`lane${laneNum}-traffic`);
            
            if (vehiclesEl) vehiclesEl.textContent = lane.vehicles;
            if (speedEl) speedEl.textContent = lane.speed;
            if (trafficEl) {
                trafficEl.textContent = lane.traffic + '%';
                
                // Update traffic level classes
                trafficEl.className = 'value';
                if (lane.traffic > 70) {
                    trafficEl.classList.add('traffic-high');
                } else if (lane.traffic > 40) {
                    trafficEl.classList.add('traffic-medium');
                } else {
                    trafficEl.classList.add('traffic-low');
                }
            }
        });
        
        // Update vehicle distribution bars
        const distribution = data.vehicle_distribution;
        document.querySelector('.bar-cars').style.width = distribution.cars + '%';
        document.querySelector('.bar-trucks').style.width = distribution.trucks + '%';
        document.querySelector('.bar-buses').style.width = distribution.buses + '%';
        document.querySelector('.bar-bikes').style.width = distribution.bikes + '%';
        
        // Update bar values
        document.querySelector('.bar-cars').parentElement.nextElementSibling.textContent = distribution.cars + '%';
        document.querySelector('.bar-trucks').parentElement.nextElementSibling.textContent = distribution.trucks + '%';
        document.querySelector('.bar-buses').parentElement.nextElementSibling.textContent = distribution.buses + '%';
        document.querySelector('.bar-bikes').parentElement.nextElementSibling.textContent = distribution.bikes + '%';
        
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