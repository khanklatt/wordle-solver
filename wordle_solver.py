"""
Wordle Solver - Interactive CLI tool for solving Wordle puzzles

This module provides an interactive command-line tool that helps users solve Wordle puzzles
by analyzing letter frequencies and filtering candidate words based on user feedback.

Example usage:
    >>> solver = WordleSolver()
    >>> solver.solve()

The solver requires:
    - Positional frequency files: /tmp/pos1.txt through /tmp/pos5.txt
    - Valid word list: /tmp/wordle-words.txt

See README.md for detailed setup and usage instructions.
"""
import os
import re
from typing import Dict, Set, List, Tuple, Optional, Callable, Any


class WordleSolver:
    """
    Main Wordle Solver class
    Loads positional letter frequencies and valid words to suggest guesses
    """
    # Constants
    WORD_LENGTH = 5
    PENALTY_SCORE = 1000
    WORDS_PER_LINE = 10
    MAX_LETTERS_IN_ALPHABET = 26
    VOWELS = set('aeiou')
    
    def __init__(self, frequency_dir: str = '/tmp', words_file: str = '/tmp/wordle-words.txt'):
        """
        Initialize Wordle Solver
        
        Requirement 1.1: Load positional letter frequency files from /tmp/pos1.txt through /tmp/pos5.txt
        Requirement 1.3: Load valid Wordle words from /tmp/wordle-words.txt
        
        Args:
            frequency_dir: Directory containing positional frequency files (default: /tmp)
            words_file: Path to file containing valid Wordle words (default: /tmp/wordle-words.txt)
        
        Raises:
            IOError: If files cannot be read (with clear error message)
        """
        self.positional_frequencies: Dict[int, str] = {}
        self.valid_words: Set[str] = set()
        
        # Load frequency files for positions 1-5
        for pos in range(1, self.WORD_LENGTH + 1):
            filepath = os.path.join(frequency_dir, f'pos{pos}.txt')
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        # Store the file content for now (will extract top-N in req 1.2)
                        self.positional_frequencies[pos] = f.read()
                except IOError as e:
                    raise IOError(f"Failed to load frequency file {filepath}: {e}") from e
        
        # Load valid Wordle words
        if os.path.exists(words_file):
            try:
                with open(words_file, 'r') as f:
                    # Store words as lowercase set for efficient lookup
                    self.valid_words = {line.strip().lower() for line in f if line.strip()}
            except IOError as e:
                raise IOError(f"Failed to load word list {words_file}: {e}") from e
        
        # Requirement 5.2: Maintain minimal state (only green/yellow/grey constraints and candidate words)
        self.green_constraints: Dict[int, str] = {}  # position -> letter mapping
        self.yellow_constraints: Dict[str, Set[int]] = {}  # letter -> set of excluded positions
        self.grey_constraints: Set[str] = set()  # set of excluded letters
        self.candidate_words: Set[str] = set()  # filtered candidate words
    
    def extract_top_letters(self, position: int, n: int) -> List[str]:
        """
        Extract top-N letters per position from frequency files
        
        Requirement 1.2: Extract top-N letters per position from frequency files
        
        Args:
            position: Position number (1-5)
            n: Number of top letters to extract
            
        Returns:
            List of top N letters for the given position
        """
        if position not in self.positional_frequencies:
            return []
        
        # Parse file content - format is "frequency letter" (e.g., "1132 s") or just "letter"
        content = self.positional_frequencies[position]
        letters = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            # Parse format: "frequency letter" or just "letter"
            parts = line.split()
            if len(parts) >= 2:
                # Format: "frequency letter" - take the last part (letter)
                letter = parts[-1].lower()
            else:
                # Format: just "letter" - backward compatibility
                letter = parts[0].lower()
            if letter and letter.isalpha():
                letters.append(letter)
        
        # Return top N letters
        return letters[:n]
    
    def get_letter_line_number(self, position: int, letter: str) -> Optional[int]:
        """
        Get the line number (1-indexed) where a letter appears in a positional frequency file
        
        Args:
            position: Position number (1-5)
            letter: Letter to find (case insensitive)
            
        Returns:
            Line number (1-indexed) where letter appears, or None if not found
        """
        if position not in self.positional_frequencies:
            return None
        
        letter_lower = letter.lower()
        content = self.positional_frequencies[position]
        lines = content.strip().split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue
            # Parse format: "frequency letter" or just "letter"
            parts = line.split()
            if len(parts) >= 2:
                file_letter = parts[-1].lower()
            else:
                file_letter = parts[0].lower()
            
            if file_letter == letter_lower:
                return line_num
        
        return None
    
    def compute_word_scores(self, candidate_words: Optional[Set[str]] = None) -> List[Tuple[str, int]]:
        """
        Compute word score for each candidate word based on positional frequency line numbers
        
        Requirement 3.5: Compute word score - lower score is better
        Score is sum of line numbers where letters appear in frequency files for unknown positions
        
        Args:
            candidate_words: Optional set of words to score. If None, uses self.candidate_words.
        
        Returns:
            List of (word, score) tuples sorted by score (lowest first)
        """
        words = candidate_words if candidate_words is not None else self.candidate_words
        if not words:
            return []
        
        # Find unknown positions (positions not in green_constraints)
        unknown_positions = [pos for pos in range(1, self.WORD_LENGTH + 1) if pos not in self.green_constraints]
        
        if not unknown_positions:
            # All positions are known, return words with score 0
            return [(word, 0) for word in sorted(words)]
        
        scored_words = []
        
        for word in words:
            score = 0
            for pos in unknown_positions:
                letter = word[pos - 1].lower()  # Get letter at this position (0-indexed: pos-1)
                line_num = self.get_letter_line_number(pos, letter)
                if line_num is not None:
                    score += line_num
                else:
                    # Letter not found in frequency file - assign high penalty score
                    score += self.PENALTY_SCORE
            
            scored_words.append((word, score))
        
        # Sort by score (lowest first), then alphabetically for ties
        scored_words.sort(key=lambda x: (x[1], x[0]))
        
        return scored_words
    
    def get_words_with_most_vowels(self) -> Set[str]:
        """
        Get words with the most vowels from candidate words
        
        Requirement 3.4: Prioritize words that have the most vowels
        
        Returns:
            Set of words with the highest vowel count
        """
        if not self.candidate_words:
            return set()
        
        max_vowel_count = 0
        vowel_words = set()
        
        for word in self.candidate_words:
            vowel_count = sum(1 for char in word.lower() if char in self.VOWELS)
            if vowel_count > max_vowel_count:
                max_vowel_count = vowel_count
                vowel_words = {word}
            elif vowel_count == max_vowel_count:
                vowel_words.add(word)
        
        return vowel_words
    
    def get_suggested_next_guess(self) -> Optional[List[Tuple[str, int]]]:
        """
        Get suggested next guess using vowel prioritization and positional frequency scoring
        
        Requirement 3.4: Prioritize words with most vowels
        Requirement 3.5: Score words based on positional frequency line numbers
        Requirement 3.5.1: Return all scored words for display
        
        Returns:
            List of (word, score) tuples sorted by score (lowest first), or None if no candidates
        """
        if not self.candidate_words:
            return None
        
        # Requirement 3.4: Get words with most vowels
        vowel_words = self.get_words_with_most_vowels()
        
        if not vowel_words:
            # Fallback to all candidates if no vowels found (shouldn't happen with valid words)
            vowel_words = self.candidate_words
        
        # Requirement 3.5: Score the vowel-rich words
        # Pass vowel_words as parameter instead of mutating state
        scored_words = self.compute_word_scores(candidate_words=vowel_words)
        
        if scored_words:
            # Requirement 3.5.1: Return all scored words
            return scored_words
        
        # Fallback: create scored list from vowel words with score 0
        return [(word, 0) for word in sorted(vowel_words)]
    
    def get_default_first_guess(self) -> str:
        """
        Get default first guess suggestion
        
        Requirement 1.4: Initialize with default first guess suggestion of "SAINT"
        
        Returns:
            Default first guess word "SAINT"
        """
        return 'SAINT'
    
    def prompt_for_guess(self) -> str:
        """
        Prompt user for guess input (case insensitive)
        
        Requirement 2.1: Prompt user for what guess the user opens with (case insensitive)
        
        Returns:
            User's guess in uppercase
        """
        user_input = input("Enter your guess: ").strip()
        # Empty input will be caught by validation in solve() method
        
        # Convert to uppercase (case insensitive per requirement 2.1)
        return user_input.upper()
    
    def prompt_for_green_letters(self) -> str:
        """
        Prompt user for green letters feedback
        
        Requirement 2.2: Prompt user for "green" letters feedback from Wordle as string with dots for unknown positions
        Requirement 4.2: Prompt user for green letters feedback after each guess
        
        Returns:
            Green letters feedback string (e.g., "S..NT" for SAINT -> SLANT)
        """
        user_input = input("Enter green letters feedback (use dots for unknown positions, e.g., 'S..NT'): ").strip()
        return user_input.upper()
    
    def convert_green_letters(self, green_string: str) -> Dict[int, str]:
        """
        Convert green letters string into position-to-letter mapping dictionary
        
        Requirement 2.3: Convert green letters string into position-to-letter mapping dictionary
        
        Args:
            green_string: String with letters and dots (e.g., "S..NT")
            
        Returns:
            Dictionary mapping position (1-indexed) to letter
        """
        mapping = {}
        for i, char in enumerate(green_string, start=1):
            if char != '.':
                mapping[i] = char.upper()
        return mapping
    
    def prompt_for_yellow_letters(self) -> str:
        """
        Prompt user for yellow letters input
        
        Requirement 2.4: Prompt user for yellow letters input as string with dots for positional communication
        Requirement 4.3: Prompt user for yellow letters feedback after green letters input
        
        Returns:
            Yellow letters feedback string (e.g., ".A..." for SAINT -> SLANT)
        """
        user_input = input("Enter yellow letters feedback (use dots for positions, e.g., '.A...'): ").strip()
        return user_input.upper()
    
    def convert_yellow_letters(self, yellow_string: str) -> Dict[str, Set[int]]:
        """
        Convert yellow letters into letter-to-excluded-positions mapping dictionary
        
        Requirement 2.5: Convert yellow letters into letter-to-excluded-positions mapping dictionary
        
        Args:
            yellow_string: String with letters and dots (e.g., ".A..." meaning A is present but not in position 2)
            
        Returns:
            Dictionary mapping letter to set of excluded positions (1-indexed)
        """
        mapping = {}
        for i, char in enumerate(yellow_string, start=1):
            if char != '.':
                letter = char.upper()
                if letter not in mapping:
                    mapping[letter] = set()
                mapping[letter].add(i)
        return mapping
    
    def prompt_for_grey_letters(self) -> str:
        """
        Accept grey letters input as space-separated letters
        
        Requirement 2.6: Accept grey letters input as space-separated letters
        Requirement 4.4: Prompt user for grey letters feedback after yellow letters input
        
        Returns:
            Grey letters input string (space-separated)
        """
        user_input = input("Enter grey letters (space-separated, e.g., 'E R T'): ").strip()
        return user_input.upper()
    
    def validate_grey_letters(self, grey_string: str) -> Tuple[bool, str]:
        """
        Validate grey letters input format
        
        Requirement 5.4: Handle invalid input gracefully with appropriate error messages
        
        Args:
            grey_string: Grey letters input string (space-separated)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not grey_string:
            return True, ""  # Empty is valid (no grey letters)
        
        # Check that all characters are letters or spaces
        for char in grey_string:
            if not (char.isalpha() or char.isspace()):
                return False, "Error: Grey letters must contain only letters and spaces."
        
        # Check that letters are single characters (not words)
        letters = grey_string.split()
        for letter in letters:
            if len(letter) != 1:
                return False, f"Error: Each grey letter must be a single character (got '{letter}')."
            if not letter.isalpha():
                return False, f"Error: Grey letters must be alphabetic (got '{letter}')."
        
        return True, ""
    
    def convert_grey_letters(self, grey_string: str) -> Set[str]:
        """
        Convert grey letters into set of excluded letters
        
        Requirement 2.7: Convert grey letters into set of excluded letters
        
        Args:
            grey_string: Space-separated letters (e.g., "E R T")
            
        Returns:
            Set of excluded letters (uppercase)
        """
        if not grey_string:
            return set()
        return {letter.upper() for letter in grey_string.split() if letter.strip()}
    
    def split_candidates_by_letter_uniqueness(self) -> Tuple[Set[str], Set[str]]:
        """
        Split candidate words into unique letters and repeated letters sections
        
        Requirement 3.2: Return candidate sets split into two sections - unique letters and repeated letters
        
        Returns:
            Tuple of (unique_letters_words, repeated_letters_words) sets
        """
        unique_words = set()
        repeated_words = set()
        
        for word in self.candidate_words:
            # Check if word has all unique letters
            letter_set = set(word.lower())
            if len(letter_set) == len(word):
                # All letters are unique
                unique_words.add(word)
            else:
                # Has repeated letters
                repeated_words.add(word)
        
        return unique_words, repeated_words
    
    def display_candidates(self) -> None:
        """
        Display filtered candidate words after each constraint application
        
        Requirement 4.5: Display filtered candidate words after each constraint application
        Requirement 3.2: Display candidates split into unique letters and repeated letters sections
        Requirement 5.3: Provide clear, human-readable prompts and feedback messages
        
        """
        if not self.candidate_words:
            print("No candidate words found.")
            return
        
        # Requirement 3.2: Split into unique letters and repeated letters sections
        unique_words, repeated_words = self.split_candidates_by_letter_uniqueness()
        
        print(f"\nFound {len(self.candidate_words)} candidate word(s):")
        
        # Section 1: Words with unique letters
        if unique_words:
            print(f"\nSection 1 - Unique letters ({len(unique_words)} word(s)):")
            sorted_unique = sorted(unique_words)
            for i in range(0, len(sorted_unique), self.WORDS_PER_LINE):
                line_words = sorted_unique[i:i+self.WORDS_PER_LINE]
                print("  " + " ".join(word.upper() for word in line_words))
        
        # Section 2: Words with repeated letters
        if repeated_words:
            print(f"\nSection 2 - Repeated letters ({len(repeated_words)} word(s)):")
            sorted_repeated = sorted(repeated_words)
            for i in range(0, len(sorted_repeated), self.WORDS_PER_LINE):
                line_words = sorted_repeated[i:i+self.WORDS_PER_LINE]
                print("  " + " ".join(word.upper() for word in line_words))
    
    def display_suggested_guess(self, scored_words: Optional[List[Tuple[str, int]]] = None) -> None:
        """
        Display suggested next guess after all constraints are applied
        
        Requirement 4.6: Display suggested next guess after all constraints are applied
        Requirement 3.5.1: Display all scored words with their scores
        Requirement 5.3: Provide clear, human-readable prompts and feedback messages
        
        Args:
            scored_words: List of (word, score) tuples, or None/string for default first guess
        """
        if scored_words is None:
            # No candidates, show default first guess
            print(f"\nSuggested next guess: {self.get_default_first_guess()}")
        elif isinstance(scored_words, str):
            # Backward compatibility: single word string
            print(f"\nSuggested next guess: {scored_words}")
        elif isinstance(scored_words, list) and len(scored_words) > 0:
            # Requirement 3.5.1: Display all scored words with scores
            print("\nSuggested next guess:")
            for word, score in scored_words:
                print(f"  {word.upper()} (score: {score})")
        else:
            # Empty list, fallback to default
            print(f"\nSuggested next guess: {self.get_default_first_guess()}")
    
    def validate_guess(self, guess: str) -> Tuple[bool, str]:
        """
        Validate guess input
        
        Requirement 5.4: Handle invalid input gracefully with appropriate error messages
        
        Args:
            guess: Guess word to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not guess:
            return False, "Error: Guess cannot be empty."
        if len(guess) != self.WORD_LENGTH:
            return False, f"Error: Guess must be exactly {self.WORD_LENGTH} letters (got {len(guess)})."
        if not guess.isalpha():
            return False, "Error: Guess must contain only letters."
        return True, ""
    
    def validate_green_letters(self, green_string: str) -> Tuple[bool, str]:
        """
        Validate green letters input format
        
        Requirement 5.4: Handle invalid input gracefully with appropriate error messages
        
        Args:
            green_string: Green letters feedback string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not green_string:
            return False, "Error: Green letters feedback cannot be empty."
        if len(green_string) != self.WORD_LENGTH:
            return False, f"Error: Green letters must be exactly {self.WORD_LENGTH} characters (got {len(green_string)})."
        if not all(c.isalpha() or c == '.' for c in green_string):
            return False, "Error: Green letters must contain only letters and dots."
        return True, ""
    
    def validate_yellow_letters(self, yellow_string: str) -> Tuple[bool, str]:
        """
        Validate yellow letters input format
        
        Requirement 5.4: Handle invalid input gracefully with appropriate error messages
        
        Args:
            yellow_string: Yellow letters feedback string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not yellow_string:
            return True, ""  # Empty is valid (no yellow letters)
        if len(yellow_string) != self.WORD_LENGTH:
            return False, f"Error: Yellow letters must be exactly {self.WORD_LENGTH} characters (got {len(yellow_string)})."
        if not all(c.isalpha() or c == '.' for c in yellow_string):
            return False, "Error: Yellow letters must contain only letters and dots."
        return True, ""
    
    def _prompt_with_validation(
        self,
        prompt_func: Callable[[], str],
        validate_func: Callable[[str], Tuple[bool, str]],
        convert_func: Optional[Callable[[str], str]] = None
    ) -> Optional[str]:
        """
        Generic prompt loop with validation and quit handling
        
        Args:
            prompt_func: Function that prompts user and returns input string
            validate_func: Function that validates input and returns (is_valid, error_msg)
            convert_func: Optional function to convert input (default: uppercase)
        
        Returns:
            Validated and converted input string, or None if user quits
        """
        while True:
            try:
                user_input = prompt_func()
                if user_input.upper() == 'QUIT':
                    print("Exiting Wordle Solver. Goodbye!")
                    return None
                
                is_valid, error_msg = validate_func(user_input)
                if is_valid:
                    if convert_func:
                        return convert_func(user_input)
                    return user_input.upper()
                else:
                    print(error_msg)
                    print("Please try again.")
            except KeyboardInterrupt:
                print("\n\nExiting Wordle Solver. Goodbye!")
                return None
    
    def solve(self) -> bool:
        """
        Main interactive loop for solving Wordle puzzle
        
        Requirement 4.7: Continue interactive loop until puzzle is solved or user exits
        Requirement 4.1-4.4: Prompt user for guess and feedback in sequence
        Requirement 4.5: Display filtered candidate words after each constraint application
        Requirement 4.6: Display suggested next guess after all constraints are applied
        
        Returns:
            True if puzzle solved, False if user exited
        """
        print("Welcome to Wordle Solver!")
        print("Enter 'quit' at any time to exit.\n")
        
        # Requirement 4.1: Suggest default first guess
        print(f"Suggested first guess: {self.get_default_first_guess()}\n")
        
        round_num = 1
        
        while True:
            print(f"\n--- Round {round_num} ---")
            
            # Requirement 4.1: Prompt for guess
            guess = self._prompt_with_validation(
                self.prompt_for_guess,
                self.validate_guess
            )
            if guess is None:
                return False
            
            # Requirement 4.2: Prompt for green letters
            green_feedback = self._prompt_with_validation(
                self.prompt_for_green_letters,
                self.validate_green_letters
            )
            if green_feedback is None:
                return False
            
            # Update green constraints
            self.green_constraints = self.convert_green_letters(green_feedback)
            
            # Check if puzzle is solved (all positions are green)
            if len(self.green_constraints) == self.WORD_LENGTH:
                print("\n🎉 Congratulations! Puzzle solved!")
                return True
            
            # Requirement 4.3: Prompt for yellow letters
            yellow_feedback = self._prompt_with_validation(
                self.prompt_for_yellow_letters,
                self.validate_yellow_letters
            )
            if yellow_feedback is None:
                return False
            
            # Requirement 4.4: Prompt for grey letters
            grey_input = self._prompt_with_validation(
                self.prompt_for_grey_letters,
                self.validate_grey_letters
            )
            if grey_input is None:
                return False
            
            # Process feedback using the refactored method (maintains consistency)
            # Convert grey input to list format for process_feedback
            grey_list = grey_input.split() if grey_input else []
            result = self.process_feedback(guess, green_feedback, yellow_feedback, grey_list)
            
            # Requirement 4.5: Display filtered candidates
            self.display_candidates()
            
            # Requirement 4.6: Display suggested next guess
            # Convert suggestions back to format expected by display_suggested_guess
            if result["suggestions"]:
                scored_words = [(s["word"].lower(), s["score"]) for s in result["suggestions"]]
                self.display_suggested_guess(scored_words)
            else:
                self.display_suggested_guess(None)
            
            round_num += 1
    
    def process_feedback(
        self,
        guess: str,
        greens: str,
        yellows: str,
        greys: List[str]
    ) -> Dict[str, Any]:
        """
        Process Wordle feedback and return candidates and suggestions
        
        Requirement 6.2: Refactor solver logic into a clean, callable function
        Requirement 6.2.1: Function named process_feedback
        Requirement 6.2.2: Takes guess, greens, yellows, greys parameters
        Requirement 6.2.3: Returns dictionary with candidates and suggestions
        
        This method processes feedback without user interaction, making it suitable
        for programmatic use (e.g., MCP tools) while maintaining the same core logic
        as the interactive solve() method.
        
        Args:
            guess: The guessed word (e.g., "saint")
            greens: Green letters feedback string with dots for unknown positions (e.g., "..i..")
            yellows: Yellow letters feedback string with dots (e.g., "s....")
            greys: List of excluded letters (e.g., ["a", "n", "t"])
        
        Returns:
            Dictionary containing:
                - candidates: List of candidate words (strings)
                - suggestions: List of dictionaries with "word" and "score" keys
                  Example: [{"word": "GUISE", "score": 19}, {"word": "POISE", "score": 20}]
        """
        # Convert inputs to proper format
        guess_upper = guess.upper()
        greens_upper = greens.upper()
        yellows_upper = yellows.upper()
        greys_upper = [g.upper() for g in greys]
        
        # Update constraints based on feedback
        # Requirement 2.3: Convert green letters to position mapping
        self.green_constraints = self.convert_green_letters(greens_upper)
        
        # Requirement 2.5: Convert yellow letters to excluded positions mapping
        self.yellow_constraints = self.convert_yellow_letters(yellows_upper)
        
        # Requirement 2.7: Convert grey letters to excluded set
        # Note: This replaces existing grey constraints (for MCP use case)
        # For CLI, we use update() to accumulate across rounds
        self.grey_constraints = set(greys_upper)
        
        # Requirement 5.1: Filter candidate words using regex-based filtering
        self.filter_candidates()
        
        # Get candidate words as sorted list
        candidates = sorted(self.candidate_words)
        
        # Requirement 3.4 & 3.5: Get suggested guesses with scores
        scored_words = self.get_suggested_next_guess()
        
        # Format suggestions as list of dicts
        suggestions = []
        if scored_words:
            for word, score in scored_words:
                suggestions.append({"word": word.upper(), "score": score})
        
        # Requirement 6.2.3: Return dictionary with candidates and suggestions
        return {
            "candidates": candidates,
            "suggestions": suggestions
        }
    
    def filter_candidates(self) -> None:
        """
        Filter candidate words using regex-based constraints
        
        Requirement 5.1: Use regex-based filtering for efficient constraint application
        Requirement 3.1.1: Green letters: Fixed positions specified by green letters shall be applied via regex
        Requirement 3.1.2: Yellow letters: Included in regex for positions without GREEN, excluded from YELLOW positions
        Requirement 3.1.3: Grey letters: Exclude words containing grey letters
        
        This method applies all constraints to filter the candidate word set.
        """
        if not self.valid_words:
            self.candidate_words = set()
            return
        
        # Start with all valid words
        candidates = self.valid_words.copy()
        
        # Requirement 3.1.3: Grey letters - exclude words containing grey letters
        if self.grey_constraints:
            grey_pattern = '|'.join(self.grey_constraints)
            candidates = {w for w in candidates if not re.search(grey_pattern, w, re.IGNORECASE)}
        
        # Requirement 3.1.1: Green letters - build regex pattern for fixed positions
        regex_pattern = [''] * self.WORD_LENGTH  # Initialize pattern for all positions
        for pos, letter in self.green_constraints.items():
            regex_pattern[pos - 1] = letter.lower()  # Convert to lowercase for matching
        
        # Requirement 3.1.2: Yellow letters - include in positions without GREEN, exclude from YELLOW positions
        yellow_letters_to_include = set()
        for letter, excluded_positions in self.yellow_constraints.items():
            yellow_letters_to_include.add(letter.lower())
            # Mark excluded positions in regex pattern
            for pos in excluded_positions:
                if not regex_pattern[pos - 1]:  # Only if position not already fixed by green
                    # Build negative lookahead or character class excluding this letter
                    if regex_pattern[pos - 1] == '':
                        regex_pattern[pos - 1] = f'[^{letter.lower()}]'
                    else:
                        # If already has a pattern, rebuild character class to exclude letter
                        if regex_pattern[pos - 1].startswith('[^'):
                            # Extract existing exclusions and add new one
                            existing = regex_pattern[pos - 1][2:-1]  # Remove [^ and ]
                            if letter.lower() not in existing:
                                regex_pattern[pos - 1] = f'[^{existing}{letter.lower()}]'
                        else:
                            # Create new exclusion pattern
                            regex_pattern[pos - 1] = f'[^{letter.lower()}]'
        
        # Build final regex pattern
        for i in range(self.WORD_LENGTH):
            if regex_pattern[i] == '':
                # Position not fixed - allow any letter
                regex_pattern[i] = '[a-z]'
        
        # Apply regex filtering
        pattern = '^' + ''.join(regex_pattern) + '$'
        regex_candidates = {w for w in candidates if re.match(pattern, w)}
        
        # Ensure yellow letters are present in the word (if any yellow constraints)
        if yellow_letters_to_include:
            final_candidates = set()
            for word in regex_candidates:
                word_letters = set(word.lower())
                # Check that all required yellow letters are present
                if yellow_letters_to_include.issubset(word_letters):
                    final_candidates.add(word)
            regex_candidates = final_candidates
        
        self.candidate_words = regex_candidates
        
        # Requirement 3.3: If candidate set is empty, expand using positional frequencies
        if not self.candidate_words:
            self.expand_candidates_when_empty()
    
    def expand_candidates_when_empty(self) -> None:
        """
        Iteratively expand top-N letter set when candidate set becomes empty
        
        Requirement 3.3: Iteratively expand top-N letter set incrementally when candidate set becomes empty
        
        This method generates candidate words by:
        1. Identifying unfixed positions (not in green_constraints)
        2. For each unfixed position, getting letters from positional frequency files
        3. Generating candidate words by combining fixed letters with frequency-based letters
        4. Skipping letters that are in grey_constraints
        5. Adding valid words that match all constraints
        
        Example: If first 4 letters are PLAN and pos5.txt contains e,y,a,t,r,
        and E is grey, it will check plany, plana, plant, etc. until finding valid words.
        """
        if not self.candidate_words and self.valid_words:
            # Find unfixed positions (positions not in green_constraints)
            fixed_positions = set(self.green_constraints.keys())
            unfixed_positions = [pos for pos in range(1, self.WORD_LENGTH + 1) if pos not in fixed_positions]
            
            if not unfixed_positions:
                # All positions are fixed, no expansion needed
                return
            
            # Start with a base pattern from green constraints
            base_word = [''] * self.WORD_LENGTH
            for pos, letter in self.green_constraints.items():
                base_word[pos - 1] = letter.lower()
            
            # For each unfixed position, get letters from frequency file
            # We'll expand incrementally, starting with top letters
            expanded_candidates = set()
            
            # Get letters for each unfixed position from frequency files
            position_letters = {}
            for pos in unfixed_positions:
                # Get all letters from frequency file for this position (up to reasonable limit)
                letters = self.extract_top_letters(pos, n=self.MAX_LETTERS_IN_ALPHABET)
                # Filter out grey letters
                filtered_letters = [l for l in letters if l.upper() not in self.grey_constraints]
                position_letters[pos] = filtered_letters
            
            # Generate candidate words by trying combinations
            # For simplicity, we'll generate words by filling unfixed positions with frequency letters
            # Start with single unfixed position case (most common)
            if len(unfixed_positions) == 1:
                pos = unfixed_positions[0]
                for letter in position_letters[pos]:
                    candidate = base_word.copy()
                    candidate[pos - 1] = letter
                    word = ''.join(candidate)
                    
                    # Check if word is valid and matches all constraints
                    if word in self.valid_words:
                        # Verify it matches green constraints (already built in)
                        # Verify it doesn't contain grey letters (already filtered)
                        # Verify yellow constraints if any
                        matches = True
                        
                        # Check yellow constraints: letter must be present but not in excluded positions
                        for yellow_letter, excluded_positions in self.yellow_constraints.items():
                            if yellow_letter.lower() not in word:
                                matches = False
                                break
                            # Check that yellow letter is not in any excluded position
                            for excluded_pos in excluded_positions:
                                if word[excluded_pos - 1] == yellow_letter.lower():
                                    matches = False
                                    break
                            if not matches:
                                break
                        
                        if matches:
                            expanded_candidates.add(word)
                            # Stop after finding first valid word (per requirement: "until it reaches plant")
                            # Actually, let's collect a few candidates for better suggestions
                            if len(expanded_candidates) >= 10:  # Limit to top 10
                                break
            else:
                # Multiple unfixed positions - more complex, generate combinations
                # For now, prioritize first unfixed position
                if unfixed_positions:
                    pos = unfixed_positions[0]
                    for letter in position_letters[pos][:5]:  # Limit to top 5 for performance
                        candidate = base_word.copy()
                        candidate[pos - 1] = letter
                        # For remaining positions, try common letters or leave flexible
                        # This is a simplified approach - could be enhanced
                        partial_word = ''.join(c if c else '.' for c in candidate)
                        # Match against valid words
                        pattern = '^' + partial_word.replace('.', '[a-z]') + '$'
                        for word in self.valid_words:
                            if re.match(pattern, word):
                                # Check constraints
                                matches = True
                                # Check grey letters
                                for grey_letter in self.grey_constraints:
                                    if grey_letter.lower() in word:
                                        matches = False
                                        break
                                if not matches:
                                    continue
                                
                                # Check yellow constraints
                                for yellow_letter, excluded_positions in self.yellow_constraints.items():
                                    if yellow_letter.lower() not in word:
                                        matches = False
                                        break
                                    for excluded_pos in excluded_positions:
                                        if word[excluded_pos - 1] == yellow_letter.lower():
                                            matches = False
                                            break
                                    if not matches:
                                        break
                                
                                if matches:
                                    expanded_candidates.add(word)
                                    if len(expanded_candidates) >= 10:
                                        break
                        if len(expanded_candidates) >= 10:
                            break
            
            self.candidate_words = expanded_candidates


def main():
    """Main entry point for command-line usage"""
    solver = WordleSolver()
    solver.solve()


if __name__ == '__main__':
    main()

