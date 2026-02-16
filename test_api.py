#!/usr/bin/env python3
"""
Interactive Test Script for Tremor Tracker API

This script tests all the main API endpoints and helps you diagnose issues.

Usage:
    python test_api.py
"""

import requests
import json
from datetime import datetime

# Configuration
API_URL = 'http://localhost:5000/api'

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_test(test_name, success, details=""):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"  {details}")

def pretty_print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

def test_connection():
    """Test 1: Check if API is reachable"""
    print_header("Test 1: API Connection")
    
    try:
        response = requests.get(f'{API_URL}/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_test("API is reachable", True)
            print("\nAPI Response:")
            pretty_print_json(data)
            return True
        else:
            print_test("API is reachable", False, 
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_test("API is reachable", False, 
                  "Cannot connect to server. Is Flask running?")
        print("\nTo start Flask:")
        print("  python app.py")
        return False
    except Exception as e:
        print_test("API is reachable", False, str(e))
        return False


def test_create_session():
    """Test 2: Create a new monitoring session"""
    print_header("Test 2: Create Monitoring Session")
    
    try:
        # Create session without notes
        response = requests.post(
            f'{API_URL}/sessions',
            json={},
            timeout=5
        )
        
        if response.status_code == 201:
            data = response.json()
            print_test("Create session (no notes)", True)
            print("\nSession created:")
            pretty_print_json(data)
            session_id = data['data']['id']
            
            # Create session with notes
            response = requests.post(
                f'{API_URL}/sessions',
                json={'notes': 'Test session with notes'},
                timeout=5
            )
            
            if response.status_code == 201:
                data = response.json()
                print_test("Create session (with notes)", True)
                print("\nSession created:")
                pretty_print_json(data)
                return session_id
            else:
                print_test("Create session (with notes)", False,
                          f"HTTP {response.status_code}: {response.text}")
                return session_id
        else:
            print_test("Create session", False,
                      f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print_test("Create session", False, str(e))
        return None


def test_get_sessions():
    """Test 3: Retrieve sessions"""
    print_header("Test 3: Retrieve Sessions")
    
    try:
        response = requests.get(f'{API_URL}/sessions', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_test("Get all sessions", True, 
                      f"Found {data['count']} session(s)")
            print("\nSessions:")
            pretty_print_json(data)
            return True
        else:
            print_test("Get all sessions", False,
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test("Get all sessions", False, str(e))
        return False


def test_get_active_session():
    """Test 4: Get active session"""
    print_header("Test 4: Get Active Session")
    
    try:
        response = requests.get(f'{API_URL}/sessions/active', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                print_test("Get active session", True,
                          f"Active session ID: {data['data']['id']}")
            else:
                print_test("Get active session", True,
                          "No active session (all sessions ended)")
            print("\nActive session:")
            pretty_print_json(data)
            return True
        else:
            print_test("Get active session", False,
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test("Get active session", False, str(e))
        return False


def test_add_sensor_data(session_id):
    """Test 5: Add sensor data"""
    print_header("Test 5: Add Sensor Data")
    
    if not session_id:
        print_test("Add sensor data", False, "No session ID available")
        return False
    
    try:
        # Add single reading
        sensor_data = {
            'session_id': session_id,
            'gyro_x': 0.5,
            'gyro_y': -0.3,
            'gyro_z': 0.2,
            'accel_x': 9.8,
            'accel_y': 0.1,
            'accel_z': 0.0
        }
        
        response = requests.post(
            f'{API_URL}/sensor-data',
            json=sensor_data,
            timeout=5
        )
        
        if response.status_code == 201:
            data = response.json()
            print_test("Add single sensor reading", True)
            print("\nResponse:")
            pretty_print_json(data)
            return True
        else:
            print_test("Add sensor data", False,
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test("Add sensor data", False, str(e))
        return False


def test_get_recent_data():
    """Test 6: Get recent sensor data"""
    print_header("Test 6: Get Recent Sensor Data")
    
    try:
        response = requests.get(
            f'{API_URL}/sensor-data/recent?limit=10&seconds=300',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test("Get recent sensor data", True,
                      f"Found {data['count']} reading(s)")
            print("\nRecent data:")
            pretty_print_json(data)
            return True
        else:
            print_test("Get recent sensor data", False,
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test("Get recent sensor data", False, str(e))
        return False


def test_simulate_data(session_id):
    """Test 7: Generate simulated tremor data"""
    print_header("Test 7: Generate Simulated Data")
    
    if not session_id:
        print_test("Simulate data", False, "No session ID available")
        return False
    
    try:
        sim_data = {
            'session_id': session_id,
            'duration_seconds': 10,  # Short duration for testing
            'frequency': 5
        }
        
        response = requests.post(
            f'{API_URL}/simulate-data',
            json=sim_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print_test("Generate simulated data", True,
                      f"Generated {data['count']} readings")
            print("\nResponse:")
            pretty_print_json(data)
            return True
        else:
            print_test("Simulate data", False,
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test("Simulate data", False, str(e))
        return False


def test_end_session(session_id):
    """Test 8: End a monitoring session"""
    print_header("Test 8: End Monitoring Session")
    
    if not session_id:
        print_test("End session", False, "No session ID available")
        return False
    
    try:
        response = requests.put(
            f'{API_URL}/sessions/{session_id}/end',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test("End session", True)
            print("\nSession ended:")
            pretty_print_json(data)
            print("\nSession Statistics:")
            session_data = data['data']
            print(f"  Duration: {session_data['duration_seconds']} seconds")
            print(f"  Avg Tremor Score: {session_data['average_tremor_score']}")
            print(f"  Max Tremor Score: {session_data['max_tremor_score']}")
            print(f"  Min Tremor Score: {session_data['min_tremor_score']}")
            return True
        else:
            print_test("End session", False,
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test("End session", False, str(e))
        return False


def test_statistics():
    """Test 9: Get tremor statistics"""
    print_header("Test 9: Get Tremor Statistics")
    
    try:
        response = requests.get(
            f'{API_URL}/statistics?days=7',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test("Get statistics", True)
            print("\nStatistics:")
            pretty_print_json(data)
            return True
        else:
            print_test("Get statistics", False,
                      f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test("Get statistics", False, str(e))
        return False


def main():
    """Run all tests"""
    print_header("TREMOR TRACKER API TEST SUITE")
    print(f"Testing API at: {API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Connection
    if not test_connection():
        print("\n⚠️  Cannot connect to API. Please start Flask:")
        print("     python app.py")
        return
    
    # Test 2: Create session
    session_id = test_create_session()
    
    # Test 3: Get sessions
    test_get_sessions()
    
    # Test 4: Get active session
    test_get_active_session()
    
    # Test 5: Add sensor data
    test_add_sensor_data(session_id)
    
    # Test 6: Get recent data
    test_get_recent_data()
    
    # Test 7: Simulate data
    test_simulate_data(session_id)
    
    # Test 8: End session
    test_end_session(session_id)
    
    # Test 9: Get statistics
    test_statistics()
    
    # Final summary
    print_header("TEST SUITE COMPLETE")
    print("\n✓ All tests completed!")
    print("\nNext steps:")
    print("  1. Review the test results above")
    print("  2. Check TROUBLESHOOTING.md for any issues")
    print("  3. Try the API with your own requests")
    print("\nHappy coding! 🚀")


if __name__ == '__main__':
    main()
