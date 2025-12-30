/**
 * API Client for Wordle Solver
 * Requirement 6.1: Web-based UI accessible via browser
 * Requirement 7.2: Respond to API requests within 500ms
 */

const API_BASE_URL = window.location.origin;

class API {
    /**
     * Process constraints and get suggestions (stateless API)
     * Requirement 6.4: Allow users to type 5-letter words and submit
     * Requirement 6.10: Allow words not in wordlist
     * 
     * @param {Object} constraints - Constraint object with greenConstraints, yellowConstraints, greyConstraints
     */
    static async processConstraints(constraints) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(constraints)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to process constraints');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`API Error: ${error.message}`);
        }
    }

    /**
     * Reset the solver state
     * Requirement 6.11: Provide reset/new game functionality
     */
    static async reset() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to reset');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`API Error: ${error.message}`);
        }
    }

    /**
     * Get default first guess
     */
    static async getDefaultGuess() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/default-guess`);
            
            if (!response.ok) {
                throw new Error('Failed to get default guess');
            }

            const data = await response.json();
            return data.guess;
        } catch (error) {
            // Fallback to hardcoded default
            return 'SAINT';
        }
    }
}

