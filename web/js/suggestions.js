/**
 * Suggestions Sidebar Component
 * Requirement 6.8: Display word suggestions in sidebar ranked by score
 * Requirement 6.9: Allow clicking suggestions to auto-fill guess input
 */

class Suggestions {
    constructor(containerId, onSuggestionClick) {
        this.container = document.getElementById(containerId);
        this.onSuggestionClick = onSuggestionClick;
    }

    /**
     * Display suggestions
     * Requirement 6.8: Display word suggestions in sidebar ranked by score
     */
    display(suggestions) {
        // Clear existing suggestions
        this.container.innerHTML = '';

        if (!suggestions || suggestions.length === 0) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'loading';
            emptyMsg.textContent = 'No suggestions available';
            this.container.appendChild(emptyMsg);
            return;
        }

        suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            if (index === 0) {
                item.classList.add('top-suggestion');
            }
            item.setAttribute('role', 'listitem');
            item.setAttribute('tabindex', '0');
            item.setAttribute('aria-label', `Suggestion ${index + 1}: ${suggestion.word}, score ${suggestion.score}`);

            const wordSpan = document.createElement('span');
            wordSpan.className = 'suggestion-word';
            wordSpan.textContent = suggestion.word;

            const scoreSpan = document.createElement('span');
            scoreSpan.className = 'suggestion-score';
            scoreSpan.textContent = `Score: ${suggestion.score}`;

            item.appendChild(wordSpan);
            item.appendChild(scoreSpan);

            // Add click handler
            item.addEventListener('click', () => {
                if (this.onSuggestionClick) {
                    this.onSuggestionClick(suggestion.word);
                }
            });

            // Add keyboard support
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (this.onSuggestionClick) {
                        this.onSuggestionClick(suggestion.word);
                    }
                }
            });

            this.container.appendChild(item);
        });
    }

    /**
     * Clear suggestions
     */
    clear() {
        this.container.innerHTML = '';
    }

    /**
     * Show loading state
     */
    showLoading() {
        this.container.innerHTML = '<div class="loading">Loading suggestions...</div>';
    }
}

