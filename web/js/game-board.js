/**
 * Game Board Component
 * Requirement 6.2: Display 5x6 grid of letter squares matching NYT interface
 * Requirement 6.5: Display submitted words in blue squares
 * Requirement 6.6: Allow users to cycle letter states: blue → yellow → green → grey → yellow
 * Requirement 6.7: Prevent new word input until all blue squares are processed
 */

class GameBoard {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.rows = 6;
        this.cols = 5;
        this.currentRow = 0;
        this.squares = [];
        this.currentGuess = '';
        this.feedbackStates = []; // Track feedback state for each square
        this.init();
    }

    init() {
        // Create 6 rows x 5 columns grid
        for (let row = 0; row < this.rows; row++) {
            this.squares[row] = [];
            this.feedbackStates[row] = [];
            for (let col = 0; col < this.cols; col++) {
                const square = document.createElement('div');
                square.className = 'letter-square empty';
                square.setAttribute('role', 'gridcell');
                square.setAttribute('aria-label', `Row ${row + 1}, Column ${col + 1}, empty`);
                square.dataset.row = row;
                square.dataset.col = col;
                this.squares[row][col] = square;
                this.feedbackStates[row][col] = null; // null = not set, 'blue', 'yellow', 'green', 'grey'
                this.container.appendChild(square);
            }
        }
    }

    /**
     * Set a word in the current row
     * Requirement 6.5: Display submitted words in blue squares
     */
    setWord(word) {
        if (this.currentRow >= this.rows) {
            return false; // Board is full
        }

        const upperWord = word.toUpperCase().slice(0, 5).padEnd(5, ' ');
        
        for (let col = 0; col < this.cols; col++) {
            const square = this.squares[this.currentRow][col];
            const letter = upperWord[col];
            
            if (letter && letter !== ' ') {
                square.textContent = letter;
                square.className = 'letter-square blue';
                square.setAttribute('aria-label', `Row ${this.currentRow + 1}, Column ${col + 1}, letter ${letter}, blue - click to cycle`);
                this.feedbackStates[this.currentRow][col] = 'blue';
                
                // Add click handler for cycling states
                square.addEventListener('click', () => this.cycleState(this.currentRow, col));
            } else {
                square.textContent = '';
                square.className = 'letter-square empty';
                this.feedbackStates[this.currentRow][col] = null;
            }
        }

        this.currentGuess = word.toUpperCase();
        return true;
    }

    /**
     * Cycle through feedback states: blue → yellow → green → grey → yellow
     * Requirement 6.6: Allow users to cycle letter states
     */
    cycleState(row, col) {
        const square = this.squares[row][col];
        const currentState = this.feedbackStates[row][col];

        if (!currentState || currentState === 'empty') {
            return; // Can't cycle empty squares
        }

        // State cycle: blue → yellow → green → grey → yellow (loops)
        const stateCycle = {
            'blue': 'yellow',
            'yellow': 'green',
            'green': 'grey',
            'grey': 'yellow'
        };

        const newState = stateCycle[currentState];
        this.feedbackStates[row][col] = newState;
        
        square.className = `letter-square ${newState}`;
        const letter = square.textContent;
        square.setAttribute('aria-label', `Row ${row + 1}, Column ${col + 1}, letter ${letter}, ${newState} - click to cycle`);
    }

    /**
     * Check if all squares in current row have been processed (not blue)
     * Requirement 6.7: Prevent new word input until all blue squares are processed
     */
    isCurrentRowProcessed() {
        if (this.currentRow >= this.rows) {
            return true;
        }

        for (let col = 0; col < this.cols; col++) {
            if (this.feedbackStates[this.currentRow][col] === 'blue') {
                return false;
            }
        }
        return true;
    }

    /**
     * Get feedback for current row
     * Returns: {greens: string, yellows: string, greys: string[]}
     * 
     * Important: In Wordle, if a letter is grey, it means that letter is NOT in the word at all.
     * So if a letter is marked as grey anywhere, ALL instances of that letter in the guess
     * should be considered grey (not yellow or green).
     */
    getFeedback() {
        if (this.currentRow >= this.rows) {
            return null;
        }

        let greens = '';
        let yellows = '';
        const greyLettersSet = new Set(); // Use Set to avoid duplicates

        // First pass: identify all letters that are marked as grey
        for (let col = 0; col < this.cols; col++) {
            const state = this.feedbackStates[this.currentRow][col];
            const letter = this.squares[this.currentRow][col].textContent;

            if (state === 'grey' && letter) {
                greyLettersSet.add(letter);
            }
        }

        // Second pass: build greens/yellows strings, but if a letter is in greyLettersSet,
        // treat it as grey everywhere (Wordle rule: if a letter is not in word, it can't be yellow/green)
        for (let col = 0; col < this.cols; col++) {
            const state = this.feedbackStates[this.currentRow][col];
            const letter = this.squares[this.currentRow][col].textContent;

            // If this letter is marked as grey anywhere, treat it as grey here too
            if (letter && greyLettersSet.has(letter)) {
                greens += '.';
                yellows += '.';
            } else if (state === 'green') {
                greens += letter;
                yellows += '.';
            } else if (state === 'yellow') {
                greens += '.';
                yellows += letter;
            } else {
                // Blue (not processed) or empty
                greens += '.';
                yellows += '.';
            }
        }

        // Convert Set to array
        const greys = Array.from(greyLettersSet);

        return { greens, yellows, greys };
    }

    /**
     * Move to next row
     */
    nextRow() {
        if (this.currentRow < this.rows - 1) {
            this.currentRow++;
            this.currentGuess = '';
        }
    }

    /**
     * Reset the board
     * Requirement 6.11: Provide reset/new game functionality
     */
    reset() {
        this.currentRow = 0;
        this.currentGuess = '';
        
        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                const square = this.squares[row][col];
                square.textContent = '';
                square.className = 'letter-square empty';
                square.setAttribute('aria-label', `Row ${row + 1}, Column ${col + 1}, empty`);
                this.feedbackStates[row][col] = null;
                // Remove all event listeners by cloning
                const newSquare = square.cloneNode(true);
                square.parentNode.replaceChild(newSquare, square);
                this.squares[row][col] = newSquare;
            }
        }
    }

    /**
     * Get current row index
     */
    getCurrentRow() {
        return this.currentRow;
    }

    /**
     * Check if board is full
     */
    isFull() {
        return this.currentRow >= this.rows;
    }
}

