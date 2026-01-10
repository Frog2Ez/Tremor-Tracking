"""
Parkinson's Tremor Monitoring Prototype
Simulates smartwatch sensor data and sends to backend API
"""

import time
import random
import math
import json
import requests
from datetime import datetime
from typing import Dict, List

class SmartWatchSimulator:
    """Simulates accelerometer and gyroscope data from a smartwatch"""
    
    def __init__(self, sample_rate_hz: int = 50):
        """
        Initialize the smartwatch simulator
        
        Args:
            sample_rate_hz: Number of samples per second (typical smartwatches: 50-100 Hz)
        """
        self.sample_rate = sample_rate_hz
        self.time_step = 1.0 / sample_rate_hz
        
        # Tremor characteristics based on research
        # Resting tremor: 4-6 Hz (Type I, II)
        # Action tremor: 5-7.5 Hz (Type III, IV)
        self.tremor_freq = random.uniform(4.5, 6.0)  # Hz
        self.tremor_amplitude = random.uniform(0.5, 2.0)  # m/s²
        
    def generate_sensor_reading(self, t: float, tremor_active: bool = True) -> Dict:
        """
        Generate a single sensor reading
        
        Args:
            t: Time in seconds
            tremor_active: Whether tremor is present
            
        Returns:
            Dictionary with accelerometer and gyroscope data
        """
        # Base gravity and noise
        gravity_x = 0.0 + random.gauss(0, 0.05)
        gravity_y = 9.81 + random.gauss(0, 0.05)
        gravity_z = 0.0 + random.gauss(0, 0.05)
        
        if tremor_active:
            # Add tremor oscillation (sinusoidal pattern)
            tremor_x = self.tremor_amplitude * math.sin(2 * math.pi * self.tremor_freq * t)
            tremor_y = self.tremor_amplitude * math.cos(2 * math.pi * self.tremor_freq * t) * 0.7
            tremor_z = self.tremor_amplitude * math.sin(2 * math.pi * self.tremor_freq * t + math.pi/4) * 0.5
        else:
            # Minimal tremor when not active
            tremor_x = random.gauss(0, 0.1)
            tremor_y = random.gauss(0, 0.1)
            tremor_z = random.gauss(0, 0.1)
        
        # Combine gravity + tremor + noise
        accel_x = gravity_x + tremor_x
        accel_y = gravity_y + tremor_y
        accel_z = gravity_z + tremor_z
        
        # Gyroscope data (rotation rate in rad/s)
        # Tremor causes rotational movement too
        if tremor_active:
            gyro_x = 0.3 * math.cos(2 * math.pi * self.tremor_freq * t) + random.gauss(0, 0.05)
            gyro_y = 0.2 * math.sin(2 * math.pi * self.tremor_freq * t) + random.gauss(0, 0.05)
            gyro_z = 0.15 * math.sin(2 * math.pi * self.tremor_freq * t + math.pi/3) + random.gauss(0, 0.05)
        else:
            gyro_x = random.gauss(0, 0.02)
            gyro_y = random.gauss(0, 0.02)
            gyro_z = random.gauss(0, 0.02)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'accelerometer': {
                'x': round(accel_x, 4),
                'y': round(accel_y, 4),
                'z': round(accel_z, 4)
            },
            'gyroscope': {
                'x': round(gyro_x, 4),
                'y': round(gyro_y, 4),
                'z': round(gyro_z, 4)
            }
        }
    
    def generate_batch(self, duration_seconds: float, tremor_pattern: str = "constant") -> List[Dict]:
        """
        Generate a batch of sensor readings
        
        Args:
            duration_seconds: How long to simulate
            tremor_pattern: "constant", "intermittent", or "varying"
            
        Returns:
            List of sensor readings
        """
        readings = []
        num_samples = int(duration_seconds * self.sample_rate)
        
        for i in range(num_samples):
            t = i * self.time_step
            
            # Determine if tremor is active based on pattern
            if tremor_pattern == "constant":
                tremor_active = True
            elif tremor_pattern == "intermittent":
                # Tremor on for 5 seconds, off for 3 seconds
                tremor_active = (t % 8.0) < 5.0
            else:  # varying
                # Gradually varying tremor intensity
                self.tremor_amplitude = 0.5 + 1.5 * abs(math.sin(t / 10.0))
                tremor_active = True
            
            reading = self.generate_sensor_reading(t, tremor_active)
            readings.append(reading)
        
        return readings


class BackendAPI:
    """Handles communication with the Flask backend"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
    
    def send_sensor_data(self, readings: List[Dict], patient_id: str = "test_patient_001") -> bool:
        """
        Send sensor data to backend API
        
        Args:
            readings: List of sensor readings
            patient_id: Identifier for the patient
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            'patient_id': patient_id,
            'device_id': 'smartwatch_sim_001',
            'readings': readings,
            'metadata': {
                'sample_rate_hz': 50,
                'sensor_type': 'simulated',
                'tremor_freq_hz': getattr(self, 'tremor_freq', 5.0)
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/sensor-data",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✓ Successfully sent {len(readings)} readings to backend")
                return True
            else:
                print(f"✗ Failed to send data. Status: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to backend. Is the server running?")
            print(f"  Attempted to connect to: {self.base_url}")
            return False
        except Exception as e:
            print(f"✗ Error sending data: {e}")
            return False
    
    def save_to_file(self, readings: List[Dict], filename: str = "tremor_data.json"):
        """
        Save readings to a JSON file (fallback if backend unavailable)
        
        Args:
            readings: List of sensor readings
            filename: Output filename
        """
        data = {
            'patient_id': 'test_patient_001',
            'device_id': 'smartwatch_sim_001',
            'readings': readings,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Saved {len(readings)} readings to {filename}")


def main():
    """Main demonstration function"""
    print("=" * 60)
    print("Parkinson's Tremor Monitoring - Smartwatch Simulator")
    print("=" * 60)
    print()
    
    # Initialize simulator
    watch = SmartWatchSimulator(sample_rate_hz=50)
    api = BackendAPI()
    
    # Simulate different tremor patterns
    patterns = ["constant", "intermittent", "varying"]
    
    for pattern in patterns:
        print(f"\n--- Simulating {pattern.upper()} tremor pattern ---")
        print(f"Duration: 10 seconds | Sample rate: 50 Hz")
        
        # Generate sensor data
        readings = watch.generate_batch(duration_seconds=10, tremor_pattern=pattern)
        print(f"Generated {len(readings)} sensor readings")
        
        # Show sample of first 3 readings
        print("\nSample readings:")
        for i, reading in enumerate(readings[:3]):
            print(f"  Reading {i+1}:")
            print(f"    Accel: ({reading['accelerometer']['x']}, "
                  f"{reading['accelerometer']['y']}, {reading['accelerometer']['z']}) m/s²")
            print(f"    Gyro:  ({reading['gyroscope']['x']}, "
                  f"{reading['gyroscope']['y']}, {reading['gyroscope']['z']}) rad/s")
        
        # Try to send to backend API
        success = api.send_sensor_data(readings)
        
        # If backend unavailable, save to file
        if not success:
            filename = f"tremor_data_{pattern}.json"
            api.save_to_file(readings, filename)
        
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("Simulation complete!")
    print("\nNext steps:")
    print("1. Start the Flask backend server")
    print("2. Re-run this script to send data to the API")
    print("3. View the data in the web interface")
    print("=" * 60)


if __name__ == "__main__":
    main()