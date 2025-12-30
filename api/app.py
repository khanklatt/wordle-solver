"""
Flask API for Wordle Solver Web UI

Requirement 6.1: Provide web-based UI accessible via browser
Requirement 7.1: Containerized using Docker
Requirement 7.2: Respond to API requests within 500ms
"""
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add parent directory to path to import wordle_solver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wordle_solver import WordleSolver

# Get project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
web_folder = os.path.join(project_root, 'web')

app = Flask(__name__, static_folder=web_folder, static_url_path='')
CORS(app)  # Enable CORS for development

def create_solver():
    """Create a new solver instance (stateless API)"""
    return WordleSolver(
        frequency_dir=os.path.join(project_root, 'lib'),
        words_file=os.path.join(project_root, 'lib', 'wordle-words.txt')
    )


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory(web_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS)"""
    return send_from_directory(web_folder, path)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.route('/api/process', methods=['POST'])
def process_guess():
    """
    Process constraints and return candidates and suggestions (stateless API)
    
    Requirement 6.4: Allow users to type 5-letter words and submit
    Requirement 6.10: Allow words not in wordlist (wordlist only for suggestions)
    
    Request body:
    {
        "greenConstraints": {"1": "S", "3": "I"},  // position -> letter
        "yellowConstraints": {"A": [2], "R": [1]},  // letter -> excluded positions
        "greyConstraints": ["A", "N", "T"]  // excluded letters
    }
    
    Response:
    {
        "candidates": ["word1", "word2", ...],
        "suggestions": [{"word": "WORD", "score": 10}, ...],
        "solved": false
    }
    """
    try:
        # Get JSON data - handle parsing errors gracefully
        data = request.get_json(force=True)  # force=True to parse even if Content-Type is wrong
        
        if data is None:
            return jsonify({
                'error': 'Invalid or missing JSON data'
            }), 400
        
        # Check if old format is being sent (backward compatibility check)
        if 'guess' in data:
            return jsonify({
                'error': 'Old API format detected. Please use new stateless format: {greenConstraints, yellowConstraints, greyConstraints}'
            }), 400
        
        # Parse constraints from request - normalize everything, never reject
        # Stateless design: accept any format and normalize it
        green_constraints_raw = data.get('greenConstraints')
        yellow_constraints_raw = data.get('yellowConstraints')
        grey_constraints_raw = data.get('greyConstraints')
        
        # Normalize to expected types (never reject, always normalize)
        if green_constraints_raw is None or not isinstance(green_constraints_raw, dict):
            green_constraints_raw = {}
        if yellow_constraints_raw is None or not isinstance(yellow_constraints_raw, dict):
            yellow_constraints_raw = {}
        if grey_constraints_raw is None or not isinstance(grey_constraints_raw, list):
            grey_constraints_raw = []
        
        # Convert green constraints: {"1": "S", "3": "I"} -> {1: "S", 3: "I"}
        # Be robust: handle None, invalid types, etc.
        green_constraints = {}
        if isinstance(green_constraints_raw, dict):
            for pos_str, letter in green_constraints_raw.items():
                try:
                    pos = int(pos_str)
                    if 1 <= pos <= 5:
                        if isinstance(letter, str) and len(letter) == 1 and letter.isalpha():
                            green_constraints[pos] = letter.upper()
                except (ValueError, TypeError, AttributeError):
                    continue
        
        # Convert yellow constraints: {"A": [2], "R": [1]} -> {"A": {2}, "R": {1}}
        # Be robust: handle None, invalid types, etc.
        yellow_constraints = {}
        if isinstance(yellow_constraints_raw, dict):
            for letter, positions in yellow_constraints_raw.items():
                try:
                    if not isinstance(letter, str) or len(letter) != 1 or not letter.isalpha():
                        continue
                    letter_upper = letter.upper()
                    pos_set = set()
                    if isinstance(positions, (list, tuple)):
                        for pos in positions:
                            if isinstance(pos, int) and 1 <= pos <= 5:
                                pos_set.add(pos)
                    if pos_set:
                        yellow_constraints[letter_upper] = pos_set
                except (TypeError, ValueError, AttributeError):
                    continue
        
        # Convert grey constraints: ["A", "N", "T"] -> {"A", "N", "T"}
        # Be robust: handle numbers, invalid types, etc. - just skip invalid entries
        grey_constraints = set()
        if isinstance(grey_constraints_raw, list):
            for item in grey_constraints_raw:
                # Only process if it's a valid letter string
                if isinstance(item, str) and len(item) == 1 and item.isalpha():
                    grey_constraints.add(item.upper())
                # Silently skip numbers, None, empty strings, etc.
        
        # Create fresh solver instance and apply constraints
        solver = create_solver()
        result = solver.apply_constraints(green_constraints, yellow_constraints, grey_constraints)
        
        # Check if solved (all 5 positions are green)
        solved = len(green_constraints) == 5
        
        return jsonify({
            'candidates': result['candidates'],
            'suggestions': result['suggestions'],
            'solved': solved
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except AttributeError as e:
        return jsonify({
            'error': f'API configuration error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    """
    Reset endpoint (no-op for stateless API, but kept for compatibility)
    
    Requirement 6.11: Provide reset/new game functionality
    """
    # Stateless API - no state to reset on server
    return jsonify({'status': 'reset'})


@app.route('/api/default-guess', methods=['GET'])
def default_guess():
    """Get the default first guess suggestion"""
    solver = create_solver()
    return jsonify({'guess': solver.get_default_first_guess()})


if __name__ == '__main__':
    # Run in development mode
    app.run(host='0.0.0.0', port=5000, debug=True)

