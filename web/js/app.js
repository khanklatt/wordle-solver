/**
 * Main Application Logic
 * Requirement 6.1: Web-based UI accessible via browser
 * Requirement 6.4: Allow users to type 5-letter words and submit via Enter key
 * Requirement 6.7: Prevent new word input until all blue squares are processed
 * Requirement 6.9: Allow clicking suggestions to auto-fill guess input
 * Requirement 7.4: Support keyboard navigation
 */

class WordleSolverApp {
    constructor() {
        this.gameBoard = new GameBoard('game-board');
        this.suggestions = new Suggestions('suggestions-list', (word) => this.handleSuggestionClick(word));
        this.wordInput = document.getElementById('word-input');
        this.submitBtn = document.getElementById('submit-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.messageEl = document.getElementById('message');
        this.isProcessing = false;
        this.constraintState = new ConstraintState(); // Maintain all constraints client-side

        this.init();
    }

    init() {
        // Input handling
        this.wordInput.addEventListener('input', (e) => this.handleInput(e));
        this.wordInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Submit button - handles both word submission and feedback submission
        this.submitBtn.addEventListener('click', () => {
            if (this.isProcessing && this.gameBoard.isCurrentRowProcessed()) {
                this.processFeedback();
            } else {
                this.handleSubmit();
            }
        });
        
        // Reset button
        this.resetBtn.addEventListener('click', () => this.handleReset());

        // Initialize ready to play (reset state on first load)
        this.initializeNewGame();

        // Focus input on load - use setTimeout to ensure DOM is fully ready
        setTimeout(() => {
            this.wordInput.focus();
        }, 0);
    }

    /**
     * Initialize a new game (ready to play state)
     */
    initializeNewGame() {
        // Reset game board state
        this.gameBoard.reset();
        this.constraintState.reset(); // Reset all constraints
        this.suggestions.clear();
        this.wordInput.value = '';
        this.wordInput.disabled = false;
        this.submitBtn.disabled = true; // Disabled until 5 letters entered
        this.submitBtn.textContent = 'Enter'; // Reset button text
        this.isProcessing = false;
        this.showMessage('', '');
        
        // Load default guess suggestion
        this.loadDefaultGuess();
    }

    /**
     * Handle input changes
     * Requirement 6.4: Allow users to type 5-letter words
     */
    handleInput(e) {
        const value = e.target.value.toUpperCase().replace(/[^A-Z]/g, '');
        e.target.value = value;

        // Enable/disable submit button based on length
        this.submitBtn.disabled = value.length !== 5 || this.isProcessing || !this.gameBoard.isCurrentRowProcessed();
    }

    /**
     * Handle keyboard events
     * Requirement 6.4: Submit via Enter key
     * Requirement 7.4: Support keyboard navigation
     */
    handleKeyDown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            // If processing feedback (word on board), submit feedback
            if (this.isProcessing && this.gameBoard.isCurrentRowProcessed()) {
                this.processFeedback();
            } 
            // Otherwise, submit new word guess
            else if (this.wordInput.value.length === 5 && !this.submitBtn.disabled && !this.isProcessing) {
                this.handleSubmit();
            }
        } else if (e.key === 'Backspace' && this.wordInput.value.length === 0) {
            // Allow backspace to work normally
        }
    }

    /**
     * Handle suggestion click
     * Requirement 6.9: Allow clicking suggestions to auto-fill guess input
     */
    handleSuggestionClick(word) {
        if (this.isProcessing || !this.gameBoard.isCurrentRowProcessed()) {
            return;
        }

        this.wordInput.value = word;
        this.submitBtn.disabled = false;
        this.wordInput.focus();
    }

    /**
     * Handle form submission
     * Requirement 6.7: Prevent new word input until all blue squares are processed
     */
    async handleSubmit() {
        const word = this.wordInput.value.toUpperCase().trim();

        if (word.length !== 5) {
            this.showMessage('Please enter a 5-letter word', 'error');
            return;
        }

        if (this.isProcessing) {
            return;
        }

        // Set word on board
        if (!this.gameBoard.setWord(word)) {
            this.showMessage('Game board is full', 'error');
            return;
        }

        // Mark as processing - user needs to cycle squares and press Enter
        this.isProcessing = true;
        this.wordInput.disabled = true;
        this.submitBtn.disabled = true;
        this.submitBtn.textContent = 'Processing...';

        // Wait for user to provide feedback by cycling squares
        this.showMessage('Click each blue square to cycle through feedback (blue → yellow → green → grey). Press Enter when done to submit.', 'info');
        
        // Monitor for when all squares are processed to enable submit
        this.updateSubmitButtonState();
    }

    /**
     * Update submit button state based on whether all squares are processed
     */
    updateSubmitButtonState() {
        if (this.isProcessing && this.gameBoard.isCurrentRowProcessed()) {
            // All squares processed, enable submit button
            this.submitBtn.disabled = false;
            this.submitBtn.textContent = 'Submit Feedback';
            this.showMessage('All squares processed. Press Enter or click "Submit Feedback" to continue.', 'info');
        } else if (this.isProcessing) {
            // Still processing squares
            this.submitBtn.disabled = true;
            this.submitBtn.textContent = 'Processing...';
        }
    }

    /**
     * Process feedback after user has cycled all squares and pressed Enter
     */
    async processFeedback() {
        const feedback = this.gameBoard.getFeedback();
        
        if (!feedback) {
            return;
        }

        // Check if all squares are processed (not blue)
        for (let col = 0; col < 5; col++) {
            if (this.gameBoard.feedbackStates[this.gameBoard.getCurrentRow()][col] === 'blue') {
                this.showMessage('Please process all letters first', 'error');
                return;
            }
        }

        // Show loading state
        this.submitBtn.disabled = true;
        this.submitBtn.textContent = 'Submitting...';
        this.suggestions.showLoading();

        try {
            const word = this.gameBoard.currentGuess;
            
            // Add feedback to constraint state
            this.constraintState.addFeedback(word, feedback.greens, feedback.yellows, feedback.greys);
            
            // Get all accumulated constraints
            const constraints = this.constraintState.getConstraints();
            
            // Send all constraints to API (stateless)
            const result = await API.processConstraints(constraints);

            // Display suggestions
            this.suggestions.display(result.suggestions);

            // Check if solved
            if (result.solved || this.constraintState.isSolved()) {
                this.showMessage('🎉 Congratulations! Puzzle solved!', 'success');
                this.wordInput.disabled = true;
                this.submitBtn.disabled = true;
                this.submitBtn.textContent = 'Enter';
                return;
            }

            // Move to next row
            this.gameBoard.nextRow();

            // Clear input and re-enable for next guess
            this.wordInput.value = '';
            this.wordInput.disabled = false;
            this.submitBtn.disabled = true;
            this.submitBtn.textContent = 'Enter';
            this.isProcessing = false;

            // Check if board is full
            if (this.gameBoard.isFull()) {
                this.showMessage('Game board is full. Click "New Game" to start over.', 'info');
                this.wordInput.disabled = true;
            } else {
                this.wordInput.focus();
            }

        } catch (error) {
            this.showMessage(`Error: ${error.message}`, 'error');
            this.wordInput.disabled = false;
            this.submitBtn.disabled = false;
            this.submitBtn.textContent = 'Enter';
            this.isProcessing = false;
        }
    }

    /**
     * Handle reset
     * Requirement 6.11: Provide reset/new game functionality
     */
    async handleReset() {
        try {
            await API.reset();
            this.initializeNewGame();
            this.wordInput.focus();
        } catch (error) {
            this.showMessage(`Error resetting: ${error.message}`, 'error');
        }
    }

    /**
     * Show message to user
     */
    showMessage(text, type = '') {
        this.messageEl.textContent = text;
        this.messageEl.className = `message ${type}`;
        
        if (!text) {
            this.messageEl.style.display = 'none';
        } else {
            this.messageEl.style.display = 'flex';
        }
    }

    /**
     * Load default guess suggestion
     */
    async loadDefaultGuess() {
        try {
            const defaultGuess = await API.getDefaultGuess();
            this.showMessage(`Suggested first guess: ${defaultGuess}`, 'info');
        } catch (error) {
            // Ignore errors, just don't show suggestion
        }
    }
}

// Initialize app when DOM is ready
let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new WordleSolverApp();

    // Monitor for when squares are clicked to update submit button state
    const gameBoardEl = document.getElementById('game-board');
    gameBoardEl.addEventListener('click', (e) => {
        if (e.target.classList.contains('letter-square') && app.isProcessing) {
            // Update submit button state after a short delay to allow state to update
            setTimeout(() => {
                app.updateSubmitButtonState();
            }, 100);
        }
    });
});

