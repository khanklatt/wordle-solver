# Web UI Setup Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OR Python 3.11+ with pip

### Option 1: Docker (Recommended)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Access at http://localhost:5000
```

### Option 2: Manual Setup

```bash
# Install Python dependencies
cd api
pip install -r requirements.txt

# Run Flask server
python app.py

# Access at http://localhost:5000
```

## Project Structure

```
wordle-solver/
├── api/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── test_api.py         # API tests
├── web/
│   ├── index.html          # Main HTML page
│   ├── css/
│   │   └── style.css       # Styling
│   └── js/
│       ├── app.js          # Main application logic
│       ├── game-board.js   # Game board component
│       ├── suggestions.js  # Suggestions sidebar
│       └── api.js          # API client
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker Compose configuration
└── .dockerignore           # Docker ignore patterns
```

## API Endpoints

- `GET /` - Serve web UI
- `GET /api/health` - Health check
- `GET /api/default-guess` - Get default first guess (SAINT)
- `POST /api/process` - Process guess and get suggestions
- `POST /api/reset` - Reset solver state

## Testing

```bash
# Run API tests (requires Flask installed)
python3 -m unittest api.test_api -v

# Run original solver tests
python3 -m unittest test_wordle_solver -v
```

## Deployment

The project includes CI/CD configuration in `.gitea/workflows/deploy.yaml` that:
1. Builds Docker image on push to main
2. Deploys using Docker Compose
3. Container name: `wordle-solver`

## Troubleshooting

### Port 5000 already in use
Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### Static files not loading
Ensure the `web/` directory is properly copied in the Dockerfile and accessible.

### API errors
Check that `lib/` directory contains required files:
- `pos1.txt` through `pos5.txt`
- `wordle-words.txt`

