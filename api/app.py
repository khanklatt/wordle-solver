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

# Get project root for creating solver instances
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
            # request.get_json() returns None if JSON is invalid or missing
            # Try to get raw data for debugging
            raw_data = request.data.decode('utf-8') if request.data else ''
            return jsonify({
                'error': 'Invalid or missing JSON data',
                'received_content_type': request.content_type,
                'raw_data_preview': raw_data[:200] if raw_data else 'empty'
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
        
        # Debug logging (can be removed in production)
        import logging
        logging.debug(f"Parsed constraints - Green: {green_constraints}, Yellow: {yellow_constraints}, Grey: {sorted(grey_constraints)}")
        
        # Create fresh solver instance and apply constraints
        solver = create_solver()
        try:
            # Ensure we're using apply_constraints, not process_feedback
            # apply_constraints takes: (green_constraints, yellow_constraints, grey_constraints)
            # It does NOT take a guess parameter
            if not hasattr(solver, 'apply_constraints'):
                raise AttributeError("WordleSolver does not have apply_constraints method. This is a code error.")
            result = solver.apply_constraints(green_constraints, yellow_constraints, grey_constraints)
        except ValueError as e:
            # ValueError from apply_constraints - check if it's the "guess" error
            error_str = str(e)
            if 'guess' in error_str.lower() and 'exactly' in error_str.lower():
                # This should never happen with apply_constraints
                raise ValueError(
                    f"Internal error: apply_constraints should not validate 'guess'. "
                    f"This suggests process_feedback was called instead. Original: {error_str}"
                )
            # Re-raise other ValueErrors as-is
            raise
        except Exception as e:
            # Log the actual exception for debugging
            import traceback
            error_trace = traceback.format_exc()
            error_str = str(e)
            # Check if this error mentions "guess" - might indicate cached code or wrong method
            if 'guess' in error_str.lower() and 'exactly' in error_str.lower():
                # This error should not exist - likely from cached bytecode
                import sys
                import os
                raise ValueError(
                    f"CACHED CODE DETECTED: Error 'Guess must be exactly 5 letters' no longer exists. "
                    f"Restart server to clear .pyc cache. Original: {error_str}"
                )
            if 'guess' in error_str.lower():
                raise ValueError(
                    f"Internal error: apply_constraints should not validate 'guess'. "
                    f"This suggests process_feedback was called instead. Original: {error_str}"
                )
            raise
        
        # Check if solved (all 5 positions are green)
        solved = len(green_constraints) == 5
        
        return jsonify({
            'candidates': result['candidates'],
            'suggestions': result['suggestions'],
            'solved': solved
        })
    
    except ValueError as e:
        # Check if error message mentions "guess" - might be from old cached code
        error_msg = str(e)
        if 'guess' in error_msg.lower() and 'exactly' in error_msg.lower():
            # This error should not exist in current code - likely from cached bytecode
            import sys
            import os
            return jsonify({
                'error': 'CACHED CODE DETECTED: The error "Guess must be exactly 5 letters" no longer exists in the codebase. Please restart the server to clear cached Python bytecode (.pyc files).',
                'original_error': error_msg,
                'python_version': sys.version,
                'code_location': __file__,
                'file_mtime': os.path.getmtime(__file__) if os.path.exists(__file__) else 'unknown'
            }), 400
        return jsonify({'error': error_msg}), 400
    except AttributeError as e:
        # Handle missing method errors
        error_msg = str(e)
        return jsonify({
            'error': f'API configuration error: {error_msg}. Please check server logs.',
            'detail': 'This indicates a code error - apply_constraints method may be missing.'
        }), 500
    except Exception as e:
        # Log the full exception for debugging
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        # Check if this is the guess validation error (should not exist)
        if 'guess' in error_msg.lower() and 'exactly' in error_msg.lower():
            return jsonify({
                'error': 'CACHED CODE DETECTED: The error "Guess must be exactly 5 letters" no longer exists. Please rebuild Docker container: docker-compose down && docker-compose build --no-cache && docker-compose up',
                'original_error': error_msg,
                'fix': 'Run: docker-compose down && docker-compose build --no-cache && docker-compose up',
                'trace': error_trace
            }), 500
        return jsonify({
            'error': f'Internal server error: {error_msg}',
            'trace': error_trace  # Include trace in development
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

