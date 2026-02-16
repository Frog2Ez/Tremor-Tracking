# Tremor Tracker - Flask Backend
### Smart Accessory for Tracking Parkinson's Tremors

**Author:** Odhrán Sisk (A00310150)

## Overview

This Flask application provides a REST API backend for a personal Parkinson's tremor tracking system. It's designed to help track tremor patterns accurately over time, addressing the challenge of memory-based recall during doctor visits.

### The Problem

People with Parkinson's disease are often asked to recall when their tremors were worst over the past week or month. However, Parkinson's also affects memory, making these answers unreliable. This system provides objective, visual data to show doctors exactly when tremors occurred and their severity.

### The Solution

This backend works with:
- **Smartwatch/Wearable**: Captures continuous motion data during daily activities
- **React Frontend**: Visualizes tremor patterns with Chart.js graphs
- **SQLite Database**: Stores all sensor readings and session data

## Features

- ✅ **Single-user system** - No complex authentication needed
- ✅ **Session management** - Track discrete monitoring periods
- ✅ **Real-time data** - Support for continuous sensor streaming
- ✅ **Batch uploads** - Efficient for smartwatch battery life
- ✅ **Automatic scoring** - Calculates tremor intensity (0-10 scale)
- ✅ **Historical analysis** - View tremor patterns over days/weeks/months
- ✅ **Simulation mode** - Test with dummy data before real sensor integration

## Technology Stack

Based on the technologies selected in the project interim report:

- **Backend**: Python 3.8+ with Flask framework
- **Database**: SQLite (simple, portable, perfect for single-user)
- **Sensors**: Accelerometer + Gyroscope (research-backed approach)
- **Communication**: REST API with JSON
- **Frontend Integration**: CORS-enabled for React + Chart.js

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The API will start on `http://localhost:5000`

Database tables are created automatically on first run.

## Quick Start

### Test the API

```bash
# Check if running
curl http://localhost:5000/api/health

# Start a monitoring session
curl -X POST http://localhost:5000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"notes": "Morning session"}'

# Generate test data for session 1
curl -X POST http://localhost:5000/api/simulate-data \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "duration_seconds": 60,
    "frequency": 10
  }'

# Get recent sensor data
curl "http://localhost:5000/api/sensor-data/recent?limit=50"

# End the session
curl -X PUT http://localhost:5000/api/sessions/1/end

# Get statistics for past 7 days
curl "http://localhost:5000/api/statistics?days=7"
```

## API Endpoints

### Health & Status

```
GET /api/health
```
Check if API is running and get database stats.

### Session Management

#### Start new session
```
POST /api/sessions
{
  "notes": "Morning session after medication"  // optional
}
```

#### End session
```
PUT /api/sessions/<session_id>/end
```
Calculates tremor statistics automatically.

#### Get all sessions
```
GET /api/sessions?limit=10&include_active=true
```

#### Get specific session
```
GET /api/sessions/<session_id>
```

#### Get active session
```
GET /api/sessions/active
```
Returns currently running session (if any).

### Sensor Data

#### Add single reading
```
POST /api/sensor-data
{
  "session_id": 1,           // optional
  "gyro_x": 0.5,             // required (rad/s)
  "gyro_y": -0.3,            // required (rad/s)
  "gyro_z": 0.2,             // required (rad/s)
  "accel_x": 9.8,            // optional (m/s²)
  "accel_y": 0.1,            // optional (m/s²)
  "accel_z": 0.0,            // optional (m/s²)
  "device_id": "watch_001"   // optional
}
```

#### Add batch readings (recommended for battery efficiency)
```
POST /api/sensor-data
{
  "session_id": 1,
  "device_id": "watch_001",
  "readings": [
    {
      "gyro_x": 0.5, "gyro_y": -0.3, "gyro_z": 0.2,
      "accel_x": 9.8, "accel_y": 0.1, "accel_z": 0.0,
      "timestamp": "2024-01-01T12:00:00"
    },
    // ... more readings
  ]
}
```

#### Get recent data (for real-time charts)
```
GET /api/sensor-data/recent?session_id=1&limit=100&seconds=60
```

#### Get all session data
```
GET /api/sessions/<session_id>/data
```

### Analytics

#### Get statistics
```
GET /api/statistics?days=7
```
Returns:
- Overall tremor statistics
- Daily averages
- Session summaries
- Trend analysis

### Testing

#### Generate simulated data
```
POST /api/simulate-data
{
  "session_id": 1,
  "duration_seconds": 120,
  "frequency": 10  // readings per second
}
```
Generates realistic tremor data at 4-6 Hz (typical Parkinson's frequency).

## Integration Examples

### React Frontend Integration

```javascript
const API_URL = 'http://localhost:5000/api';

// Start a monitoring session
const startSession = async (notes) => {
  const response = await fetch(`${API_URL}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });
  return response.json();
};

