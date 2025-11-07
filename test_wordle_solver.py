"""
Test suite for Wordle Solver
Tests are organized by requirement ID for traceability
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from wordle_solver import WordleSolver


class TestDataLoading(unittest.TestCase):
    """Tests for Requirement 1.1: Load positional letter frequency files"""
    
    def test_load_positional_frequency_files(self):
        """
        Test Case 1.1.1: System loads positional frequency files from /tmp/pos1.txt through /tmp/pos5.txt
        
        Given: Frequency files exist at /tmp/pos1.txt through /tmp/pos5.txt
        When: WordleSolver is initialized
        Then: All five positional frequency files are loaded successfully
        """
        # Create temporary frequency files for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test frequency files in format: "frequency letter"
            for pos in range(1, 6):
                filepath = os.path.join(tmpdir, f'pos{pos}.txt')
                with open(filepath, 'w') as f:
                    f.write('100 a\n90 b\n80 c\n70 d\n60 e\n')
            
            # Temporarily override the path for testing
            solver = WordleSolver(frequency_dir=tmpdir)
            
            # Verify all files were loaded
            self.assertEqual(len(solver.positional_frequencies), 5)
            for pos in range(1, 6):
                self.assertIn(pos, solver.positional_frequencies)
    
    def test_extract_top_n_letters_per_position(self):
        """
        Test Case 1.2.1: System extracts top-N letters per position from frequency files
        
        Requirement 1.2: Extract top-N letters per position from frequency files
        
        Given: Frequency files contain letters ordered by frequency (one per line)
        When: extract_top_letters is called with N=3
        Then: Top 3 letters are extracted for each position
        """
        # Create temporary frequency files for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test frequency files with format: "frequency letter"
            test_data = {
                1: '1132 s\n635 a\n629 i\n584 n\n506 t\n',
                2: '1000 a\n900 o\n800 e\n700 i\n600 r\n',
                3: '1000 a\n900 i\n800 n\n700 o\n600 r\n',
                4: '1000 e\n900 t\n800 s\n700 n\n600 r\n',
                5: '1000 e\n900 y\n800 t\n700 r\n600 s\n'
            }
            
            for pos in range(1, 6):
                filepath = os.path.join(tmpdir, f'pos{pos}.txt')
                with open(filepath, 'w') as f:
                    f.write(test_data[pos])
            
            solver = WordleSolver(frequency_dir=tmpdir)
            
            # Extract top 3 letters for position 1
            top_letters = solver.extract_top_letters(position=1, n=3)
            
            # Verify top 3 letters are extracted correctly
            self.assertEqual(top_letters, ['s', 'a', 'i'])
            
            # Test position 5 with top 3
            top_letters_pos5 = solver.extract_top_letters(position=5, n=3)
            self.assertEqual(top_letters_pos5, ['e', 'y', 't'])
    
    def test_load_valid_wordle_words(self):
        """
        Test Case 1.3.1: System loads valid Wordle words from /tmp/wordle-words.txt
        
        Requirement 1.3: Load valid Wordle words from /tmp/wordle-words.txt
        
        Given: wordle-words.txt file exists with one word per line
        When: WordleSolver is initialized with words_file parameter
        Then: All valid words are loaded into the solver
        """
        # Create temporary word file for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            words_file = os.path.join(tmpdir, 'wordle-words.txt')
            test_words = ['saint', 'slant', 'plant', 'chant', 'grant']
            
            with open(words_file, 'w') as f:
                f.write('\n'.join(test_words))
            
            solver = WordleSolver(words_file=words_file)
            
            # Verify words were loaded
            self.assertEqual(len(solver.valid_words), 5)
            self.assertIn('saint', solver.valid_words)
            self.assertIn('plant', solver.valid_words)
    
    def test_default_first_guess_saint(self):
        """
        Test Case 1.4.1: System initializes with default first guess suggestion of "SAINT"
        
        Requirement 1.4: Initialize with default first guess suggestion of "SAINT"
        
        Given: WordleSolver is initialized
        When: Default first guess is requested
        Then: Default first guess is "SAINT"
        """
        solver = WordleSolver()
        
        # Verify default first guess is "SAINT"
        self.assertEqual(solver.get_default_first_guess(), 'SAINT')


class TestUserInputProcessing(unittest.TestCase):
    """Tests for Requirement 2.x: User Input Processing"""
    
    @patch('builtins.input')
    def test_prompt_user_for_guess_input_case_insensitive(self, mock_input):
        """
        Test Case 2.1.1: System prompts user for guess input (case insensitive)
        
        Requirement 2.1: Prompt user for what guess the user opens with (case insensitive)
        
        Given: System is ready to accept user guess
        When: prompt_for_guess is called
        Then: User is prompted and input is accepted (case insensitive, converted to uppercase)
        """
        mock_input.return_value = 'saint'
        solver = WordleSolver()
        
        # Test with lowercase input
        guess = solver.prompt_for_guess()
        self.assertEqual(guess, 'SAINT')
        
        # Test with uppercase input
        mock_input.return_value = 'PLANT'
        guess = solver.prompt_for_guess()
        self.assertEqual(guess, 'PLANT')
        
        # Test with mixed case input
        mock_input.return_value = 'SlAnT'
        guess = solver.prompt_for_guess()
        self.assertEqual(guess, 'SLANT')
        
        # Verify input was called
        self.assertTrue(mock_input.called)
    
    @patch('builtins.input')
    def test_prompt_user_for_green_letters_feedback(self, mock_input):
        """
        Test Case 2.2.1: System prompts user for green letters feedback
        
        Requirement 2.2: Prompt user for "green" letters feedback from Wordle as string with dots for unknown positions
        
        Given: User has made a guess
        When: prompt_for_green_letters is called
        Then: User is prompted for green letters feedback (e.g., "S..NT" for SAINT -> SLANT)
        """
        mock_input.return_value = 'S..NT'
        solver = WordleSolver()
        
        green_feedback = solver.prompt_for_green_letters()
        self.assertEqual(green_feedback, 'S..NT')
        
        # Test with all dots (no green letters)
        mock_input.return_value = '.....'
        green_feedback = solver.prompt_for_green_letters()
        self.assertEqual(green_feedback, '.....')
        
        # Verify input was called
        self.assertTrue(mock_input.called)
    
    def test_convert_green_letters_to_position_mapping(self):
        """
        Test Case 2.3.1: System converts green letters string into position-to-letter mapping dictionary
        
        Requirement 2.3: Convert green letters string into position-to-letter mapping dictionary
        
        Given: Green letters feedback string (e.g., "S..NT")
        When: convert_green_letters is called
        Then: Returns dictionary mapping position (1-indexed) to letter
        """
        solver = WordleSolver()
        
        # Test with "S..NT" (positions 1=S, 4=N, 5=T)
        result = solver.convert_green_letters('S..NT')
        expected = {1: 'S', 4: 'N', 5: 'T'}
        self.assertEqual(result, expected)
        
        # Test with all dots (no green letters)
        result = solver.convert_green_letters('.....')
        self.assertEqual(result, {})
        
        # Test with all letters (all green)
        result = solver.convert_green_letters('SAINT')
        expected = {1: 'S', 2: 'A', 3: 'I', 4: 'N', 5: 'T'}
        self.assertEqual(result, expected)
    
    @patch('builtins.input')
    def test_prompt_user_for_yellow_letters_input(self, mock_input):
        """
        Test Case 2.4.1: System prompts user for yellow letters input
        
        Requirement 2.4: Prompt user for yellow letters input as string with dots for positional communication
        
        Given: User has entered green letters feedback
        When: prompt_for_yellow_letters is called
        Then: User is prompted for yellow letters feedback (e.g., ".A..." for SAINT -> SLANT)
        """
        mock_input.return_value = '.A...'
        solver = WordleSolver()
        
        yellow_feedback = solver.prompt_for_yellow_letters()
        self.assertEqual(yellow_feedback, '.A...')
        
        # Verify input was called
        self.assertTrue(mock_input.called)
    
    def test_convert_yellow_letters_to_excluded_positions_mapping(self):
        """
        Test Case 2.5.1: System converts yellow letters into letter-to-excluded-positions mapping dictionary
        
        Requirement 2.5: Convert yellow letters into letter-to-excluded-positions mapping dictionary
        
        Given: Yellow letters feedback string (e.g., ".A..." meaning A is in word but not in position 2)
        When: convert_yellow_letters is called
        Then: Returns dictionary mapping letter to set of excluded positions
        """
        solver = WordleSolver()
        
        # Test with ".A..." (A is present but not in position 2)
        result = solver.convert_yellow_letters('.A...')
        expected = {'A': {2}}
        self.assertEqual(result, expected)
        
        # Test with multiple yellow letters
        result = solver.convert_yellow_letters('.A.I.')
        expected = {'A': {2}, 'I': {4}}
        self.assertEqual(result, expected)
        
        # Test with all dots (no yellow letters)
        result = solver.convert_yellow_letters('.....')
        self.assertEqual(result, {})
    
    @patch('builtins.input')
    def test_accept_grey_letters_input_space_separated(self, mock_input):
        """
        Test Case 2.6.1: System accepts grey letters input as space-separated letters
        
        Requirement 2.6: Accept grey letters input as space-separated letters
        
        Given: User has entered yellow letters feedback
        When: prompt_for_grey_letters is called
        Then: User can enter space-separated letters (e.g., "E R T")
        """
        mock_input.return_value = 'E R T'
        solver = WordleSolver()
        
        grey_input = solver.prompt_for_grey_letters()
        self.assertEqual(grey_input, 'E R T')
        
        # Test with single letter
        mock_input.return_value = 'X'
        grey_input = solver.prompt_for_grey_letters()
        self.assertEqual(grey_input, 'X')
        
        # Verify input was called
        self.assertTrue(mock_input.called)
    
    def test_convert_grey_letters_to_excluded_set(self):
        """
        Test Case 2.7.1: System converts grey letters into set of excluded letters
        
        Requirement 2.7: Convert grey letters into set of excluded letters
        
        Given: Grey letters input as space-separated string (e.g., "E R T")
        When: convert_grey_letters is called
        Then: Returns set of excluded letters (uppercase)
        """
        solver = WordleSolver()
        
        # Test with space-separated letters
        result = solver.convert_grey_letters('E R T')
        expected = {'E', 'R', 'T'}
        self.assertEqual(result, expected)
        
        # Test with single letter
        result = solver.convert_grey_letters('X')
        expected = {'X'}
        self.assertEqual(result, expected)
        
        # Test with empty string
        result = solver.convert_grey_letters('')
        self.assertEqual(result, set())
        
        # Test case insensitivity
        result = solver.convert_grey_letters('e r t')
        expected = {'E', 'R', 'T'}
        self.assertEqual(result, expected)


class TestStateManagement(unittest.TestCase):
    """Tests for Requirement 5.2: Maintain minimal state"""
    
    def test_maintain_constraints_state(self):
        """
        Test Case 5.2.1: System maintains minimal state (green/yellow/grey constraints and candidate words)
        
        Requirement 5.2: Maintain minimal state (only green/yellow/grey constraints and candidate words)
        
        Given: WordleSolver is initialized
        When: Constraints are set via methods
        Then: State is maintained in instance variables
        """
        solver = WordleSolver()
        
        # Verify initial state
        self.assertIsInstance(solver.green_constraints, dict)
        self.assertIsInstance(solver.yellow_constraints, dict)
        self.assertIsInstance(solver.grey_constraints, set)
        self.assertIsInstance(solver.candidate_words, set)
        
        # Set constraints
        solver.green_constraints = {1: 'S', 4: 'N', 5: 'T'}
        solver.yellow_constraints = {'A': {2}}
        solver.grey_constraints = {'E', 'R'}
        
        # Verify state is maintained
        self.assertEqual(solver.green_constraints, {1: 'S', 4: 'N', 5: 'T'})
        self.assertEqual(solver.yellow_constraints, {'A': {2}})
        self.assertEqual(solver.grey_constraints, {'E', 'R'})


class TestCLIInterface(unittest.TestCase):
    """Tests for Requirement 4.x: Interactive CLI Interface"""
    
    def test_display_filtered_candidate_words(self):
        """
        Test Case 4.5.1: System displays filtered candidate words after each constraint application
        
        Requirement 4.5: Display filtered candidate words after each constraint application
        Requirement 3.2: Display candidates split into unique letters and repeated letters sections
        
        Given: Candidate words have been filtered
        When: display_candidates is called
        Then: Candidate words are displayed in two sections (unique letters and repeated letters)
        """
        solver = WordleSolver()
        solver.candidate_words = {'saint', 'slant', 'plant', 'briss', 'hello'}
        
        # Capture print output
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            solver.display_candidates()
        
        output = f.getvalue()
        self.assertIn('saint', output.lower())
        self.assertIn('candidate', output.lower())
        # Verify two sections are displayed
        self.assertIn('section 1', output.lower())
        self.assertIn('section 2', output.lower())
        self.assertIn('unique letters', output.lower())
        self.assertIn('repeated letters', output.lower())
        # Verify words are in correct sections
        self.assertIn('briss', output.lower())  # Should be in section 2
        self.assertIn('hello', output.lower())  # Should be in section 2
    
    def test_display_suggested_next_guess(self):
        """
        Test Case 4.6.1: System displays suggested next guess after all constraints are applied
        
        Requirement 4.6: Display suggested next guess after all constraints are applied
        
        Given: Constraints have been applied and next guess is determined
        When: display_suggested_guess is called
        Then: Suggested guess is displayed
        """
        solver = WordleSolver()
        
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            solver.display_suggested_guess('PLANT')
        
        output = f.getvalue()
        self.assertIn('PLANT', output)
        self.assertIn('suggest', output.lower())
    
    @patch('builtins.input')
    def test_interactive_loop_continues_until_solved_or_exit(self, mock_input):
        """
        Test Case 4.7.1: System continues interactive loop until puzzle is solved or user exits
        
        Requirement 4.7: Continue interactive loop until puzzle is solved or user exits
        
        Given: Interactive loop is started
        When: User provides input that solves puzzle (all green) or quits
        Then: Loop exits appropriately
        """
        solver = WordleSolver()
        
        # Test 1: User quits immediately
        mock_input.side_effect = ['quit']
        result = solver.solve()
        self.assertFalse(result)  # User exited
        
        # Test 2: Puzzle solved (all 5 positions green)
        mock_input.side_effect = ['saint', 'SAINT', '.A...', '']  # All green = solved
        result = solver.solve()
        self.assertTrue(result)  # Puzzle solved
    
    def test_handle_invalid_input_gracefully(self):
        """
        Test Case 5.4.1: System handles invalid input gracefully with appropriate error messages
        
        Requirement 5.4: Handle invalid input gracefully with appropriate error messages
        
        Given: User provides invalid input
        When: Input validation methods are called
        Then: Appropriate error messages are returned without crashing
        """
        solver = WordleSolver()
        
        # Test invalid guess length
        result = solver.validate_guess('ABCD')  # Too short
        self.assertFalse(result[0])  # Validation failed
        self.assertIn('error', result[1].lower() or '')
        
        # Test invalid green letters format
        result = solver.validate_green_letters('S..N')  # Wrong length
        self.assertFalse(result[0])
        
        # Test invalid yellow letters format  
        result = solver.validate_yellow_letters('A..')  # Wrong length
        self.assertFalse(result[0])


class TestGuessWordFilterGeneration(unittest.TestCase):
    """Tests for Requirement 3.1: Guess Word Filter Generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.solver = WordleSolver()
        # Use a comprehensive test word set
        self.solver.valid_words = {
            'saint', 'slant', 'plant', 'chant', 'grant', 'crane',
            'plane', 'slate', 'stale', 'steal', 'least', 'teals',
            'slain', 'snail', 'trail', 'train', 'brain', 'grain'
        }
    
    def test_green_letters_fixed_positions_regex(self):
        """
        Test Case 3.1.1: Green letters filtering via regex
        
        Requirement 3.1.1: Green letters: Fixed positions specified by green letters shall be applied via regex
        
        Given: Green constraints specifying fixed letter positions
        When: filter_candidates is called
        Then: Only words matching the fixed positions are included
        """
        # Test: First letter must be S
        self.solver.green_constraints = {1: 'S'}
        self.solver.yellow_constraints = {}
        self.solver.grey_constraints = set()
        
        self.solver.filter_candidates()
        
        # All remaining words must start with S
        for word in self.solver.candidate_words:
            self.assertEqual(word[0].lower(), 's')
        
        # Should include: saint, slant, slate, stale, steal, slain, snail
        expected_words = {'saint', 'slant', 'slate', 'stale', 'steal', 'slain', 'snail'}
        self.assertEqual(self.solver.candidate_words, expected_words)
        
        # Test: Multiple green positions (S at pos 1, T at pos 5)
        self.solver.green_constraints = {1: 'S', 5: 'T'}
        self.solver.filter_candidates()
        
        # All words must start with S and end with T
        for word in self.solver.candidate_words:
            self.assertEqual(word[0].lower(), 's')
            self.assertEqual(word[4].lower(), 't')
        
        # Should include: saint, slant
        self.assertIn('saint', self.solver.candidate_words)
        self.assertIn('slant', self.solver.candidate_words)
        self.assertNotIn('plant', self.solver.candidate_words)  # Doesn't start with S
    
    def test_yellow_letters_included_excluded_positions(self):
        """
        Test Case 3.1.2: Yellow letters filtering via regex
        
        Requirement 3.1.2: Yellow letters included in regex for positions without GREEN,
        but excluded from positions where we've gotten a YELLOW indicator
        
        Given: Yellow constraints specifying letters present but not in specific positions
        When: filter_candidates is called
        Then: Words include yellow letters but not in excluded positions
        """
        # Test: A is present but not in position 2
        self.solver.green_constraints = {}
        self.solver.yellow_constraints = {'A': {2}}  # A not in position 2
        self.solver.grey_constraints = set()
        
        self.solver.filter_candidates()
        
        # All words must contain A, but not in position 2
        for word in self.solver.candidate_words:
            self.assertIn('a', word.lower())
            self.assertNotEqual(word[1].lower(), 'a')  # Position 2 (0-indexed: 1)
        
        # Should include: saint (A at pos 2, but wait - this violates the constraint!)
        # Actually, if A is yellow at position 2, it means A is in the word but NOT at position 2
        # So 'saint' should be excluded (A is at position 2)
        # But 'plant' should be included (A is at position 3)
        self.assertIn('plant', self.solver.candidate_words)
        self.assertNotIn('saint', self.solver.candidate_words)  # A is at position 2
        
        # Test: Multiple yellow letters
        self.solver.yellow_constraints = {'A': {2}, 'L': {1}}  # A not in pos 2, L not in pos 1
        self.solver.filter_candidates()
        
        # All words must contain both A and L, with constraints
        for word in self.solver.candidate_words:
            self.assertIn('a', word.lower())
            self.assertIn('l', word.lower())
            self.assertNotEqual(word[1].lower(), 'a')  # A not in position 2
            self.assertNotEqual(word[0].lower(), 'l')  # L not in position 1
    
    def test_grey_letters_exclusion(self):
        """
        Test Case 3.1.3: Grey letters exclusion
        
        Requirement 3.1.3: Grey letters: Exclude words containing grey letters
        
        Given: Grey constraints specifying excluded letters
        When: filter_candidates is called
        Then: Words containing grey letters are excluded
        """
        # Test: Exclude E and R
        self.solver.green_constraints = {}
        self.solver.yellow_constraints = {}
        self.solver.grey_constraints = {'E', 'R'}
        
        self.solver.filter_candidates()
        
        # No words should contain E or R
        for word in self.solver.candidate_words:
            self.assertNotIn('e', word.lower())
            self.assertNotIn('r', word.lower())
        
        # Should exclude: crane (E), plane (E), slate (E), stale (E), steal (E), least (E), teals (E), trail (R), train (R), brain (R), grain (R), grant (R), chant (no E/R but verify)
        excluded_words = {'crane', 'plane', 'slate', 'stale', 'steal', 'least', 'teals', 'trail', 'train', 'brain', 'grain', 'grant'}
        for word in excluded_words:
            self.assertNotIn(word, self.solver.candidate_words)
        
        # Should include: saint, slant, plant, chant, slain, snail (no E or R)
        included_words = {'saint', 'slant', 'plant', 'chant', 'slain', 'snail'}
        for word in included_words:
            self.assertIn(word, self.solver.candidate_words)
        
        # Test: Combined with green constraints
        self.solver.green_constraints = {1: 'S'}
        self.solver.grey_constraints = {'E', 'R'}
        self.solver.filter_candidates()
        
        # Words must start with S and not contain E or R
        for word in self.solver.candidate_words:
            self.assertEqual(word[0].lower(), 's')
            self.assertNotIn('e', word.lower())
            self.assertNotIn('r', word.lower())
        
        # Should include: saint, slant, slain, snail (all start with S, no E or R)
        self.assertIn('saint', self.solver.candidate_words)
        self.assertIn('slant', self.solver.candidate_words)
        self.assertIn('slain', self.solver.candidate_words)
        self.assertIn('snail', self.solver.candidate_words)
    
    def test_split_candidates_into_unique_and_repeated_letters(self):
        """
        Test Case 3.2.1: System splits candidate words into unique letters and repeated letters sections
        
        Requirement 3.2: Return candidate sets split into two sections - unique letters and repeated letters
        
        Given: Candidate words include both unique-letter words and words with repeated letters
        When: split_candidates_by_letter_uniqueness is called
        Then: Returns two sets - unique_letters_words and repeated_letters_words
        """
        solver = WordleSolver()
        solver.candidate_words = {'brisk', 'briss', 'saint', 'slant', 'hello', 'plant'}
        
        unique_words, repeated_words = solver.split_candidates_by_letter_uniqueness()
        
        # Words with unique letters: brisk, saint, slant, plant
        expected_unique = {'brisk', 'saint', 'slant', 'plant'}
        # Words with repeated letters: briss (double S), hello (double L)
        expected_repeated = {'briss', 'hello'}
        
        self.assertEqual(unique_words, expected_unique)
        self.assertEqual(repeated_words, expected_repeated)
        
        # Verify all words are accounted for
        self.assertEqual(len(unique_words) + len(repeated_words), len(solver.candidate_words))
        
        # Verify no overlap
        self.assertEqual(unique_words & repeated_words, set())
    
    def test_compute_word_score_based_on_positional_frequency(self):
        """
        Test Case 3.5.1: System computes word score based on positional frequency line numbers
        
        Requirement 3.5: Compute word score for each word - lower score is better
        Score is sum of line numbers where letters appear in frequency files for unknown positions
        
        Given: Candidate words and unknown positions
        When: compute_word_scores is called
        Then: Returns words with scores, sorted by score (lowest first)
        """
        import tempfile
        import os
        
        # Create temporary frequency files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create pos1.txt: n at line 1, p at line 6 (to match example)
            pos1_file = os.path.join(tmpdir, 'pos1.txt')
            with open(pos1_file, 'w') as f:
                # Line 1: n, line 6: p (with other letters in between)
                f.write('1000 n\n900 a\n800 i\n700 s\n600 t\n500 p\n')
            
            # Create frequency files for other positions (needed for scoring)
            for pos in range(2, 6):
                pos_file = os.path.join(tmpdir, f'pos{pos}.txt')
                with open(pos_file, 'w') as f:
                    f.write('1000 o\n900 i\n800 s\n700 e\n')  # Common letters for positions 2-5
            
            solver = WordleSolver(frequency_dir=tmpdir)
            solver.candidate_words = {'noise', 'poise'}
            
            # Set up: only position 1 is unknown (positions 2-5 are known)
            # For NOISE: positions 2=O, 3=I, 4=S, 5=E
            # For POISE: positions 2=O, 3=I, 4=S, 5=E
            solver.green_constraints = {2: 'O', 3: 'I', 4: 'S', 5: 'E'}  # Only position 1 is unknown
            
            # Compute scores
            scored_words = solver.compute_word_scores()
            
            # NOISE: N is at line 1 in pos1.txt, so score = 1
            # POISE: P is at line 6 in pos1.txt, so score = 6
            # NOISE should have lower (better) score
            self.assertIsInstance(scored_words, list)
            self.assertEqual(len(scored_words), 2)
            
            # Check that NOISE comes before POISE (lower score first)
            self.assertEqual(scored_words[0][0], 'noise')
            self.assertEqual(scored_words[0][1], 1)  # Score should be 1
            self.assertEqual(scored_words[1][0], 'poise')
            self.assertEqual(scored_words[1][1], 6)  # Score should be 6
    
    def test_prioritize_words_with_most_vowels(self):
        """
        Test Case 3.4.1: System prioritizes words with most vowels in suggestions
        
        Requirement 3.4: Prioritize words that have the most vowels
        
        Given: Set of candidate words with varying vowel counts
        When: get_words_with_most_vowels is called
        Then: Returns words with the highest vowel count
        """
        solver = WordleSolver()
        solver.candidate_words = {'brisk', 'chips', 'clips', 'guise', 'hoise', 'moise', 'poise', 'prism'}
        
        # Get words with most vowels
        vowel_words = solver.get_words_with_most_vowels()
        
        # Words with 3 vowels: guise, hoise, moise, poise
        # Words with 2 vowels: brisk, chips, clips, prism
        expected_vowel_words = {'guise', 'hoise', 'moise', 'poise'}
        self.assertEqual(vowel_words, expected_vowel_words)
        
        # Test with words that have different vowel counts
        solver.candidate_words = {'aeiou', 'aeio', 'aei', 'ae', 'a'}
        vowel_words = solver.get_words_with_most_vowels()
        self.assertEqual(vowel_words, {'aeiou'})  # Should return only the word with 5 vowels
    
    def test_suggest_next_guess_using_vowels_and_scores(self):
        """
        Test Case 3.4-3.5 Integration: System suggests next guess using vowel prioritization and scoring
        
        Given: Candidate words with varying vowels and scores
        When: get_suggested_next_guess is called
        Then: Returns word with most vowels, scored and ranked by positional frequency
        """
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frequency files - for position 1: g at line 1, h at line 2, m at line 3, p at line 4, o at line 5
            pos1_file = os.path.join(tmpdir, 'pos1.txt')
            with open(pos1_file, 'w') as f:
                f.write('1000 g\n900 h\n800 m\n700 p\n600 o\n')
            
            # Create frequency files for other positions
            for pos in range(2, 6):
                pos_file = os.path.join(tmpdir, f'pos{pos}.txt')
                with open(pos_file, 'w') as f:
                    f.write('1000 u\n900 i\n800 s\n700 e\n')
            
            solver = WordleSolver(frequency_dir=tmpdir)
            solver.candidate_words = {'brisk', 'chips', 'clips', 'guise', 'hoise', 'moise', 'poise', 'prism'}
            solver.green_constraints = {}  # All positions unknown
            
            # Get suggested guess (now returns list of scored words)
            scored_words = solver.get_suggested_next_guess()
            
            # Should return list of scored words
            self.assertIsInstance(scored_words, list)
            self.assertGreater(len(scored_words), 0)
            
            # Should contain vowel-rich words (guise, hoise, moise, poise)
            scored_word_set = {word.lower() for word, score in scored_words}
            vowel_words = {'guise', 'hoise', 'moise', 'poise'}
            self.assertTrue(vowel_words.issubset(scored_word_set), 
                          f"Scored words should include all vowel-rich words. Got: {scored_word_set}")
            
            # GUISE should be first (lowest score, G is at line 1)
            self.assertEqual(scored_words[0][0].lower(), 'guise')
            # All words should be sorted by score (lowest first)
            scores = [score for word, score in scored_words]
            self.assertEqual(scores, sorted(scores), "Words should be sorted by score (lowest first)")
    
    def test_display_word_scores_next_to_scored_words(self):
        """
        Test Case 3.5.1.1: System displays word scores next to all scored words
        
        Requirement 3.5.1: Word scores will be shown next to all words that were scored,
        and all scored words will be shown in the suggested next guess
        
        Given: Scored words from vowel prioritization and positional frequency scoring
        When: display_suggested_guess is called with scored words
        Then: All scored words are displayed with their scores
        """
        import tempfile
        import os
        import io
        import sys
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frequency files - for position 1: g at line 1, h at line 2, m at line 3, p at line 4
            pos1_file = os.path.join(tmpdir, 'pos1.txt')
            with open(pos1_file, 'w') as f:
                f.write('1000 g\n900 h\n800 m\n700 p\n')
            
            # Create frequency files for other positions
            for pos in range(2, 6):
                pos_file = os.path.join(tmpdir, f'pos{pos}.txt')
                with open(pos_file, 'w') as f:
                    f.write('1000 u\n900 i\n800 s\n700 e\n')
            
            solver = WordleSolver(frequency_dir=tmpdir)
            solver.candidate_words = {'guise', 'hoise', 'moise', 'poise'}
            solver.green_constraints = {}  # All positions unknown
            
            # Get scored words
            vowel_words = solver.get_words_with_most_vowels()
            original_candidates = solver.candidate_words
            solver.candidate_words = vowel_words
            scored_words = solver.compute_word_scores()
            solver.candidate_words = original_candidates
            
            # Capture output
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            try:
                # Display suggested guess with scored words
                solver.display_suggested_guess(scored_words)
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__
            
            # Verify all scored words are displayed with scores
            # Format should be: "  WORD (score: number)"
            self.assertIn('GUISE', output)
            self.assertIn('HOISE', output)
            self.assertIn('MOISE', output)
            self.assertIn('POISE', output)
            # Check that scores are displayed (format: "WORD (score: number)")
            self.assertIn('(score:', output, "Scores should be displayed with 'score:' label")
            # Verify all 4 words appear with score format
            import re
            # Pattern: WORD (score: number)
            score_pattern = r'(GUISE|HOISE|MOISE|POISE)\s*\(score:\s*\d+\)'
            matches = re.findall(score_pattern, output)
            self.assertEqual(len(matches), 4, f"All 4 scored words should be displayed with scores. Found: {matches}")
    
    def test_iteratively_expand_top_n_letters_when_empty(self):
        """
        Test Case 3.3.1: System iteratively expands top-N letter set when candidate set is empty
        
        Requirement 3.3: Iteratively expand top-N letter set incrementally when candidate set becomes empty
        
        Given: Candidate set is empty after filtering, and we have green constraints (e.g., PLAN for positions 1-4)
        When: expand_candidates_when_empty is called
        Then: System generates candidate words using positional frequencies, skipping excluded letters
        """
        import tempfile
        import os
        
        # Create temporary frequency file for position 5
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create pos5.txt with format: "frequency letter" in order: e, y, a, t, r
            pos5_file = os.path.join(tmpdir, 'pos5.txt')
            with open(pos5_file, 'w') as f:
                f.write('1000 e\n900 y\n800 a\n700 t\n600 r\n')
            
            # Initialize solver with frequency directory
            solver = WordleSolver(frequency_dir=tmpdir)
            
            # Set up valid words including plant, plany, plana
            solver.valid_words = {'plant', 'plany', 'plana', 'saint', 'slant'}
            
            # Set up constraints: PLAN for positions 1-4 (green constraints)
            solver.green_constraints = {1: 'P', 2: 'L', 3: 'A', 4: 'N'}
            solver.yellow_constraints = {}
            solver.grey_constraints = {'E'}  # E is excluded
            
            # Filter candidates - should result in empty set initially
            solver.filter_candidates()
            
            # Verify candidate set is empty (because plant, plany, plana might not match if we filter strictly)
            # Actually, let's check: PLAN + any letter should match if we have plant, plany, plana
            # But if E is grey, plany and plana might be excluded if they contain other issues
            # Let's set up so we know it will be empty, then expand
            
            # Clear candidates to simulate empty set
            solver.candidate_words = set()
            
            # Now expand candidates
            solver.expand_candidates_when_empty()
            
            # Should find words starting with PLAN, checking letters from pos5.txt in order
            # Since E is excluded, should skip 'e' and check 'y', 'a', 't', 'r'
            # Should find 'plant' (P-L-A-N-T) as a valid word
            self.assertGreater(len(solver.candidate_words), 0)
            self.assertIn('plant', solver.candidate_words)
            
            # Verify that excluded letter 'e' was skipped (no words ending with 'e' if E is grey)
            for word in solver.candidate_words:
                if word.startswith('plan'):
                    self.assertNotEqual(word[4].lower(), 'e')  # 5th letter (0-indexed: 4) should not be 'e'


