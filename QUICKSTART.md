# Quick Start Guide - Tremor Tracker Backend

Get up and running in 2 minutes!

## Step 1: Install Dependencies

```bash
# Make sure you have Python 3.8+ installed
python --version

# Install required packages
pip install -r requirements.txt
```

## Step 2: Start the Server

```bash
# Start the Flask development server
# Database is created automatically on first run!
python app.py
```

The API will be running at `http://localhost:5000`

**That's it!** The database (`tremor_tracker.db`) is created automatically.

## Optional: Add Sample Data for Testing

```bash
# Generate sample sessions with realistic tremor data
python db_manager.py seed

# View database statistics
python db_manager.py stats
```

## Step 3: Test the API

Open a new terminal and try these commands:

```bash
# Check if API is running
curl http://localhost:5000/api/health

# Create a monitoring session
curl -X POST http://localhost:5000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"notes": "Test session"}'

# Generate 60 seconds of simulated tremor data
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

# Get statistics
curl "http://localhost:5000/api/statistics?days=7"
```

## Next Steps

### For Development:
1. Read the full [README.md](README.md) for detailed API documentation
2. Check [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for database structure
3. See [WEAROS_INTEGRATION.md](WEAROS_INTEGRATION.md) for smartwatch integration

### For Integration with React Frontend:
1. Make sure CORS is enabled (it is by default)
2. Use API endpoint: `http://localhost:5000/api`
3. See README.md for example JavaScript code

### For WearOS Smartwatch Integration:
1. See WEAROS_INTEGRATION.md for complete guide
2. Use WearOSSensors library for the watch app
3. Create NativeScript phone relay app

## Common Commands

```bash
# View database statistics
python db_manager.py stats

# Generate sample data for testing
python db_manager.py seed

# Export data to JSON
python db_manager.py export

# Start the server
python app.py
```

## Common Commands

```bash
# View database statistics
python db_manager.py stats

# Reset database (WARNING: deletes all data!)
python db_manager.py reset

# Export data to JSON
python db_manager.py export

# Run tests
pytest test_app.py

# Run tests with coverage
pytest --cov=app test_app.py
```

## Troubleshooting

### Port already in use?
Change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### Database locked error?
Stop all running Flask instances and try again.

### Import errors?
Make sure you're in the correct directory and virtual environment is activated.

## Quick API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/patients` | GET | List all patients |
| `/api/patients` | POST | Create patient |
| `/api/sessions` | POST | Start session |
| `/api/sessions/<id>/end` | PUT | End session |
| `/api/sensor-data` | POST | Add sensor data |
| `/api/sensor-data/recent` | GET | Get recent data |

For complete API documentation, see [README.md](README.md).

## Support

- View database schema: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- Full documentation: [README.md](README.md)
- Run tests to verify everything works: `pytest test_app.py`