// Get recent data for real-time chart
const getRecentData = async (sessionId) => {
  const response = await fetch(
    `${API_URL}/sensor-data/recent?session_id=${sessionId}&limit=100&seconds=60`
  );
  const data = await response.json();
  
  // Format for Chart.js
  return {
    labels: data.data.map(r => new Date(r.timestamp)),
    datasets: [{
      label: 'Tremor Intensity',
      data: data.data.map(r => r.tremor_score),
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1
    }]
  };
};

// End session
const endSession = async (sessionId) => {
  const response = await fetch(`${API_URL}/sessions/${sessionId}/end`, {
    method: 'PUT',
  });
  return response.json();
};
```

### Android Device Integration

Example Android code to collect and send gyroscope data:

```kotlin
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager

class TremorMonitor : SensorEventListener {
    private val sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val gyroscope = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
    private val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    
    private val readings = mutableListOf<SensorReading>()
    
    fun startMonitoring() {
        sensorManager.registerListener(this, gyroscope, SensorManager.SENSOR_DELAY_NORMAL)
        sensorManager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_NORMAL)
    }
    
    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_GYROSCOPE -> {
                val reading = SensorReading(
                    gyro_x = event.values[0],
                    gyro_y = event.values[1],
                    gyro_z = event.values[2],
                    timestamp = System.currentTimeMillis()
                )
                readings.add(reading)
                
                // Batch upload every 100 readings for battery efficiency
                if (readings.size >= 100) {
                    uploadReadings()
                }
            }
        }
    }
    
    private fun uploadReadings() {
        // Send to Flask backend
        val json = JSONObject().apply {
            put("session_id", currentSessionId)
            put("device_id", getDeviceId())
            put("readings", JSONArray(readings))
        }
        
        // HTTP POST to /api/sensor-data
        // ... (use OkHttp or similar)
        
        readings.clear()
    }
}
```

## Database

### Structure

See `DATABASE_SCHEMA.md` for detailed schema documentation.

**Tables:**
- `tremor_sessions`: Monitoring sessions with calculated statistics
- `sensor_readings`: Individual sensor readings with tremor scores

### Viewing Data

```bash
# Open database in sqlite3
sqlite3 tremor_tracker.db

# View sessions
SELECT * FROM tremor_sessions ORDER BY session_start DESC LIMIT 5;

# View recent readings
SELECT timestamp, tremor_score FROM sensor_readings 
ORDER BY timestamp DESC LIMIT 10;
```

## Tremor Scoring

### Current Algorithm

Simple magnitude-based scoring:
1. Calculate gyroscope magnitude: `sqrt(x² + y² + z²)`
2. Normalize to 0-10 scale: `score = min(magnitude * 2, 10)`

### Future Enhancements

As mentioned in the project report, production version should implement:

1. **FFT Analysis** using SciKit Digital Health library
   - Detect 4-6 Hz frequency (Parkinson's tremor characteristic)
   - Filter out non-tremor movements

2. **Machine Learning Classification**
   - Train on labeled tremor data
   - Map to clinical severity scales (UPDRS)

3. **Multi-Sensor Fusion**
   - Combine accelerometer and gyroscope
   - More robust detection

## Project Structure

```
tremor-tracker-backend/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── DATABASE_SCHEMA.md      # Database documentation
├── README.md              # This file
├── QUICKSTART.md          # Quick start guide
└── tremor_tracker.db      # SQLite database (created on first run)
```

## Testing

The `/api/simulate-data` endpoint generates realistic tremor data for testing:

- Simulates 4-6 Hz tremor frequency (typical for Parkinson's)
- Adds random variation and noise
- Useful for testing frontend visualizations before hardware is ready

## Production Deployment

For production use:

1. **Use Gunicorn** instead of Flask development server:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set environment variables**:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=random-secret-key-here
   ```

3. **Consider database backups**:
   - SQLite file is easily backed up (just copy `tremor_tracker.db`)
   - Use `/api/simulate-data` endpoint to export data to JSON if needed

4. **Security considerations**:
   - This is designed for personal use, not multi-user deployment
   - If deploying remotely, add HTTPS and authentication
   - Protect PHI (Protected Health Information) appropriately

## Alignment with Project Report

This implementation follows the architecture defined in the interim report:

- ✅ Flask backend with Python (Section 3.3)
- ✅ SQLite/PostgreSQL database support (Section 3.4)
- ✅ REST API for React frontend integration (Section 3.5)
- ✅ Accelerometer + Gyroscope data collection (Section 3.1)
- ✅ Wireless communication support (Section 3.6)
- ✅ Simulation mode for prototyping (Section 4)
- ✅ Background operation with minimal user interaction (Section 3.2)

## Support & Documentation

- **Database Schema**: See `DATABASE_SCHEMA.md`
- **Quick Start**: See `QUICKSTART.md`
- **API Reference**: This README

## License

Educational/Research project for Ulster University.

## Acknowledgments

- Research citations from project interim report
- Designed to address real-world need for objective tremor tracking
- Built with guidance from Parkinson's disease research literature
