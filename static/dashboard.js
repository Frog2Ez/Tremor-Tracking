const API_BASE = 'http://localhost:5000';
let currentPatientId = null;
let charts = {};

// Initialize on page load
window.addEventListener('load', () => {
    refreshStats();
    loadPatients();
});

function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
    setTimeout(() => {
        statusDiv.innerHTML = '';
    }, 5000);
}

async function refreshStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const data = await response.json();
        document.getElementById('totalPatients').textContent = data.patients || 0;
        document.getElementById('totalReadings').textContent = data.readings || 0;
        document.getElementById('totalUploads').textContent = data.uploads || 0;
        
        showStatus('✓ Statistics refreshed', 'success');
    } catch (error) {
        showStatus('✗ Cannot connect to backend. Make sure Flask server is running on http://localhost:5000', 'error');
        console.error('Error:', error);
    }
}

async function loadPatients() {
    try {
        const response = await fetch(`${API_BASE}/api/patients`);
        if (!response.ok) throw new Error('Failed to fetch patients');
        
        const data = await response.json();
        const select = document.getElementById('patientSelect');
        
        if (data.patients.length === 0) {
            select.innerHTML = '<option value="">No patients found - Run the simulator first</option>';
            return;
        }
        
        select.innerHTML = '<option value="">-- Select a patient --</option>';
        data.patients.forEach(patient => {
            const option = document.createElement('option');
            option.value = patient.patient_id;
            option.textContent = `${patient.patient_id} (${patient.reading_count} readings)`;
            select.appendChild(option);
        });
        
        showStatus(`Found ${data.patients.length} patient(s)`, 'success');
    } catch (error) {
        showStatus('Error loading patients', 'error');
        console.error('Error:', error);
    }
}

async function loadPatientData() {
    const select = document.getElementById('patientSelect');
    const patientId = select.value;
    
    if (!patientId) {
        showStatus('Please select a patient first', 'error');
        return;
    }
    
    currentPatientId = patientId;
    const chartsContainer = document.getElementById('chartsContainer');
    chartsContainer.innerHTML = '<div class="loading">Loading tremor data...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/patients/${patientId}/data?limit=500`);
        if (!response.ok) throw new Error('Failed to fetch patient data');
        
        const data = await response.json();
        
        if (data.readings.length === 0) {
            chartsContainer.innerHTML = `
                <div class="chart-container">
                    <div class="no-data">
                        <div class="no-data-icon">📊</div>
                        <h2>No Data Available</h2>
                        <p>This patient has no sensor readings yet.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        showStatus(`✓ Loaded ${data.readings.length} readings for ${patientId}`, 'success');
        renderCharts(data.readings);
        
    } catch (error) {
        showStatus('Error loading patient data', 'error');
        console.error('Error:', error);
        chartsContainer.innerHTML = '';
    }
}

function renderCharts(readings) {
    // Reverse to show chronological order
    readings = readings.reverse();
    
    // Prepare data
    const labels = readings.map((r, i) => i); // Sample index
    const accelData = {
        x: readings.map(r => r.accelerometer.x),
        y: readings.map(r => r.accelerometer.y),
        z: readings.map(r => r.accelerometer.z)
    };
    const gyroData = {
        x: readings.map(r => r.gyroscope.x),
        y: readings.map(r => r.gyroscope.y),
        z: readings.map(r => r.gyroscope.z)
    };
    
    // Calculate tremor magnitude (overall shaking intensity)
    const tremorMagnitude = readings.map(r => {
        const ax = r.accelerometer.x;
        const ay = r.accelerometer.y - 9.81; // Remove gravity
        const az = r.accelerometer.z;
        return Math.sqrt(ax*ax + ay*ay + az*az);
    });
    
    const chartsContainer = document.getElementById('chartsContainer');
    chartsContainer.innerHTML = `
        <div class="chart-container">
            <div class="chart-title">📈 Tremor Intensity Over Time</div>
            <canvas id="tremorChart"></canvas>
        </div>
        <div class="chart-container">
            <div class="chart-title">📊 Accelerometer Data (X, Y, Z axes)</div>
            <canvas id="accelChart"></canvas>
        </div>
        <div class="chart-container">
            <div class="chart-title">🔄 Gyroscope Data (Rotation)</div>
            <canvas id="gyroChart"></canvas>
        </div>
    `;
    
    // Destroy old charts
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    
    // Tremor magnitude chart
    charts.tremor = new Chart(document.getElementById('tremorChart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Tremor Magnitude (m/s²)',
                data: tremorMagnitude,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 3,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Sample Number' }
                },
                y: { 
                    title: { display: true, text: 'Magnitude (m/s²)' }
                }
            }
        }
    });
    
    // Accelerometer chart
    charts.accel = new Chart(document.getElementById('accelChart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'X-axis',
                    data: accelData.x,
                    borderColor: '#ff6384',
                    borderWidth: 1.5,
                    pointRadius: 0
                },
                {
                    label: 'Y-axis',
                    data: accelData.y,
                    borderColor: '#36a2eb',
                    borderWidth: 1.5,
                    pointRadius: 0
                },
                {
                    label: 'Z-axis',
                    data: accelData.z,
                    borderColor: '#4bc0c0',
                    borderWidth: 1.5,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 3,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Sample Number' }
                },
                y: { 
                    title: { display: true, text: 'Acceleration (m/s²)' }
                }
            }
        }
    });
    
    // Gyroscope chart
    charts.gyro = new Chart(document.getElementById('gyroChart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'X-axis',
                    data: gyroData.x,
                    borderColor: '#ff6384',
                    borderWidth: 1.5,
                    pointRadius: 0
                },
                {
                    label: 'Y-axis',
                    data: gyroData.y,
                    borderColor: '#36a2eb',
                    borderWidth: 1.5,
                    pointRadius: 0
                },
                {
                    label: 'Z-axis',
                    data: gyroData.z,
                    borderColor: '#4bc0c0',
                    borderWidth: 1.5,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 3,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Sample Number' }
                },
                y: { 
                    title: { display: true, text: 'Angular Velocity (rad/s)' }
                }
            }
        }
    });
}