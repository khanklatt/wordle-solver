# Project Requirements Document

## Project Objective
Provide an interactive Wordle solver that guides users through solving Wordle puzzles by allowing them to input guesses, report Wordle feedback (green/yellow/grey letters), and receive filtered candidate words and next guess suggestions based on positional letter frequency analysis. Wordle provides context of correct guesses (the right letter, in the right spot) with Green squares, valid but incorrect guesses (the right letter, but in the wrong position) with Yellow squares, and invalid guesses (a letter that is not in the word at all) with Grey squares.

This document assumes the reader is familiar with the rules and concepts from the popular 5-letter game Wordle.

## Requirements (Technical PM Role)

### Functional Requirements

#### 1. Data Loading and Initialization
- 1.1: APPROVED, MVP - System shall load positional letter frequency files from /tmp/pos1.txt through /tmp/pos5.txt
- 1.2: APPROVED, MVP - System shall extract top-N letters per position from frequency files
- 1.3: APPROVED, MVP - System shall load valid Wordle words from /tmp/wordle-words.txt
- 1.4: APPROVED, MVP - System shall initialize with default first guess suggestion of "SAINT"

#### 2. User Input Processing
- 2.1: APPROVED, MVP - System shall prompt the user for what guess the user opens with (case insensitive)
- 2.2: APPROVED, MVP - System shall prompt the user for "green" letters feedback from Wordle as string with dots for unknown positions (e.g., "S..NT" if we guessed SAINT and the word was SLANT)
- 2.3: APPROVED, MVP - System shall convert green letters string into position-to-letter mapping dictionary
- 2.4: APPROVED, MVP - System shall prompt the user for yellow letters input as string with dots for positional communication. (e.g. a guess of SAINT when the word was SLANT would result in the user entering .A..., because the A of SAINT in the second position is present in SLANT, but in the 3rd letter's slot)
- 2.5: APPROVED, MVP - System shall convert yellow letters into letter-to-excluded-positions mapping dictionary (letter A is known not to be in the 3rd position but present elsewhere)
- 2.6: APPROVED, MVP - System shall accept grey letters input as space-separated letters
- 2.7: APPROVED, MVP - System shall convert grey letters into set of excluded letters. These will not appear anywhere in any word.

#### 3. Guess Word Filter Generation
- 3.1: APPROVED, MVP - System shall use several strategies to filter candidate words:
- 3.1.1: APPROVED, MVP - Green letters: Fixed positions specified by green letters shall be applied via regex
- 3.1.2: APPROVED, MVP - Yellow letters: These letters will be included in the regex query for any letter position where we do not have a GREEN response, but no longer in a position where we've gotten a YELLOW indicator.
- 3.1.3: APPROVED, MVP - Grey letters: Exclude words containing grey letters
- 3.2: DEPRECATED, MVP - System shall return candidate sets split into two sections. The first section will contain only suggestions that have unique letters in them. The second section will offer words from candidate set with repeated letters.
- 3.3: APPROVED, MVP - System shall iteratively expand top-N letter set incrementally when candidate set becomes empty after filtering. Consider the example as follows:
    Suppose we know the first four letters of the word are PLAN. System should generate guesses for the fifth letter from /tmp/pos5.txt in sequence order: the file presently contains e, y, a, t, and r..
    If the letter e was excluded as a grey letter from a previous guess, then the system will check for plany, plana, until it reaches plant as a valid word in the list for the suggestion of the guess.
- 3.4: APPROVED, MVP - System shall make a suggestion once it has calculated the set of candidate words that prioritizes those words that have the most vowels. For example if the current set of suggested words is "BRISK CHIPS CLIPS GUISE MOISE POISE PRISM", GUISE and POISE should be offered as suggested words because they contain the most vowels among that set.
3.5: APPROVED, MVP - System shall compute a "word score" for all of the suggested words. The lower the score, the better. For each letter in the puzzle that remains unknown, check each of the recommended words from 3.4 against the position of the unknown letters and give it the score of the line number it is found. For example, if we are down to one unknown letter in the puzzle where the two possibilities are POISE and NOISE, the word NOISE would have a score of 6 whereas POISE would have the score of 16 because pos1.txt contains a p in the 6th line (6th most likely letter to be found in the first letter of a word) instead of NOISE which is 16th in that file. Note that the score should be the sum of all of the unknown letters, and the lowest scores are the ones suggested next.
3.5.1: APPROVED - Word scores will be shown next to all words that were scored, and all scored words will be shown in the suggested next guess.

#### 4. Interactive CLI Interface
- 4.1: APPROVED, MVP - System shall prompt user for first guess with default suggestion "SAINT"
- 4.2: APPROVED, MVP - System shall prompt user for green letters feedback after each guess
- 4.3: APPROVED, MVP - System shall prompt user for yellow letters feedback after green letters input
- 4.4: APPROVED, MVP - System shall prompt user for grey letters feedback after yellow letters input
- 4.5: APPROVED, MVP - System shall display filtered candidate words after each constraint application
- 4.6: APPROVED, MVP - System shall display suggested next guess after all constraints are applied
- 4.7: APPROVED, MVP - System shall continue interactive loop until puzzle is solved or user exits

#### 6. Web-Based User Interface
- 6.1: APPROVED, MVP - System shall provide web-based UI accessible via browser
- 6.2: APPROVED, MVP - System shall display 5x6 grid of letter squares matching NYT interface
- 6.3: APPROVED, MVP - System shall accept input via system keyboard (mobile/desktop)
- 6.4: APPROVED, MVP - System shall allow users to type 5-letter words and submit via Enter key
- 6.5: APPROVED, MVP - System shall display submitted words in blue squares
- 6.6: APPROVED, MVP - System shall allow users to cycle letter states: blue → yellow → green → grey → yellow
- 6.7: APPROVED, MVP - System shall prevent new word input until all blue squares are processed
- 6.8: APPROVED, MVP - System shall display word suggestions in sidebar ranked by score
- 6.9: APPROVED, MVP - System shall allow clicking suggestions to auto-fill guess input
- 6.10: APPROVED, MVP - System shall allow words not in wordlist (wordlist only for suggestions)
- 6.11: APPROVED, MVP - System shall provide reset/new game functionality

### Non-Functional Requirements
- 5.1: APPROVED, MVP - System shall use regex-based filtering for efficient constraint application
- 5.2: APPROVED, MVP - System shall maintain minimal state (only green/yellow/grey constraints and candidate words)
- 5.3: APPROVED, MVP - System shall provide clear, human-readable prompts and feedback messages
- 5.4: APPROVED, MVP - System shall handle invalid input gracefully with appropriate error messages
- 7.1: APPROVED, MVP - System shall be containerized using Docker
- 7.2: APPROVED, MVP - System shall respond to API requests within 500ms
- 7.3: APPROVED, MVP - System shall be responsive on mobile devices (320px+ width)
- 7.4: APPROVED, MVP - System shall support keyboard navigation
- 7.5: APPROVED, MVP - System shall maintain all game state (green/yellow/grey constraints) in the client browser
- 7.6: APPROVED, MVP - System shall use a stateless API design where the client sends all accumulated constraints with each request

### Architectural Decision Records (Technical PM Role)

- We must use regex-based filtering for green/yellow/grey constraints given performance requirements and pattern matching needs
- We shall load positional letter frequencies from /tmp/pos1.txt through /tmp/pos5.txt given these are provided as static input files
- We shall load valid Wordle words from /tmp/wordle-words.txt given this contains the complete word list
- We must implement incremental letter expansion strategy given the need to handle cases where initial top-N letters yield no candidates
- We shall exclude words with repeated letters from candidate set given Wordle rules disallow repeated letters
- We can use minimal state management (only tracking constraints and candidates) given simplicity and clarity benefits
- We must prioritize words using top positional letters for guess suggestions given the goal of maximizing information gain
- We must use python as the programming language of choice
- We shall use Flask for the web API backend given its simplicity and Python integration
- We shall use vanilla JavaScript for the frontend given no build step is required and simplicity benefits
- We shall use Docker for containerization given deployment consistency requirements
- We shall use system keyboard for input given accessibility and development simplicity benefits
- We must use a stateless API design where the client maintains all constraint state (green/yellow/grey letters) and sends complete constraint state with each request, given this eliminates state synchronization issues and simplifies the API
- We shall maintain constraint state in the client browser (ConstraintState class) to accumulate green/yellow/grey letter constraints across all rounds, given this ensures correct constraint application and prevents state loss

## Test Specifications (Developer Role)

### Test Cases
Test cases for requirements 1.1-1.4, 2.1-2.7, 3.1.1-3.1.3, 3.3, 3.5, 4.5-4.7, and 5.1-5.4 are documented in `test_wordle_solver.py`:

Test cases for requirements 6.1, 6.4, 6.10, 6.11, 7.2, 7.5, and 7.6 are documented in `api/test_api.py`:
- `TestAPIEndpoints` class: Tests for API endpoints (health, default-guess, process, reset)
- Tests cover stateless API design with constraint-based requests (greenConstraints, yellowConstraints, greyConstraints)
- Tests verify constraint accumulation simulation (client-side state management)
- Tests verify grey letter exclusion works correctly across multiple rounds
- All API tests reference requirement IDs and follow Given-When-Then format
- Note: Stateless API design (7.5, 7.6) ensures each request is independent and includes all constraint state
- `TestDataLoading` class: Tests for requirements 1.1-1.4 (data loading and initialization)
- `TestUserInputProcessing` class: Tests for requirements 2.1-2.7 (user input processing)
- `TestGuessWordFilterGeneration` class: Tests for requirements 3.1.1-3.1.3, 3.3, 3.5 (word filtering strategies)
- `TestCLIInterface` class: Tests for requirements 4.5-4.7 (interactive CLI interface)
- `TestStateManagement` class: Tests for requirement 5.2 (state management)
- `TestRegexFiltering` class: Tests for requirement 5.1 (regex-based filtering)
- All tests reference requirement IDs and follow Given-When-Then format
- Note: Requirement 3.2 has been deprecated and removed (previously split candidates into unique/repeated letter sections)

## Tasks (Developer Role)
Implementation tasks for requirements 1.1-2.7, 3.1.1-3.1.3, 3.2 (deprecated), 3.3, 3.5, 4.5-4.7, and 5.1-5.4 are complete. See test file for test case details and implementation file for code structure.

## Implementation Notes
- Requirements 1.1-1.4: Implemented in `WordleSolver.__init__`, `extract_top_letters()`, and `get_default_first_guess()` methods
- Requirements 2.1-2.7: Implemented as separate methods for prompting and converting user input (green/yellow/grey letters)
- Requirements 3.1.1-3.1.3: Implemented in `filter_candidates()` method using regex patterns for green/yellow/grey letter filtering
- Requirement 3.2: DEPRECATED and REMOVED - Previously implemented in `split_candidates_by_letter_uniqueness()` method, but removed. Candidates are now displayed as a sorted list with scoring used to prioritize solutions.
- Requirement 3.3: Implemented in `expand_candidates_when_empty()` method, automatically called when `filter_candidates()` results in empty set
- Requirement 3.5: Implemented in `compute_word_scores()` and `get_letter_line_number()` methods - computes scores based on positional frequency line numbers for unknown positions
- Requirements 4.5-4.7: Implemented in `display_candidates()`, `display_suggested_guess()`, and `solve()` methods (interactive loop)
- Requirements 5.1-5.2: Implemented in `filter_candidates()` method (regex-based filtering) and state variables in `__init__`
- Requirement 5.4: Implemented in `validate_guess()`, `validate_green_letters()`, and `validate_yellow_letters()` methods
- All methods include requirement ID references in docstrings
- User input methods use `unittest.mock.patch` for testing without actual user interaction
- Note: Requirements 4.1-4.4 are satisfied by existing prompt methods (2.1-2.4)
- Requirements 6.1, 6.4, 6.10, 6.11: Implemented in `api/app.py` Flask application with REST endpoints
- Requirements 6.2, 6.5, 6.6, 6.7: Implemented in `web/js/game-board.js` component
- Requirements 6.8, 6.9: Implemented in `web/js/suggestions.js` component
- Requirements 6.1, 6.4, 7.4: Implemented in `web/js/app.js` main application logic
- Requirements 7.1: Implemented in `Dockerfile` and `docker-compose.yml`
- Requirements 7.2: API response time optimized with efficient Flask endpoints
- Requirements 7.3: Responsive design implemented in `web/css/style.css` with mobile breakpoints
- Requirements 7.4: Keyboard navigation and ARIA labels implemented throughout frontend components
- Requirements 7.5, 7.6: Stateless API design implemented - client maintains all constraint state in `web/js/constraint-state.js`, API accepts complete constraint state in each request via `apply_constraints()` method in `wordle_solver.py`, eliminating state synchronization issues

## Test Results
All tests passing:
- CLI Tests (26/26):
  - Requirements 1.1-1.4: 4 tests passing
  - Requirements 2.1-2.7: 7 tests passing
  - Requirements 3.1.1-3.1.3: 3 tests passing
  - Requirement 3.3: 1 test passing
  - Requirement 3.5: 1 test passing
  - Requirements 4.5-4.7: 3 tests passing
  - Requirements 5.1-5.2, 5.4: 3 tests passing
- API Tests (10/10):
  - Requirements 6.1, 6.4, 6.10, 6.11: 4 tests passing
  - Requirements 7.2, 7.5, 7.6: 6 tests passing (including stateless API and constraint accumulation tests)
- Run `python3 -m unittest test_wordle_solver -v` for CLI tests
- Run `python3 -m unittest api.test_api -v` for API tests (requires Flask)
- Run `./run_tests.sh` to run all tests

## Relevant Files
- `wordle_solver.py` - Main implementation (Requirements 1.1-1.4, 2.1-2.7, 3.1.1-3.1.3, 3.3, 3.5, 4.5-4.7, 5.1-5.2, 5.4)
- `test_wordle_solver.py` - Test suite with 26 test cases covering requirements 1.1-2.7, 3.1.1-3.1.3, 3.3, 3.5, 4.5-4.7, 5.1-5.2, 5.4
- `api/app.py` - Flask API backend (Requirements 6.1, 6.4, 6.10, 6.11, 7.1, 7.2)
- `api/test_api.py` - API test suite covering requirements 6.1, 6.4, 6.10, 6.11, 7.2
- `web/index.html` - Main HTML structure (Requirements 6.1, 6.2, 6.3, 7.3, 7.4)
- `web/css/style.css` - Styling (Requirements 6.2, 7.3, 7.4)
- `web/js/app.js` - Main application logic (Requirements 6.1, 6.4, 6.7, 6.9, 7.4, 7.5, 7.6)
- `web/js/constraint-state.js` - Client-side constraint state manager (Requirements 7.5, 7.6)
- `web/js/game-board.js` - Game board component (Requirements 6.2, 6.5, 6.6, 6.7)
- `web/js/suggestions.js` - Suggestions component (Requirements 6.8, 6.9)
- `web/js/api.js` - API client (Requirements 6.1, 7.2, 7.6)
- `Dockerfile` - Container definition (Requirement 7.1)
- `docker-compose.yml` - Development setup (Requirement 7.1)
