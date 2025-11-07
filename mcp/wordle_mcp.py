"""
MCP Tool for Wordle Solver

Requirement 6.3: Expose WordleSolver as an MCP tool
Requirement 6.3.1: Function named suggest_guess
Requirement 6.3.2: Calls WordleSolver.process_feedback and returns results

This module provides an MCP (Model Context Protocol) interface to the Wordle Solver,
allowing it to be used programmatically by AI assistants and other tools.
"""
import sys
import os

# Add parent directory to path to import wordle_solver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import Tool, start
from wordle_solver import WordleSolver

# Create a single solver instance to reuse across tool calls
solver = WordleSolver()


@Tool("suggest_guess")
def suggest_guess(guess: str, greens: str, yellows: str, greys: list[str]) -> dict:
    """
    Suggest next Wordle guess based on feedback
    
    Requirement 6.3.1: Function named suggest_guess
    Requirement 6.3.2: Calls WordleSolver.process_feedback and returns results
    
    Args:
        guess: The guessed word (e.g., "saint")
        greens: Green letters feedback string with dots (e.g., "..i..")
        yellows: Yellow letters feedback string with dots (e.g., "s....")
        greys: List of excluded letters (e.g., ["a", "n", "t"])
    
    Returns:
        Dictionary containing:
            - candidates: List of candidate words
            - suggestions: List of dicts with "word" and "score" keys
    """
    result = solver.process_feedback(guess, greens, yellows, greys)
    return result


if __name__ == "__main__":
    start()
