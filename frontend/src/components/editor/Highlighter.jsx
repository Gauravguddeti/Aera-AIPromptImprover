import React, { useRef, useEffect } from 'react';
import './Highlighter.css';

const SEVERITY_COLORS = {
    generic_term: { bg: 'rgba(245, 158, 11, 0.3)', underline: '#f59e0b' },      // orange
    subjective_qualifier: { bg: 'rgba(245, 158, 11, 0.3)', underline: '#f59e0b' },
    missing_context: { bg: 'rgba(239, 68, 68, 0.25)', underline: '#ef4444' },   // red
    imprecise_quantity: { bg: 'rgba(245, 158, 11, 0.3)', underline: '#f59e0b' },
    weak_instruction: { bg: 'rgba(239, 68, 68, 0.25)', underline: '#ef4444' },
    missing_examples: { bg: 'rgba(59, 130, 246, 0.25)', underline: '#3b82f6' }, // blue - needs examples
    missing_reasoning: { bg: 'rgba(168, 85, 247, 0.25)', underline: '#a855f7' }, // purple - needs CoT
    missing_structure: { bg: 'rgba(236, 72, 153, 0.25)', underline: '#ec4899' }, // pink - needs structure
    ambiguous_task: { bg: 'rgba(239, 68, 68, 0.3)', underline: '#ef4444' }      // red - unclear task
};

function Highlighter({ text, issues, onHover, onLeave }) {
    const highlightRef = useRef(null);

    useEffect(() => {
        console.log('Highlighter useEffect triggered - issues:', issues.length);
        if (!highlightRef.current) return;

        // Clear previous highlights
        highlightRef.current.innerHTML = '';

        if (!text || issues.length === 0) {
            highlightRef.current.textContent = text || '';
            return;
        }

        // Sort issues by start position
        const sortedIssues = [...issues].sort((a, b) => a.start - b.start);

        let lastIndex = 0;
        const fragment = document.createDocumentFragment();

        sortedIssues.forEach((issue, idx) => {
            // Add text before this issue
            if (lastIndex < issue.start) {
                const textNode = document.createTextNode(text.substring(lastIndex, issue.start));
                fragment.appendChild(textNode);
            }

            // Get the text and trim spaces
            let issueText = text.substring(issue.start, issue.end);
            let trimmedText = issueText;
            let startOffset = 0;
            let endOffset = 0;
            
            // Count leading spaces
            const leadingMatch = issueText.match(/^\s*/);
            if (leadingMatch) {
                startOffset = leadingMatch[0].length;
            }
            
            // Count trailing spaces
            const trailingMatch = issueText.match(/\s*$/);
            if (trailingMatch) {
                endOffset = trailingMatch[0].length;
            }
            
            // Add leading spaces as text nodes
            if (startOffset > 0) {
                fragment.appendChild(document.createTextNode(issueText.substring(0, startOffset)));
            }
            
            // Get the actual content without spaces
            trimmedText = issueText.substring(startOffset, issueText.length - endOffset);
            
            // Add highlighted text (without spaces)
            if (trimmedText.length > 0) {
                const span = document.createElement('span');
                span.className = 'highlight';
                span.dataset.issueIndex = idx;
                span.textContent = trimmedText;
                
                const colors = SEVERITY_COLORS[issue.type] || SEVERITY_COLORS.generic_term;
                span.style.background = colors.bg;
                span.style.borderBottom = `2px wavy ${colors.underline}`;

                span.addEventListener('mouseenter', (e) => {
                    console.log('Hovering issue:', issue);
                    const rect = span.getBoundingClientRect();
                    onHover(issue, rect);
                });
                
                span.addEventListener('mouseleave', () => {
                    onLeave();
                });

                fragment.appendChild(span);
            }
            
            // Add trailing spaces as text nodes
            if (endOffset > 0) {
                fragment.appendChild(document.createTextNode(issueText.substring(issueText.length - endOffset)));
            }
            
            lastIndex = issue.end;
        });

        // Add remaining text
        if (lastIndex < text.length) {
            const textNode = document.createTextNode(text.substring(lastIndex));
            fragment.appendChild(textNode);
        }

        highlightRef.current.appendChild(fragment);
        console.log('Highlighter finished rendering', issues.length, 'issues');
    }, [text, issues, onHover, onLeave]);

    return (
        <div ref={highlightRef} className="highlighter-overlay"></div>
    );
}

export default Highlighter;
