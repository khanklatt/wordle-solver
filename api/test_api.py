"""
Test suite for Wordle Solver API
Tests API endpoints for requirements 6.1, 6.4, 6.10, 6.11, 7.2, 7.5, 7.6

Requirement 7.5: System shall maintain all game state (green/yellow/grey constraints) in the client browser
Requirement 7.6: System shall use a stateless API design where the client sends all accumulated constraints with each request
"""
import unittest
import os
import sys
import tempfile
import shutil

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import app
from api.app import app, create_solver


class TestAPIEndpoints(unittest.TestCase):
    """Tests for API endpoints"""

    def setUp(self):
        """Set up test client"""
        self.client = app.test_client()
        self.client.testing = True

    def test_health_endpoint(self):
        """
        Test Case: Health check endpoint returns healthy status
        
        Given: API server is running
        When: GET /api/health is called
        Then: Returns {"status": "healthy"}
        """
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')

    def test_default_guess_endpoint(self):
        """
        Test Case: Default guess endpoint returns SAINT
        
        Given: API server is running
        When: GET /api/default-guess is called
        Then: Returns {"guess": "SAINT"}
        """
        response = self.client.get('/api/default-guess')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['guess'], 'SAINT')

    def test_process_constraints_valid(self):
        """
        Test Case: Process constraints with valid input (stateless API)
        
        Requirement 6.4: Allow users to type 5-letter words and submit
        Requirement 6.10: Allow words not in wordlist
        Requirement 7.6: Stateless API design - client sends all constraints
        
        Given: Valid constraint data
        When: POST /api/process is called with valid constraints
        Then: Returns candidates and suggestions
        """
        response = self.client.post('/api/process', json={
            'greenConstraints': {},
            'yellowConstraints': {},
            'greyConstraints': []
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('candidates', data)
        self.assertIn('suggestions', data)
        self.assertIn('solved', data)
        self.assertIsInstance(data['candidates'], list)
        self.assertIsInstance(data['suggestions'], list)
        self.assertGreater(len(data['suggestions']), 0)  # Should have suggestions

    def test_process_constraints_with_grey_letters(self):
        """
        Test Case: Process constraints with grey letters (stateless API)
        
        Requirement 7.6: Stateless API design
        
        Given: Constraints with grey letters (e.g., SAINT all grey)
        When: POST /api/process is called
        Then: Returns candidates and suggestions excluding words with grey letters
        """
        response = self.client.post('/api/process', json={
            'greenConstraints': {},
            'yellowConstraints': {},
            'greyConstraints': ['S', 'A', 'I', 'N', 'T']
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('candidates', data)
        self.assertIn('suggestions', data)
        
        # Verify no suggestions contain grey letters
        for suggestion in data['suggestions']:
            word = suggestion['word'].upper()
            self.assertNotIn('S', word)
            self.assertNotIn('A', word)
            self.assertNotIn('I', word)
            self.assertNotIn('N', word)
            self.assertNotIn('T', word)

    def test_process_constraints_missing_fields(self):
        """
        Test Case: Process constraints with missing fields (stateless API)
        
        Requirement 7.6: Stateless API design
        
        Given: Request with missing constraint fields
        When: POST /api/process is called
        Then: Uses empty defaults and returns successfully (API is lenient)
        """
        # Missing all fields - should use defaults
        response = self.client.post('/api/process', json={})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('candidates', data)
        self.assertIn('suggestions', data)

    def test_reset_endpoint(self):
        """
        Test Case: Reset endpoint (stateless API - no-op but kept for compatibility)
        
        Requirement 6.11: Provide reset/new game functionality
        Requirement 7.6: Stateless API design - no server state to reset
        
        Given: Stateless API
        When: POST /api/reset is called
        Then: Returns success status (no-op for stateless API)
        """
        # Reset should always succeed (no state to reset in stateless API)
        response = self.client.post('/api/reset')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'reset')

    def test_process_constraints_solves_puzzle(self):
        """
        Test Case: Process constraints that solve puzzle (stateless API)
        
        Requirement 7.6: Stateless API design
        
        Given: All 5 positions are green
        When: POST /api/process is called with all green constraints
        Then: Returns solved=true
        """
        response = self.client.post('/api/process', json={
            'greenConstraints': {'1': 'S', '2': 'A', '3': 'I', '4': 'N', '5': 'T'},
            'yellowConstraints': {},
            'greyConstraints': []
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['solved'])
    
    def test_process_constraints_with_green_and_yellow(self):
        """
        Test Case: Process constraints with green and yellow letters (stateless API)
        
        Requirement 7.6: Stateless API design
        
        Given: Constraints with green and yellow letters
        When: POST /api/process is called
        Then: Returns filtered candidates and suggestions
        """
        response = self.client.post('/api/process', json={
            'greenConstraints': {'3': 'I'},  # I in position 3
            'yellowConstraints': {'S': [1]},  # S is in word but not position 1
            'greyConstraints': ['A', 'N', 'T']
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('candidates', data)
        self.assertIn('suggestions', data)
        
        # Verify suggestions match constraints
        for suggestion in data['suggestions']:
            word = suggestion['word'].upper()
            # Should have I in position 3 (0-indexed: 2)
            self.assertEqual(word[2], 'I')
            # Should contain S but not in position 1 (0-indexed: 0)
            self.assertIn('S', word)
            self.assertNotEqual(word[0], 'S')
            # Should not contain A, N, T
            self.assertNotIn('A', word)
            self.assertNotIn('N', word)
            self.assertNotIn('T', word)
    
    def test_process_constraints_accumulation_simulation(self):
        """
        Test Case: Simulate constraint accumulation across rounds (stateless API)
        
        Requirement 7.5: Client maintains all constraint state
        Requirement 7.6: Stateless API design
        
        Given: Multiple rounds of constraints (simulating client accumulation)
        When: POST /api/process is called with accumulated constraints
        Then: Returns correct candidates respecting all constraints
        """
        # Round 1: SAINT all grey
        response1 = self.client.post('/api/process', json={
            'greenConstraints': {},
            'yellowConstraints': {},
            'greyConstraints': ['S', 'A', 'I', 'N', 'T']
        })
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        
        # Round 2: CRUEL with some feedback, accumulated with Round 1 greys
        response2 = self.client.post('/api/process', json={
            'greenConstraints': {'1': 'C'},  # C in position 1
            'yellowConstraints': {'R': [2]},  # R in word but not position 2
            'greyConstraints': ['S', 'A', 'I', 'N', 'T', 'U', 'E', 'L']  # All accumulated greys
        })
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        
        # Verify suggestions don't contain any grey letters from both rounds
        for suggestion in data2['suggestions']:
            word = suggestion['word'].upper()
            # Should start with C
            self.assertEqual(word[0], 'C')
            # Should contain R but not in position 2
            self.assertIn('R', word)
            self.assertNotEqual(word[1], 'R')
            # Should not contain any grey letters
            grey_letters = ['S', 'A', 'I', 'N', 'T', 'U', 'E', 'L']
            for grey in grey_letters:
                self.assertNotIn(grey, word, f"Word {word} should not contain grey letter {grey}")
    
    def test_bug_scenario_saint_then_farce(self):
        """
        Test Case: Bug fix - FARCE should not appear after SAINT all grey
        
        Requirement 7.5: Client maintains all constraint state
        Requirement 7.6: Stateless API design
        
        Given: SAINT played with all letters grey, then CRUEL played
        When: POST /api/process is called with accumulated constraints
        Then: FARCE should NOT be in suggestions (contains A which is grey)
        """
        # Simulate: SAINT all grey, then CRUEL with some feedback
        # Client accumulates: greys = ['S', 'A', 'I', 'N', 'T', 'U', 'E', 'L']
        response = self.client.post('/api/process', json={
            'greenConstraints': {'1': 'C'},  # C in position 1 from CRUEL
            'yellowConstraints': {'R': [2]},  # R in word but not position 2
            'greyConstraints': ['S', 'A', 'I', 'N', 'T', 'U', 'E', 'L']  # All accumulated
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # FARCE should NOT be in suggestions (contains A which is grey)
        suggestion_words = [s['word'].upper() for s in data['suggestions']]
        self.assertNotIn('FARCE', suggestion_words, 
                        "FARCE should not be suggested - it contains 'A' which is grey")
        
        # Verify no suggestions contain grey letters
        for suggestion in data['suggestions']:
            word = suggestion['word'].upper()
            for grey in ['S', 'A', 'I', 'N', 'T', 'U', 'E', 'L']:
                self.assertNotIn(grey, word, 
                               f"Word {word} should not contain grey letter {grey}")


if __name__ == '__main__':
    unittest.main()

