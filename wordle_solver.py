"""
Wordle Solver - Interactive CLI tool for solving Wordle puzzles

This module provides an interactive command-line tool that helps users solve Wordle puzzles
by analyzing letter frequencies and filtering candidate words based on user feedback.

Example usage:
    >>> solver = WordleSolver()
    >>> solver.solve()

The solver requires:
    - Positional frequency files: ./lib/pos1.txt through ./lib/pos5.txt
    - Valid word list: ./lib/wordle-words.txt

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
    MAX_EXPANDED_CANDIDATES = 10
    MAX_LETTERS_PER_POSITION_FOR_EXPANSION = 5
    
    def __init__(self, frequency_dir: Optional[str] = None, words_file: Optional[str] = None):
        """
        Initialize Wordle Solver
        
        Requirement 1.1: Load positional letter frequency files from ./lib/pos1.txt through ./lib/pos5.txt
        Requirement 1.3: Load valid Wordle words from ./lib/wordle-words.txt
        
        Args:
            frequency_dir: Directory containing positional frequency files (default: ./lib relative to project root)
            words_file: Path to file containing valid Wordle words (default: ./lib/wordle-words.txt relative to project root)
        
        Raises:
            IOError: If files cannot be read (with clear error message)
        """
        # Get project root directory (directory containing this file)
        # Since wordle_solver.py is in the project root, __file__'s directory is the project root
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Set default paths relative to project root
        if frequency_dir is None:
            frequency_dir = os.path.join(project_root, 'lib')
        if words_file is None:
            words_file = os.path.join(project_root, 'lib', 'wordle-words.txt')
        self.positional_frequencies: Dict[int, str] = {}
        self.valid_words: Set[str] = set()
        
        # Load frequency files for positions 1-5
        for pos in range(1, self.WORD_LENGTH + 1):
            filepath = os.path.join(frequency_dir, f'pos{pos}.txt')
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        self.positional_frequencies[pos] = f.read()
                except IOError as e:
                    raise IOError(f"Failed to load frequency file {filepath}: {e}") from e
        
        # Load valid Wordle words
        if os.path.exists(words_file):
            try:
                with open(words_file, 'r') as f:
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
        Get suggested next guess using positional frequency scoring
        
        Requirement 3.5: Compute word score for all suggested words (not just ones with most vowels)
        Words are grouped by score, with lowest scores shown first
        Requirement 3.5.1: Return all scored words for display
        
        Returns:
            List of (word, score) tuples sorted by score (lowest first), or None if no candidates
        """
        if not self.candidate_words:
            return None
        
        # Requirement 3.5: Score all candidate words
        scored_words = self.compute_word_scores(candidate_words=self.candidate_words)
        
        if scored_words:
            # Requirement 3.5.1: Return all scored words, grouped by score (lowest first)
            return scored_words
        
        # Fallback: create scored list from all candidates with score 0
        return [(word, 0) for word in sorted(self.candidate_words)]
    
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
    
    def normalize_grey_letters(self, grey_string: str) -> str:
        """
        Normalize grey letters input - extract valid single letters, ignore invalid entries
        
        Stateless design: accepts any input and normalizes it rather than rejecting.
        
        Args:
            grey_string: Grey letters input string (space-separated or any format)
        
        Returns:
            Normalized grey string (space-separated valid single letters, uppercase)
        """
        if not grey_string:
            return ""
        # Extract all single alphabetic characters (ignore multi-char, numbers, etc.)
        letters = []
        for item in str(grey_string).split():
            item = item.strip().upper()
            # Only include single alphabetic characters
            if len(item) == 1 and item.isalpha():
                letters.append(item)
        return ' '.join(letters)
    
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
    
    def display_candidates(self) -> None:
        """
        Display filtered candidate words after each constraint application
        
        Requirement 4.5: Display filtered candidate words after each constraint application
        Requirement 5.3: Provide clear, human-readable prompts and feedback messages
        """
        if not self.candidate_words:
            print("No candidate words found.")
            return
        
        print(f"\nFound {len(self.candidate_words)} candidate word(s):")
        
        # Display candidates as sorted list
        sorted_candidates = sorted(self.candidate_words)
        for i in range(0, len(sorted_candidates), self.WORDS_PER_LINE):
            line_words = sorted_candidates[i:i+self.WORDS_PER_LINE]
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
    
    def normalize_guess(self, guess: str) -> str:
        """
        Normalize guess input - extract alphabetic characters and pad/truncate to WORD_LENGTH
        
        Stateless design: accepts any input and normalizes it rather than rejecting.
        
        Args:
            guess: Guess word to normalize
            
        Returns:
            Normalized guess string (uppercase, WORD_LENGTH characters)
        """
        if not guess:
            return 'X' * self.WORD_LENGTH  # Pad with X if empty
        # Extract only alphabetic characters
        guess = ''.join(c for c in str(guess).strip().upper() if c.isalpha())
        # Pad or truncate to WORD_LENGTH
        if len(guess) < self.WORD_LENGTH:
            return guess + 'X' * (self.WORD_LENGTH - len(guess))
        elif len(guess) > self.WORD_LENGTH:
            return guess[:self.WORD_LENGTH]
        return guess
    
    def normalize_green_letters(self, green_string: str) -> str:
        """
        Normalize green letters input - pad/truncate to WORD_LENGTH, filter invalid chars
        
        Stateless design: accepts any input and normalizes it rather than rejecting.
        
        Args:
            green_string: Green letters feedback string
            
        Returns:
            Normalized green string (uppercase, WORD_LENGTH characters, letters and dots only)
        """
        if not green_string:
            return '.' * self.WORD_LENGTH
        # Filter to letters and dots only, uppercase
        normalized = ''.join(c.upper() if c.isalpha() else '.' if c == '.' else '.' 
                            for c in str(green_string).strip())
        # Pad or truncate to WORD_LENGTH
        if len(normalized) < self.WORD_LENGTH:
            return normalized + '.' * (self.WORD_LENGTH - len(normalized))
        elif len(normalized) > self.WORD_LENGTH:
            return normalized[:self.WORD_LENGTH]
        return normalized
    
    def normalize_yellow_letters(self, yellow_string: str) -> str:
        """
        Normalize yellow letters input - pad/truncate to WORD_LENGTH, filter invalid chars
        
        Stateless design: accepts any input and normalizes it rather than rejecting.
        
        Args:
            yellow_string: Yellow letters feedback string
            
        Returns:
            Normalized yellow string (uppercase, WORD_LENGTH characters, letters and dots only)
        """
        if not yellow_string:
            return '.' * self.WORD_LENGTH
        # Filter to letters and dots only, uppercase
        normalized = ''.join(c.upper() if c.isalpha() else '.' if c == '.' else '.' 
                            for c in str(yellow_string).strip())
        # Pad or truncate to WORD_LENGTH
        if len(normalized) < self.WORD_LENGTH:
            return normalized + '.' * (self.WORD_LENGTH - len(normalized))
        elif len(normalized) > self.WORD_LENGTH:
            return normalized[:self.WORD_LENGTH]
        return normalized
    
    def _prompt_with_normalization(
        self,
        prompt_func: Callable[[], str],
        normalize_func: Callable[[str], str]
    ) -> Optional[str]:
        """
        Generic prompt loop with normalization and quit handling
        
        Stateless design: normalizes input rather than rejecting invalid formats.
        
        Args:
            prompt_func: Function that prompts user and returns input string
            normalize_func: Function that normalizes input to valid format
        
        Returns:
            Normalized input string, or None if user quits
        """
        while True:
            try:
                user_input = prompt_func()
                if user_input.upper().strip() == 'QUIT':
                    print("Exiting Wordle Solver. Goodbye!")
                    return None
                
                # Normalize input (never reject, always normalize)
                normalized = normalize_func(user_input)
                return normalized
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
            
            # Requirement 4.1: Prompt for guess (normalize, don't validate)
            guess = self._prompt_with_normalization(
                self.prompt_for_guess,
                self.normalize_guess
            )
            if guess is None:
                return False
            
            # Requirement 4.2: Prompt for green letters (normalize, don't validate)
            green_feedback = self._prompt_with_normalization(
                self.prompt_for_green_letters,
                self.normalize_green_letters
            )
            if green_feedback is None:
                return False
            
            # Check if puzzle is solved (all positions are green)
            # Note: We check after process_feedback which merges constraints
            # But we need to check the new green feedback specifically
            new_green_constraints = self.convert_green_letters(green_feedback)
            if len(new_green_constraints) == self.WORD_LENGTH:
                # Update constraints and check
                self.green_constraints.update(new_green_constraints)
                if len(self.green_constraints) == self.WORD_LENGTH:
                    print("\n🎉 Congratulations! Puzzle solved!")
                    return True
            
            # Requirement 4.3: Prompt for yellow letters (normalize, don't validate)
            yellow_feedback = self._prompt_with_normalization(
                self.prompt_for_yellow_letters,
                self.normalize_yellow_letters
            )
            if yellow_feedback is None:
                return False
            
            # Requirement 4.4: Prompt for grey letters (normalize, don't validate)
            grey_input = self._prompt_with_normalization(
                self.prompt_for_grey_letters,
                self.normalize_grey_letters
            )
            if grey_input is None:
                return False
            
            # Process feedback using the refactored method (maintains consistency)
            # Convert grey input to list format for process_feedback
            # Note: grey_input is already normalized (space-separated valid letters)
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
    
    def apply_constraints(
        self,
        green_constraints: Dict[int, str],
        yellow_constraints: Dict[str, Set[int]],
        grey_constraints: Set[str]
    ) -> Dict[str, Any]:
        """
        Apply constraints directly and return candidates and suggestions (stateless API)
        
        Stateless version: accepts all constraints at once rather than accumulating.
        This method is used by the web API to process constraints without requiring a guess.
        
        Args:
            green_constraints: Dict mapping position (1-indexed) to letter
            yellow_constraints: Dict mapping letter to set of excluded positions (1-indexed)
            grey_constraints: Set of excluded letters
        
        Returns:
            Dictionary containing:
                - candidates: List of candidate words (strings)
                - suggestions: List of dictionaries with "word" and "score" keys
        """
        # Reset and apply constraints directly
        self.green_constraints = green_constraints.copy()
        self.yellow_constraints = {k: v.copy() for k, v in yellow_constraints.items()}
        self.grey_constraints = grey_constraints.copy()
        
        # Filter candidates
        self.filter_candidates()
        
        # Get candidate words as sorted list
        candidates = sorted(self.candidate_words)
        
        # Get suggested guesses with scores
        scored_words = self.get_suggested_next_guess()
        
        # Format suggestions as list of dicts
        suggestions = []
        if scored_words:
            for word, score in scored_words:
                suggestions.append({"word": word.upper(), "score": score})
        
        return {
            "candidates": candidates,
            "suggestions": suggestions
        }
    
    def process_feedback(
        self,
        guess: str,
        greens: str,
        yellows: str,
        greys: List[str]
    ) -> Dict[str, Any]:
        """
        Process Wordle feedback and return candidates and suggestions
        
        This method processes feedback without user interaction, maintaining the same
        core logic as the interactive solve() method. It merges constraints across
        rounds to ensure discoveries from previous rounds are applied in future rounds.
        
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
        
        Raises:
            ValueError: If input parameters are invalid
        """
        # Normalize inputs - be flexible about format
        # Convert guess to string and normalize - truncate or pad to WORD_LENGTH
        if not guess:
            guess = ""
        guess = str(guess).strip().upper()
        # Only keep alphabetic characters
        guess = ''.join(c for c in guess if c.isalpha())
        # Truncate or pad to WORD_LENGTH
        if len(guess) < self.WORD_LENGTH:
            guess = guess + 'X' * (self.WORD_LENGTH - len(guess))  # Pad with X (will be filtered out)
        elif len(guess) > self.WORD_LENGTH:
            guess = guess[:self.WORD_LENGTH]
        
        # Normalize greens - pad with dots if shorter, truncate if longer
        if not greens:
            greens = ""
        greens = str(greens).strip().upper()
        if len(greens) < self.WORD_LENGTH:
            greens = greens + '.' * (self.WORD_LENGTH - len(greens))
        elif len(greens) > self.WORD_LENGTH:
            greens = greens[:self.WORD_LENGTH]
        
        # Normalize yellows - pad with dots if shorter, truncate if longer
        if not yellows:
            yellows = ""
        yellows = str(yellows).strip().upper()
        if len(yellows) < self.WORD_LENGTH:
            yellows = yellows + '.' * (self.WORD_LENGTH - len(yellows))
        elif len(yellows) > self.WORD_LENGTH:
            yellows = yellows[:self.WORD_LENGTH]
        
        # Normalize greys - filter to valid letters only
        if not isinstance(greys, list):
            greys = []
        greys_upper = []
        for grey in greys:
            if isinstance(grey, str) and len(grey) == 1 and grey.isalpha():
                greys_upper.append(grey.upper())
            elif isinstance(grey, str) and grey.strip():
                # Try to extract single letter from string
                cleaned = grey.strip().upper()
                if len(cleaned) == 1 and cleaned.isalpha():
                    greys_upper.append(cleaned)
        
        # Use normalized values (already upper case)
        guess_upper = guess
        greens_upper = greens
        yellows_upper = yellows
        
        # Update constraints based on feedback - MERGE with existing constraints
        new_green_constraints = self.convert_green_letters(greens_upper)
        self.green_constraints.update(new_green_constraints)
        
        new_yellow_constraints = self.convert_yellow_letters(yellows_upper)
        for letter, excluded_positions in new_yellow_constraints.items():
            if letter in self.yellow_constraints:
                self.yellow_constraints[letter].update(excluded_positions)
            else:
                self.yellow_constraints[letter] = excluded_positions.copy()
        
        self.grey_constraints.update(greys_upper)
        
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
        
        return {
            "candidates": candidates,
            "suggestions": suggestions
        }
    
    def _word_matches_yellow_constraints(self, word: str) -> bool:
        """
        Check if word satisfies all yellow letter constraints
        
        Args:
            word: Word to check (lowercase)
            
        Returns:
            True if word satisfies all yellow constraints, False otherwise
        """
        for yellow_letter, excluded_positions in self.yellow_constraints.items():
            if yellow_letter.lower() not in word:
                return False
            for excluded_pos in excluded_positions:
                if word[excluded_pos - 1] == yellow_letter.lower():
                    return False
        return True
    
    def _build_position_pattern(self, pos: int, green_letter: Optional[str], excluded_letters: Set[str]) -> str:
        """
        Build regex pattern for a single position
        
        Args:
            pos: Position number (1-indexed)
            green_letter: Fixed letter for this position (if any)
            excluded_letters: Set of letters to exclude from this position
            
        Returns:
            Regex pattern string for this position
        """
        if green_letter:
            return green_letter.lower()
        if excluded_letters:
            excluded_chars = ''.join(sorted(excluded_letters))
            return f'[^{excluded_chars}]'
        return '[a-z]'
    
    def _filter_grey_letters(self, candidates: Set[str]) -> Set[str]:
        """
        Filter out words containing grey letters
        
        Args:
            candidates: Set of candidate words to filter
            
        Returns:
            Filtered set of candidates without grey letters
        """
        if not self.grey_constraints:
            return candidates
        grey_pattern = '|'.join(self.grey_constraints)
        return {w for w in candidates if not re.search(grey_pattern, w, re.IGNORECASE)}
    
    def _build_regex_pattern(self) -> Tuple[List[str], Set[str]]:
        """
        Build regex pattern for all positions based on green and yellow constraints
        
        Returns:
            Tuple of (regex_pattern_list, yellow_letters_to_include_set)
        """
        regex_pattern = [''] * self.WORD_LENGTH
        
        for pos, letter in self.green_constraints.items():
            regex_pattern[pos - 1] = letter.lower()
        
        yellow_letters_to_include = set()
        position_exclusions: Dict[int, Set[str]] = {}
        
        for letter, excluded_positions in self.yellow_constraints.items():
            yellow_letters_to_include.add(letter.lower())
            for pos in excluded_positions:
                if not regex_pattern[pos - 1]:
                    if pos not in position_exclusions:
                        position_exclusions[pos] = set()
                    position_exclusions[pos].add(letter.lower())
        
        for i in range(self.WORD_LENGTH):
            if regex_pattern[i]:
                continue
            excluded = position_exclusions.get(i + 1, set())
            regex_pattern[i] = self._build_position_pattern(i + 1, None, excluded)
        
        return regex_pattern, yellow_letters_to_include
    
    def _apply_regex_filter(self, candidates: Set[str], regex_pattern: List[str]) -> Set[str]:
        """
        Apply regex pattern to filter candidates
        
        Args:
            candidates: Set of candidate words
            regex_pattern: List of regex patterns for each position
            
        Returns:
            Filtered set of candidates matching the regex pattern
        """
        pattern = '^' + ''.join(regex_pattern) + '$'
        return {w for w in candidates if re.match(pattern, w)}
    
    def _verify_yellow_letters(self, candidates: Set[str], yellow_letters_to_include: Set[str]) -> Set[str]:
        """
        Verify that candidates contain all required yellow letters
        
        Args:
            candidates: Set of candidate words
            yellow_letters_to_include: Set of yellow letters that must be present
            
        Returns:
            Filtered set of candidates containing all required yellow letters
        """
        if not yellow_letters_to_include:
            return candidates
        
        final_candidates = set()
        for word in candidates:
            word_letters = set(word.lower())
            if yellow_letters_to_include.issubset(word_letters):
                final_candidates.add(word)
        return final_candidates
    
    def filter_candidates(self) -> None:
        """
        Filter candidate words using regex-based constraints
        
        Requirement 5.1: Use regex-based filtering for efficient constraint application
        Requirement 3.1.1: Green letters: Fixed positions specified by green letters shall be applied via regex
        Requirement 3.1.2: Yellow letters: Included in regex for positions without GREEN, excluded from YELLOW positions
        Requirement 3.1.3: Grey letters: Exclude words containing grey letters
        
        This method applies all constraints to filter the candidate word set.
        
        Example:
            Given constraints:
            - Green: position 3 = 'I' (..i..)
            - Yellow: 'S' excluded from position 1 (s....)
            - Grey: ['A', 'N', 'T']
            
            Input: valid_words = {'saint', 'guise', 'poise', 'noise'}
            After filtering: candidate_words = {'guise', 'poise', 'noise'}
            (saint excluded due to grey letters A, N, T)
        """
        if not self.valid_words:
            self.candidate_words = set()
            return
        
        candidates = self.valid_words.copy()
        candidates = self._filter_grey_letters(candidates)
        regex_pattern, yellow_letters_to_include = self._build_regex_pattern()
        regex_candidates = self._apply_regex_filter(candidates, regex_pattern)
        regex_candidates = self._verify_yellow_letters(regex_candidates, yellow_letters_to_include)
        
        self.candidate_words = regex_candidates
        
        if not self.candidate_words:
            self.expand_candidates_when_empty()
    
    def _validate_expanded_candidate(self, word: str) -> bool:
        """
        Validate that an expanded candidate word matches all constraints
        
        Args:
            word: Word to validate (lowercase)
            
        Returns:
            True if word matches all constraints, False otherwise
        """
        if any(grey_letter.lower() in word for grey_letter in self.grey_constraints):
            return False
        return self._word_matches_yellow_constraints(word)
    
    def _expand_single_unfixed_position(
        self, 
        base_word: List[str], 
        unfixed_pos: int, 
        position_letters: Dict[int, List[str]]
    ) -> Set[str]:
        """
        Expand candidates when only one position is unfixed
        
        Args:
            base_word: Base word pattern with fixed positions filled
            unfixed_pos: Position number that is unfixed (1-indexed)
            position_letters: Dictionary mapping position to available letters
            
        Returns:
            Set of valid expanded candidate words
        """
        expanded_candidates = set()
        for letter in position_letters[unfixed_pos]:
            candidate = base_word.copy()
            candidate[unfixed_pos - 1] = letter
            word = ''.join(candidate)
            if word in self.valid_words and self._validate_expanded_candidate(word):
                expanded_candidates.add(word)
                if len(expanded_candidates) >= self.MAX_EXPANDED_CANDIDATES:
                    break
        return expanded_candidates
    
    def _expand_multiple_unfixed_positions(
        self,
        base_word: List[str],
        unfixed_positions: List[int],
        position_letters: Dict[int, List[str]]
    ) -> Set[str]:
        """
        Expand candidates when multiple positions are unfixed
        
        Args:
            base_word: Base word pattern with fixed positions filled
            unfixed_positions: List of unfixed position numbers (1-indexed)
            position_letters: Dictionary mapping position to available letters
            
        Returns:
            Set of valid expanded candidate words
        """
        expanded_candidates = set()
        if not unfixed_positions:
            return expanded_candidates
        
        pos = unfixed_positions[0]
        for letter in position_letters[pos][:self.MAX_LETTERS_PER_POSITION_FOR_EXPANSION]:
            candidate = base_word.copy()
            candidate[pos - 1] = letter
            partial_word = ''.join(c if c else '.' for c in candidate)
            pattern = '^' + partial_word.replace('.', '[a-z]') + '$'
            
            for word in self.valid_words:
                if re.match(pattern, word) and self._validate_expanded_candidate(word):
                    expanded_candidates.add(word)
                    if len(expanded_candidates) >= self.MAX_EXPANDED_CANDIDATES:
                        break
            if len(expanded_candidates) >= self.MAX_EXPANDED_CANDIDATES:
                break
        
        return expanded_candidates
    
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
        
        Example:
            Given:
            - Green constraints: {1: 'P', 2: 'L', 3: 'A', 4: 'N'} (PLAN fixed)
            - Grey constraints: {'E'}
            - pos5.txt contains: e, y, a, t, r (in frequency order)
            
            Process:
            1. Unfixed position: 5
            2. Try 'y' from pos5.txt -> 'plany' (if valid word)
            3. Try 'a' from pos5.txt -> 'plana' (if valid word)
            4. Try 't' from pos5.txt -> 'plant' (valid word, added to candidates)
            5. Stop after finding MAX_EXPANDED_CANDIDATES words
        """
        if not self.candidate_words and self.valid_words:
            fixed_positions = set(self.green_constraints.keys())
            unfixed_positions = [pos for pos in range(1, self.WORD_LENGTH + 1) if pos not in fixed_positions]
            
            if not unfixed_positions:
                return
            
            base_word = [''] * self.WORD_LENGTH
            for pos, letter in self.green_constraints.items():
                base_word[pos - 1] = letter.lower()
            
            position_letters: Dict[int, List[str]] = {}
            for pos in unfixed_positions:
                letters = self.extract_top_letters(pos, n=self.MAX_LETTERS_IN_ALPHABET)
                filtered_letters = [l for l in letters if l.upper() not in self.grey_constraints]
                position_letters[pos] = filtered_letters
            if len(unfixed_positions) == 1:
                expanded_candidates = self._expand_single_unfixed_position(
                    base_word, unfixed_positions[0], position_letters
                )
            else:
                expanded_candidates = self._expand_multiple_unfixed_positions(
                    base_word, unfixed_positions, position_letters
                )
            
            self.candidate_words = expanded_candidates


def main():
    """Main entry point for command-line usage"""
    solver = WordleSolver()
    solver.solve()


if __name__ == '__main__':
    main()

