/**
 * Constraint State Manager
 * Maintains all green, yellow, and grey letter constraints across rounds
 * Stateless API design: client maintains all state
 */

class ConstraintState {
    constructor() {
        // Green: position (1-5) -> letter
        this.greenConstraints = {};
        
        // Yellow: letter -> set of excluded positions (1-5)
        this.yellowConstraints = {};
        
        // Grey: set of excluded letters
        this.greyConstraints = new Set();
    }

    /**
     * Add feedback from a guess
     * @param {string} guess - The guessed word
     * @param {string} greens - Green feedback string (e.g., "S..NT")
     * @param {string} yellows - Yellow feedback string (e.g., ".A...")
     * @param {string[]} greys - Array of grey letters
     */
    addFeedback(guess, greens, yellows, greys) {
        const upperGuess = guess.toUpperCase();
        
        // Process green constraints
        for (let i = 0; i < 5; i++) {
            if (greens[i] && greens[i] !== '.') {
                this.greenConstraints[i + 1] = greens[i].toUpperCase();
            }
        }
        
        // Process yellow constraints
        for (let i = 0; i < 5; i++) {
            if (yellows[i] && yellows[i] !== '.') {
                const letter = yellows[i].toUpperCase();
                if (!this.yellowConstraints[letter]) {
                    this.yellowConstraints[letter] = new Set();
                }
                // Yellow means letter is in word but NOT in this position
                this.yellowConstraints[letter].add(i + 1);
            }
        }
        
        // Process grey constraints
        for (const letter of greys) {
            if (letter && letter.length === 1) {
                this.greyConstraints.add(letter.toUpperCase());
            }
        }
    }

    /**
     * Get all constraints in format for API
     * @returns {Object} Constraints object for API
     */
    getConstraints() {
        // Convert green constraints: {1: "S", 3: "I"} -> {"1": "S", "3": "I"}
        const greenConstraints = {};
        for (const [pos, letter] of Object.entries(this.greenConstraints)) {
            greenConstraints[String(pos)] = letter;
        }
        
        // Convert yellow constraints: {"A": Set([2])} -> {"A": [2]}
        const yellowConstraints = {};
        // Use for...in to iterate over object keys, then access the Set directly
        for (const letter in this.yellowConstraints) {
            if (this.yellowConstraints.hasOwnProperty(letter)) {
                const positions = this.yellowConstraints[letter];
                // Handle both Set and Array
                if (positions instanceof Set) {
                    yellowConstraints[letter] = Array.from(positions);
                } else if (Array.isArray(positions)) {
                    yellowConstraints[letter] = positions;
                } else {
                    // Fallback: try to convert
                    yellowConstraints[letter] = Array.from(positions || []);
                }
            }
        }
        
        // Convert grey constraints: Set(["A", "N"]) -> ["A", "N"]
        const greyConstraints = Array.from(this.greyConstraints);
        
        return {
            greenConstraints,
            yellowConstraints,
            greyConstraints
        };
    }

    /**
     * Reset all constraints
     */
    reset() {
        this.greenConstraints = {};
        this.yellowConstraints = {};
        this.greyConstraints = new Set();
    }

    /**
     * Check if puzzle is solved (all 5 positions are green)
     */
    isSolved() {
        return Object.keys(this.greenConstraints).length === 5;
    }
}

