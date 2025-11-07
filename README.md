# Wordle Solver

An interactive command-line tool that helps you solve Wordle puzzles by analyzing letter frequencies and filtering candidate words based on your guesses and feedback.

## Overview

Wordle Solver guides you through solving Wordle puzzles by:
- Suggesting optimal first guesses based on positional letter frequency analysis
- Filtering candidate words based on green (correct position), yellow (wrong position), and grey (not in word) feedback
- Expanding candidate sets using frequency data when initial filtering yields no results
- Providing clear, human-readable feedback and suggestions

## Prerequisites

- Python 3.6 or higher
- Required input files (see Setup section)

## Setup

### 1. Required Input Files

The solver requires the following files to be present in the `./lib/` directory:

#### Positional Letter Frequency Files
- `./lib/pos1.txt` - Letters for position 1, ordered by frequency (descending)
- `./lib/pos2.txt` - Letters for position 2, ordered by frequency (descending)
- `./lib/pos3.txt` - Letters for position 3, ordered by frequency (descending)
- `./lib/pos4.txt` - Letters for position 4, ordered by frequency (descending)
- `./lib/pos5.txt` - Letters for position 5, ordered by frequency (descending)

**Format**: Each line contains a frequency count followed by a space and the letter:
```
frequency letter
```

Example `./lib/pos1.txt`:
```
1132 s
635 c
635 a
629 b
584 t
506 p
...
```

The files are sorted in descending order by frequency (highest frequency first). The solver extracts the letter from each line, ignoring the frequency count.

#### Valid Word List
- `./lib/wordle-words.txt` - List of valid 5-letter Wordle words (one word per line, lowercase)

Example `./lib/wordle-words.txt`:
```
saint
slant
plant
chant
grant
...
```

### 2. Installation

No installation required! Just ensure you have Python 3.6+ and the required input files.

## Usage

### Running the Solver

Run the solver from the command line:

```bash
python3 wordle_solver.py
```

Or import and use programmatically:

```python
from wordle_solver import WordleSolver

solver = WordleSolver()
solver.solve()
```

### Interactive Session Guide

1. **Start the solver**: Run `python3 wordle_solver.py`

2. **Enter your first guess**: 
   - The solver suggests "SAINT" as the default first guess
   - Press Enter to use the default, or type your own 5-letter word
   - The solver accepts input in any case (uppercase, lowercase, or mixed)

3. **Enter green letters feedback**:
   - Green letters = correct letter in correct position
   - Use dots (`.`) for unknown positions
   - Example: If you guessed "SAINT" and got S and T in correct positions, enter `S..NT`

4. **Enter yellow letters feedback**:
   - Yellow letters = correct letter in wrong position
   - Use dots (`.`) for positions where the letter is NOT located
   - Example: If A is in the word but not in position 2, enter `.A...`

5. **Enter grey letters**:
   - Grey letters = letters not in the word at all
   - Enter space-separated letters (e.g., `E R T`)
   - Can be uppercase, lowercase, or mixed

6. **Review suggestions**:
   - The solver displays filtered candidate words
   - A suggested next guess is provided
   - Repeat steps 2-5 until the puzzle is solved

7. **Exit**: Type `quit` at any prompt to exit

### Example Session

```
Welcome to Wordle Solver!
Enter 'quit' at any time to exit.

--- Round 1 ---
Enter your guess (default: SAINT): 
Enter green letters feedback (use dots for unknown positions, e.g., 'S..NT'): .....
Enter yellow letters feedback (use dots for positions, e.g., '.A...'): .A...
Enter grey letters (space-separated, e.g., 'E R T'): E R

Found 15 candidate word(s):
  CHANT GRANT PLANT SAINT SLANT

Suggested next guess: SAINT

--- Round 2 ---
Enter your guess (default: SAINT): PLANT
Enter green letters feedback (use dots for unknown positions, e.g., 'S..NT'): PLAN.
Enter yellow letters feedback (use dots for positions, e.g., '.A...'): .....
Enter grey letters (space-separated, e.g., 'E R T'): 

Found 2 candidate word(s):
  PLANE PLANT

Suggested next guess: PLANE

--- Round 3 ---
Enter your guess (default: SAINT): PLANE
Enter green letters feedback (use dots for unknown positions, e.g., 'S..NT'): PLANT

🎉 Congratulations! Puzzle solved!
```