class TestRegexFiltering(unittest.TestCase):
    """Tests for Requirement 5.1: Regex-based filtering"""
    
    def test_use_regex_based_filtering(self):
        """
        Test Case 5.1.1: System uses regex-based filtering for efficient constraint application
        
        Requirement 5.1: Use regex-based filtering for efficient constraint application
        
        Given: Constraints and candidate words
        When: filter_candidates is called
        Then: Words are filtered using regex patterns
        """
        solver = WordleSolver()
        solver.valid_words = {'saint', 'slant', 'plant', 'chant', 'grant', 'crane'}
        
        # Set up constraints
        solver.green_constraints = {1: 'S'}  # First letter must be S
        solver.yellow_constraints = {'A': {2}}  # A is present but not in position 2
        solver.grey_constraints = {'E', 'R'}  # E and R are excluded
        
        # Filter candidates
        solver.filter_candidates()
        
        # Verify filtering worked (saint and slant should remain, others filtered)
        # Note: This is a basic test - full filtering logic will be in requirement 3
        self.assertIsInstance(solver.candidate_words, set)
        # At minimum, words with excluded letters should be removed
        for word in solver.candidate_words:
            self.assertNotIn('e', word.lower())
            self.assertNotIn('r', word.lower())


if __name__ == '__main__':
    unittest.main()

