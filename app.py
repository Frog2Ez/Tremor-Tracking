"""
Smart Accessory for Tracking Parkinson's Tremors - Flask Backend
Single User Version

This Flask application serves as the backend for a personal Parkinson's tremor 
tracking system designed for individual use. It provides REST API endpoints for:
- Real-time sensor data collection from smartwatch/wearable
- Tremor monitoring session management
- Historical data retrieval and analysis
- Data visualization support

Author: Odhrán Sisk (A00310150)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import math
from typing import Dict, List

# Initialize Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) for React frontend
# This allows the React app to make requests to this backend
CORS(app)

# Database configuration
# Using SQLite for simplicity - single file database perfect for single-user application
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tremor_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking to save resources
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Initialize SQLAlchemy ORM
db = SQLAlchemy(app)

# ============================================================================
# DATABASE MODELS
# ============================================================================

class TremorSession(db.Model):
    """
    Tremor Session model
    Represents a monitoring session where tremor data is collected
    Each session contains multiple sensor readings
    
    Since this is a single-user system, no patient_id is needed
    """
    __tablename__ = 'tremor_sessions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Session metadata
    session_start = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_end = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)  # Duration in seconds
    
    # Tremor analysis results
    # These are calculated when the session ends based on all readings
    average_tremor_score = db.Column(db.Float, nullable=True)  # Average tremor intensity (0-10 scale)
    max_tremor_score = db.Column(db.Float, nullable=True)  # Maximum tremor detected
    min_tremor_score = db.Column(db.Float, nullable=True)  # Minimum tremor detected
    tremor_frequency_hz = db.Column(db.Float, nullable=True)  # Dominant tremor frequency
    
    # Session notes (e.g., "After medication", "Morning session", etc.)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    # One session can have many sensor readings
    sensor_readings = db.relationship('SensorReading', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict:
        """Convert session object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'session_start': self.session_start.isoformat(),
            'session_end': self.session_end.isoformat() if self.session_end else None,
            'duration_seconds': self.duration_seconds,
            'average_tremor_score': self.average_tremor_score,
            'max_tremor_score': self.max_tremor_score,
            'min_tremor_score': self.min_tremor_score,
            'tremor_frequency_hz': self.tremor_frequency_hz,
            'notes': self.notes
        }


