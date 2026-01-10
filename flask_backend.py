"""
Flask Backend API for Parkinson's Tremor Monitoring
Receives sensor data from smartwatch and stores in database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

# Database configuration
DB_PATH = 'tremor_data.db'

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sensor readings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            accel_x REAL NOT NULL,
            accel_y REAL NOT NULL,
            accel_z REAL NOT NULL,
            gyro_x REAL NOT NULL,
            gyro_y REAL NOT NULL,
            gyro_z REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    ''')
    
    # Metadata table for batch uploads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS upload_metadata (
            upload_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            sample_rate_hz INTEGER,
            num_readings INTEGER,
            tremor_freq_hz REAL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """
    Endpoint to receive sensor data from smartwatch
    
    Expected JSON format:
    {
        "patient_id": "patient_001",
        "device_id": "smartwatch_001",
        "readings": [
            {
                "timestamp": "2024-01-10T10:30:00",
                "accelerometer": {"x": 0.5, "y": 9.8, "z": 0.2},
                "gyroscope": {"x": 0.1, "y": 0.05, "z": 0.03}
            },
            ...
        ],
        "metadata": {
            "sample_rate_hz": 50,
            "tremor_freq_hz": 5.2
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['patient_id', 'readings']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        patient_id = data['patient_id']
        device_id = data.get('device_id', 'unknown')
        readings = data['readings']
        metadata = data.get('metadata', {})
        
        if not readings:
            return jsonify({'error': 'No readings provided'}), 400
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Ensure patient exists
        cursor.execute('''
            INSERT OR IGNORE INTO patients (patient_id) VALUES (?)
        ''', (patient_id,))
        
        # Insert all readings
        for reading in readings:
            accel = reading['accelerometer']
            gyro = reading['gyroscope']
            timestamp = reading['timestamp']
            
            cursor.execute('''
                INSERT INTO sensor_readings 
                (patient_id, device_id, timestamp, accel_x, accel_y, accel_z, 
                 gyro_x, gyro_y, gyro_z)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id, device_id, timestamp,
                accel['x'], accel['y'], accel['z'],
                gyro['x'], gyro['y'], gyro['z']
            ))
        
        # Store metadata
        cursor.execute('''
            INSERT INTO upload_metadata 
            (patient_id, device_id, sample_rate_hz, num_readings, tremor_freq_hz)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            patient_id, device_id,
            metadata.get('sample_rate_hz'),
            len(readings),
            metadata.get('tremor_freq_hz')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Received and stored {len(readings)} readings',
            'patient_id': patient_id,
            'readings_count': len(readings)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<patient_id>/data', methods=['GET'])
def get_patient_data(patient_id):
    """
    Retrieve sensor data for a specific patient
    
    Query parameters:
    - limit: Maximum number of readings to return (default: 1000)
    - offset: Number of readings to skip (default: 0)
    """
    try:
        limit = request.args.get('limit', 1000, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get readings
        cursor.execute('''
            SELECT timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
            FROM sensor_readings
            WHERE patient_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (patient_id, limit, offset))
        
        rows = cursor.fetchall()
        
        readings = [
            {
                'timestamp': row[0],
                'accelerometer': {'x': row[1], 'y': row[2], 'z': row[3]},
                'gyroscope': {'x': row[4], 'y': row[5], 'z': row[6]}
            }
            for row in rows
        ]
        
        # Get total count
        cursor.execute('''
            SELECT COUNT(*) FROM sensor_readings WHERE patient_id = ?
        ''', (patient_id,))
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'patient_id': patient_id,
            'readings': readings,
            'count': len(readings),
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients', methods=['GET'])
def list_patients():
    """List all patients in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.patient_id, p.created_at, COUNT(sr.id) as reading_count
            FROM patients p
            LEFT JOIN sensor_readings sr ON p.patient_id = sr.patient_id
            GROUP BY p.patient_id, p.created_at
            ORDER BY p.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        
        patients = [
            {
                'patient_id': row[0],
                'created_at': row[1],
                'reading_count': row[2]
            }
            for row in rows
        ]
        
        conn.close()
        
        return jsonify({
            'patients': patients,
            'count': len(patients)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM patients')
        patient_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sensor_readings')
        reading_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM upload_metadata')
        upload_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'patients': patient_count,
            'readings': reading_count,
            'uploads': upload_count,
            'database_file': DB_PATH,
            'database_exists': os.path.exists(DB_PATH)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Tremor Monitoring API',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Flask Backend for Tremor Monitoring")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    print("\nAPI Endpoints:")
    print("  POST   /api/sensor-data          - Receive sensor data")
    print("  GET    /api/patients             - List all patients")
    print("  GET    /api/patients/<id>/data   - Get patient data")
    print("  GET    /api/stats                - Database statistics")
    print("  GET    /health                   - Health check")
    print("\n" + "=" * 60)
    print("Server starting on http://localhost:5000")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)