## Understanding Feedback Format

### Green Letters
- **Format**: 5-character string with letters and dots
- **Meaning**: Letters in correct positions
- **Example**: `S..NT` means:
  - Position 1: S (correct)
  - Position 2: unknown
  - Position 3: unknown
  - Position 4: N (correct)
  - Position 5: T (correct)

### Yellow Letters
- **Format**: 5-character string with letters and dots
- **Meaning**: Letters present in word but NOT in this position
- **Example**: `.A...` means:
  - A is in the word somewhere
  - A is NOT in position 2 (where it appears in your guess)

### Grey Letters
- **Format**: Space-separated letters
- **Meaning**: Letters not in the word at all
- **Example**: `E R T` means E, R, and T are not in the word

## Features

- **Smart Filtering**: Uses regex-based filtering for efficient constraint application
- **Frequency Analysis**: Leverages positional letter frequency data for optimal suggestions
- **Automatic Expansion**: When no candidates match, automatically expands using frequency data
- **Input Validation**: Gracefully handles invalid input with clear error messages
- **Case Insensitive**: Accepts input in any case format
- **Interactive Loop**: Continues until puzzle solved or user exits

## Troubleshooting

### "No candidate words found"
- This is normal when constraints are very restrictive
- The solver will automatically try to expand candidates using frequency data
- If still empty, try entering more guesses to gather more information

### Invalid Input Errors
- **Guess**: Must be exactly 5 letters, alphabetic only
- **Green/Yellow feedback**: Must be exactly 5 characters (letters and dots only)
- **Grey letters**: Space-separated letters, any length

### File Not Found Errors
- Ensure all required files exist in `./lib/` directory
- Check file permissions (must be readable)
- Verify file format (one item per line)

## MCP Tool Support

The Wordle Solver can be used as an MCP (Model Context Protocol) tool for integration with AI assistants.

### HTTP API (Requirement 6.5)

Start the FastAPI server:
```bash
python -m uvicorn mcp.api:app --host 0.0.0.0 --port 8000
```

Make POST requests to `/process_feedback`:
```bash
curl -X POST "http://localhost:8000/process_feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "guess": "saint",
    "greens": "..i..",
    "yellows": "s....",
    "greys": ["a", "n", "t"]
  }'
```

### Python SDK (Requirement 6.3)

Run the MCP tool directly:
```bash
python mcp/wordle_mcp.py
```

### ChatGPT Plugin (Requirement 6.6)

The Wordle Solver can be used as a ChatGPT plugin:

1. Start the FastAPI server:
```bash
python -m uvicorn mcp.api:app --host 0.0.0.0 --port 8000
```

2. In ChatGPT, go to Settings → Beta features → Plugins → Install an unverified plugin

3. Enter your server URL (e.g., `http://localhost:8000`)

4. ChatGPT will automatically discover the plugin via:
   - `/.well-known/ai-plugin.json` - Plugin manifest
   - `/openapi.yaml` - OpenAPI specification

The plugin files are located in:
- `.well-known/ai-plugin.json` - ChatGPT plugin manifest
- `openapi.yaml` - OpenAPI 3.0 specification

## Customization

You can customize file paths when creating a solver instance:

```python
from wordle_solver import WordleSolver

# Use custom paths
solver = WordleSolver(
    frequency_dir='/path/to/frequency/files',
    words_file='/path/to/wordle-words.txt'
)
```

## Project Structure

```
wordle-solver/
├── wordle_solver.py      # Main solver implementation
├── test_wordle_solver.py # Test suite
├── README.md             # This file
└── docs/
    ├── PROJECT.md        # Requirements and specifications
    ├── ROLES.md          # Development role definitions
    ├── WORKFLOW.md       # Development workflow
    └── PROMPTS.md        # AI agent prompts
```

## Testing

Run the test suite to verify everything works:

```bash
python3 -m unittest test_wordle_solver -v
```

## Methodology

This project is implemented using the Sancak methodology framework. See the framework documentation in `/docs` for development methodology details.
