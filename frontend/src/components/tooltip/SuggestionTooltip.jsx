import React from 'react';
import './SuggestionTooltip.css';

function SuggestionTooltip({ issue, position, onApply, onClose, onFeedback }) {
    console.log('=== TOOLTIP RENDERING ===');
    console.log('Issue:', issue);
    console.log('Position:', position);
    console.log('Suggestions:', issue.suggestions);
    
    return (
        <div 
            className="suggestion-tooltip"
            style={{
                top: `${position.top}px`,
                left: `${position.left}px`
            }}
            onMouseEnter={(e) => e.stopPropagation()}
            onMouseLeave={onClose}
        >
            <div className="tooltip-header">
                <div className="tooltip-title">
                    <strong>{issue.text}</strong>
                    <span className="issue-type">{issue.type.replace('_', ' ')}</span>
                </div>
                <button className="tooltip-close" onClick={onClose}>×</button>
            </div>

            <div className="tooltip-content">
                {issue.suggestions && issue.suggestions.length > 0 ? (
                    <>
                        <p className="tooltip-label">Suggestions:</p>
                        <div className="suggestions-list">
                            {issue.suggestions.map((suggestion, idx) => (
                                <div 
                                    key={suggestion.id || idx}
                                    className="suggestion-item"
                                    onClick={() => onApply(suggestion)}
                                >
                                    <div className="suggestion-text">
                                        "{suggestion.improved_text}"
                                    </div>
                                    <div className="suggestion-rationale">
                                        {suggestion.rationale}
                                    </div>
                                    <div className="suggestion-meta">
                                        {suggestion.type} · {Math.round(suggestion.confidence * 100)}% confidence
                                    </div>
                                    <div className="suggestion-actions">
                                        <button
                                            type="button"
                                            className="feedback-button"
                                            aria-label="Helpful suggestion"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onFeedback?.(suggestion, 'up');
                                            }}
                                        >
                                            👍
                                        </button>
                                        <button
                                            type="button"
                                            className="feedback-button"
                                            aria-label="Not helpful suggestion"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onFeedback?.(suggestion, 'down');
                                            }}
                                        >
                                            👎
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                ) : (
                    <p className="no-suggestions">No suggestions available</p>
                )}
            </div>

            <div className="tooltip-footer">
                <small>Click to apply. Use 👍/👎 to rate quality.</small>
            </div>
        </div>
    );
}

export default SuggestionTooltip;