class SensorReading(db.Model):
    """
    Sensor Reading model
    Stores individual accelerometer and gyroscope sensor readings from the wearable device
    
    Based on research (Barrachina-Fernández et al., 2021), both accelerometer and 
    gyroscope data are important for assessing Parkinson's tremor characteristics
    """
    __tablename__ = 'sensor_readings'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to session (nullable to allow readings outside of formal sessions)
    session_id = db.Column(db.Integer, db.ForeignKey('tremor_sessions.id'), nullable=True, index=True)
    
    # Timestamp of the reading
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Gyroscope data (rotation rates in radians/second)
    # Measures rotational movement - key indicator of tremor
    # x-axis: rotation around the x-axis (roll)
    gyro_x = db.Column(db.Float, nullable=False)
    # y-axis: rotation around the y-axis (pitch)
    gyro_y = db.Column(db.Float, nullable=False)
    # z-axis: rotation around the z-axis (yaw)
    gyro_z = db.Column(db.Float, nullable=False)
    
    # Accelerometer data (acceleration in m/s²)
    # Measures linear movement and gravity
    accel_x = db.Column(db.Float, nullable=True)
    accel_y = db.Column(db.Float, nullable=True)
    accel_z = db.Column(db.Float, nullable=True)
    
    # Calculated tremor metrics
    magnitude = db.Column(db.Float, nullable=True)  # Vector magnitude of gyroscope reading
    tremor_score = db.Column(db.Float, nullable=True)  # Computed tremor intensity score (0-10)
    
    # Device information
    device_id = db.Column(db.String(100), nullable=True)  # Identifier for the Android device/smartwatch
    
    def calculate_magnitude(self) -> float:
        """
        Calculate the magnitude of the gyroscope vector
        Uses 3D vector magnitude formula: sqrt(x² + y² + z²)
        
        This provides a single value representing overall rotational movement intensity
        """
        return math.sqrt(self.gyro_x**2 + self.gyro_y**2 + self.gyro_z**2)
    
    def calculate_tremor_score(self) -> float:
        """
        Calculate tremor intensity score based on gyroscope magnitude
        
        Parkinson's tremors typically occur at 4-6 Hz with varying intensity
        This is a simplified scoring algorithm
        
        For production, this could be enhanced with:
        - FFT analysis to detect 4-6 Hz frequency characteristic of Parkinson's
        - Machine learning models trained on labeled tremor data
        - Integration of accelerometer data for more robust detection
        
        Returns:
            float: Tremor score on a 0-10 scale
        """
        magnitude = self.magnitude if self.magnitude else self.calculate_magnitude()
        
        # Normalize magnitude to 0-10 scale
        # These thresholds should be calibrated based on real-world data collection
        # Typical tremor magnitudes range from 0 to ~5 rad/s
        score = min(magnitude * 2, 10.0)
        
        return round(score, 2)
    
    def to_dict(self) -> Dict:
        """Convert sensor reading object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'gyro_x': self.gyro_x,
            'gyro_y': self.gyro_y,
            'gyro_z': self.gyro_z,
            'accel_x': self.accel_x,
            'accel_y': self.accel_y,
            'accel_z': self.accel_z,
            'magnitude': self.magnitude,
            'tremor_score': self.tremor_score,
            'device_id': self.device_id
        }


# ============================================================================
# API ENDPOINTS - SESSION MANAGEMENT
# ============================================================================

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """
    Start a new tremor monitoring session
    
    Expected JSON body:
    {
        "notes": "Morning session after medication"  # Optional
    }
    
    Returns:
        JSON object containing created session details
    """
    try:
        data = request.get_json() or {}
        
        # Create new session
        session = TremorSession(
            notes=data.get('notes')
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': session.to_dict(),
            'message': 'Session started successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sessions/<int:session_id>/end', methods=['PUT'])
def end_session(session_id):
    """
    End a tremor monitoring session and calculate summary statistics
    
    This endpoint:
    1. Sets the session end time
    2. Calculates session duration
    3. Analyzes all readings to compute tremor statistics
    4. Calculates dominant tremor frequency (simplified version)
    
    Args:
        session_id: ID of the session to end
        
    Returns:
        JSON object containing updated session with calculated statistics
    """
    try:
        session = TremorSession.query.get(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        if session.session_end:
            return jsonify({
                'success': False,
                'error': 'Session already ended'
            }), 400
        
        # Set session end time
        session.session_end = datetime.utcnow()
        
        # Calculate duration in seconds
        duration = session.session_end - session.session_start
        session.duration_seconds = int(duration.total_seconds())
        
        # Calculate tremor statistics from sensor readings
        readings = SensorReading.query.filter_by(session_id=session_id).all()
        
        if readings:
            tremor_scores = [r.tremor_score for r in readings if r.tremor_score is not None]
            
            if tremor_scores:
                session.average_tremor_score = round(sum(tremor_scores) / len(tremor_scores), 2)
                session.max_tremor_score = round(max(tremor_scores), 2)
                session.min_tremor_score = round(min(tremor_scores), 2)
                
                # Calculate dominant tremor frequency
                # NOTE: This is a placeholder - in production, implement FFT analysis
                # to detect the 4-6 Hz frequency characteristic of Parkinson's tremor
                # Using SciKit Digital Health library as mentioned in the report
                session.tremor_frequency_hz = 5.0  # Placeholder
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': session.to_dict(),
            'message': 'Session ended successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """
    Get all tremor monitoring sessions
    
    Query parameters:
        limit: Maximum number of sessions to return (default: 10)
        include_active: Include active (non-ended) sessions (default: true)
        
    Returns:
        JSON list of sessions ordered by most recent first
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        include_active = request.args.get('include_active', 'true').lower() == 'true'
        
        # Build query
        query = TremorSession.query
        
        # Filter out active sessions if requested
        if not include_active:
            query = query.filter(TremorSession.session_end.isnot(None))
        
        # Execute query - most recent first
        sessions = query.order_by(TremorSession.session_start.desc())\
            .limit(limit)\
            .all()
        
        return jsonify({
            'success': True,
            'data': [session.to_dict() for session in sessions],
            'count': len(sessions)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get details for a specific session
    
    Args:
        session_id: Session database ID
        
    Returns:
        JSON object with session details
    """
    try:
        session = TremorSession.query.get(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': session.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sessions/active', methods=['GET'])
def get_active_session():
    """
    Get the currently active (non-ended) session if one exists
    
    This is useful for the smartwatch app to determine if it should
    continue recording to an existing session or start a new one
    
    Returns:
        JSON object with active session details, or null if no active session
    """
    try:
        active_session = TremorSession.query.filter(
            TremorSession.session_end.is_(None)
        ).order_by(TremorSession.session_start.desc()).first()
        
        if active_session:
            return jsonify({
                'success': True,
                'data': active_session.to_dict()
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No active session'
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ENDPOINTS - SENSOR DATA
# ============================================================================

@app.route('/api/sensor-data', methods=['POST'])
def add_sensor_data():
    """
    Add new sensor reading(s) from the wearable device
    
    Supports both single reading and batch upload for efficiency
    Batch upload is important for the smartwatch to buffer readings and send them
    together, reducing battery consumption from frequent network operations
    
    Expected JSON body (single reading):
    {
        "session_id": 1,  # Optional - can record without active session
        "gyro_x": 0.5,
        "gyro_y": -0.3,
        "gyro_z": 0.2,
        "accel_x": 9.8,   # Optional
        "accel_y": 0.1,   # Optional
        "accel_z": 0.0,   # Optional
        "device_id": "smartwatch_001"  # Optional
    }
    
    Expected JSON body (batch upload):
    {
        "session_id": 1,
        "readings": [
            {
                "gyro_x": 0.5, "gyro_y": -0.3, "gyro_z": 0.2,
                "accel_x": 9.8, "accel_y": 0.1, "accel_z": 0.0,
                "timestamp": "2024-01-01T12:00:00"
            },
            {
                "gyro_x": 0.6, "gyro_y": -0.2, "gyro_z": 0.1,
                "accel_x": 9.7, "accel_y": 0.2, "accel_z": 0.1,
                "timestamp": "2024-01-01T12:00:01"
            }
        ],
        "device_id": "smartwatch_001"
    }
    
    Returns:
        JSON confirmation of data storage
    """
    try:
        data = request.get_json()
        
        # Get session_id if provided (readings can exist without a session)
        session_id = data.get('session_id')
        
        # Verify session exists if provided
        if session_id:
            session = TremorSession.query.get(session_id)
            if not session:
                return jsonify({
                    'success': False,
                    'error': 'Session not found'
                }), 404
        
        created_readings = []
        
        # Check if this is a batch upload
        if 'readings' in data:
            # Batch upload - more efficient for smartwatch battery
            for reading_data in data['readings']:
                reading = create_sensor_reading(
                    session_id=session_id,
                    gyro_x=reading_data['gyro_x'],
                    gyro_y=reading_data['gyro_y'],
                    gyro_z=reading_data['gyro_z'],
                    accel_x=reading_data.get('accel_x'),
                    accel_y=reading_data.get('accel_y'),
                    accel_z=reading_data.get('accel_z'),
                    device_id=data.get('device_id'),
                    timestamp=reading_data.get('timestamp')
                )
                created_readings.append(reading)
        else:
            # Single reading
            if not all(k in data for k in ['gyro_x', 'gyro_y', 'gyro_z']):
                return jsonify({
                    'success': False,
                    'error': 'Missing required gyroscope fields: gyro_x, gyro_y, gyro_z'
                }), 400
            
            reading = create_sensor_reading(
                session_id=session_id,
                gyro_x=data['gyro_x'],
                gyro_y=data['gyro_y'],
                gyro_z=data['gyro_z'],
                accel_x=data.get('accel_x'),
                accel_y=data.get('accel_y'),
                accel_z=data.get('accel_z'),
                device_id=data.get('device_id')
            )
            created_readings.append(reading)
        
        # Bulk save to database for efficiency
        db.session.bulk_save_objects(created_readings)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(created_readings)} reading(s) stored successfully',
            'count': len(created_readings)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def create_sensor_reading(session_id, gyro_x, gyro_y, gyro_z, 
                         accel_x=None, accel_y=None, accel_z=None,
                         device_id=None, timestamp=None):
    """
    Helper function to create a sensor reading object
    
    Args:
        session_id: Session database ID (optional)
        gyro_x: X-axis gyroscope reading (rad/s)
        gyro_y: Y-axis gyroscope reading (rad/s)
        gyro_z: Z-axis gyroscope reading (rad/s)
        accel_x: X-axis accelerometer reading (m/s², optional)
        accel_y: Y-axis accelerometer reading (m/s², optional)
        accel_z: Z-axis accelerometer reading (m/s², optional)
        device_id: Device identifier (optional)
        timestamp: Reading timestamp (optional, defaults to now)
        
    Returns:
        SensorReading object
    """
    reading = SensorReading(
        session_id=session_id,
        gyro_x=gyro_x,
        gyro_y=gyro_y,
        gyro_z=gyro_z,
        accel_x=accel_x,
        accel_y=accel_y,
        accel_z=accel_z,
        device_id=device_id
    )
    
    # Set custom timestamp if provided
    if timestamp:
        reading.timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    # Calculate magnitude and tremor score
    reading.magnitude = reading.calculate_magnitude()
    reading.tremor_score = reading.calculate_tremor_score()
    
    return reading


@app.route('/api/sensor-data/recent', methods=['GET'])
def get_recent_sensor_data():
    """
    Get recent sensor readings for real-time visualization
    
    This endpoint is designed to support the React frontend with Chart.js
    for displaying real-time tremor data as mentioned in the report
    
    Query parameters:
        session_id: Filter by session (optional)
        limit: Number of readings to return (default: 100)
        seconds: Get readings from last N seconds (default: 60)
        
    Returns:
        JSON list of recent sensor readings in chronological order
    """
    try:
        # Get query parameters
        session_id = request.args.get('session_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        seconds = request.args.get('seconds', 60, type=int)
        
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(seconds=seconds)
        
        # Build query
        query = SensorReading.query.filter(
            SensorReading.timestamp >= time_threshold
        )
        
        # Add session filter if provided
        if session_id:
            query = query.filter(SensorReading.session_id == session_id)
        
        # Execute query
        readings = query.order_by(SensorReading.timestamp.desc())\
            .limit(limit)\
            .all()
        
        # Reverse to get chronological order for Chart.js
        readings.reverse()
        
        return jsonify({
            'success': True,
            'data': [reading.to_dict() for reading in readings],
            'count': len(readings)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sessions/<int:session_id>/data', methods=['GET'])
def get_session_data(session_id):
    """
    Get all sensor readings for a specific session
    
    This is useful for viewing historical session data and creating
    visualizations of past tremor patterns
    
    Args:
        session_id: Session database ID
        
    Returns:
        JSON list of all sensor readings in the session
    """
    try:
        # Verify session exists
        session = TremorSession.query.get(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Get all readings for this session
        readings = SensorReading.query.filter_by(session_id=session_id)\
            .order_by(SensorReading.timestamp.asc())\
            .all()
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'data': [reading.to_dict() for reading in readings],
            'count': len(readings)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ENDPOINTS - ANALYTICS & STATISTICS
# ============================================================================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get statistical summary for tremor tracking
    
    This provides an overview that helps answer the question:
    "When were tremors worst over the past week/month?"
    as mentioned in the project definition
    
    Query parameters:
        days: Number of days to include in statistics (default: 7)
        
    Returns:
        JSON object with statistical analysis
    """
    try:
        days = request.args.get('days', 7, type=int)
        
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Get sessions in time period
        sessions = TremorSession.query.filter(
            TremorSession.session_start >= time_threshold
        ).all()
        
        # Get readings in time period
        readings = SensorReading.query.filter(
            SensorReading.timestamp >= time_threshold
        ).all()
        
        # Calculate statistics
        statistics = {
            'time_period_days': days,
            'total_sessions': len(sessions),
            'total_readings': len(readings),
            'average_tremor_score': None,
            'max_tremor_score': None,
            'min_tremor_score': None,
            'daily_averages': [],  # Average tremor score per day
            'session_summaries': []
        }
        
        # Calculate overall tremor statistics
        if readings:
            tremor_scores = [r.tremor_score for r in readings if r.tremor_score is not None]
            if tremor_scores:
                statistics['average_tremor_score'] = round(sum(tremor_scores) / len(tremor_scores), 2)
                statistics['max_tremor_score'] = round(max(tremor_scores), 2)
                statistics['min_tremor_score'] = round(min(tremor_scores), 2)
        
        # Calculate daily averages for trend analysis
        # This helps visualize tremor patterns over time
        from collections import defaultdict
        daily_scores = defaultdict(list)
        
        for reading in readings:
            if reading.tremor_score is not None:
                date = reading.timestamp.date().isoformat()
                daily_scores[date].append(reading.tremor_score)
        
        for date, scores in sorted(daily_scores.items()):
            statistics['daily_averages'].append({
                'date': date,
                'average_score': round(sum(scores) / len(scores), 2),
                'max_score': round(max(scores), 2),
                'min_score': round(min(scores), 2),
                'reading_count': len(scores)
            })
        
        # Add session summaries
        for session in sessions:
            if session.session_end:
                statistics['session_summaries'].append({
                    'id': session.id,
                    'date': session.session_start.date().isoformat(),
                    'time': session.session_start.time().isoformat(),
                    'duration_minutes': round(session.duration_seconds / 60, 1) if session.duration_seconds else None,
                    'average_score': session.average_tremor_score,
                    'max_score': session.max_tremor_score,
                    'min_score': session.min_tremor_score,
                    'notes': session.notes
                })
        
        return jsonify({
            'success': True,
            'data': statistics
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API is running
    
    Returns:
        JSON status message with database stats
    """
    try:
        # Get some basic stats
        session_count = TremorSession.query.count()
        reading_count = SensorReading.query.count()
        
        return jsonify({
            'success': True,
            'message': 'Tremor Tracker API is running',
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'total_sessions': session_count,
                'total_readings': reading_count
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': True,
            'message': 'API is running but database not initialized',
            'timestamp': datetime.utcnow().isoformat()
        }), 200


@app.route('/api/simulate-data', methods=['POST'])
def simulate_tremor_data():
    """
    Generate simulated tremor data for testing
    
    As mentioned in the report, this supports prototyping with dummy data
    before real sensor data is available from the smartwatch
    
    Expected JSON body:
    {
        "session_id": 1,  # Optional
        "duration_seconds": 60,
        "frequency": 10  # Readings per second
    }
    
    Returns:
        JSON confirmation with number of readings generated
    """
    try:
        import random
        
        data = request.get_json()
        session_id = data.get('session_id')
        duration = data.get('duration_seconds', 60)
        frequency = data.get('frequency', 10)
        
        # Verify session exists if provided
        if session_id:
            session = TremorSession.query.get(session_id)
            if not session:
                return jsonify({
                    'success': False,
                    'error': 'Session not found'
                }), 404
        
        # Generate simulated readings
        readings = []
        total_readings = duration * frequency
        start_time = datetime.utcnow() - timedelta(seconds=duration)
        
        for i in range(total_readings):
            # Simulate tremor with 4-6 Hz oscillation (typical Parkinson's tremor)
            t = i / frequency
            tremor_freq = 5.0 + random.uniform(-0.5, 0.5)  # 4.5-5.5 Hz
            base_tremor = 0.4 * math.sin(2 * math.pi * tremor_freq * t)
            
            # Add random variation and noise
            variation = random.uniform(0.8, 1.2)
            gyro_x = base_tremor * variation + random.uniform(-0.1, 0.1)
            gyro_y = base_tremor * 0.7 * variation + random.uniform(-0.1, 0.1)
            gyro_z = base_tremor * 0.5 * variation + random.uniform(-0.05, 0.05)
            
            # Simulate gravity + small movements for accelerometer
            accel_x = 9.8 + random.uniform(-0.5, 0.5)
            accel_y = random.uniform(-0.3, 0.3)
            accel_z = random.uniform(-0.2, 0.2)
            
            timestamp = start_time + timedelta(seconds=i/frequency)
            
            reading = create_sensor_reading(
                session_id=session_id,
                gyro_x=gyro_x,
                gyro_y=gyro_y,
                gyro_z=gyro_z,
                accel_x=accel_x,
                accel_y=accel_y,
                accel_z=accel_z,
                device_id='simulator',
                timestamp=timestamp.isoformat()
            )
            readings.append(reading)
        
        # Save to database
        db.session.bulk_save_objects(readings)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(readings)} simulated readings',
            'count': len(readings)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """
    Initialize the database by creating all tables
    """
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Initialize database on first run
    init_db()
    
    # Run Flask development server
    # In production, use a proper WSGI server like Gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)
