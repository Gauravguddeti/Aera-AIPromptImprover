import React, { useState, useEffect, useRef, useCallback } from 'react';
import debounce from 'debounce';
import { v4 as uuidv4 } from 'uuid';
import Highlighter from './Highlighter';
import SuggestionTooltip from '../tooltip/SuggestionTooltip';
import CursorPlanPanel from '../planner/CursorPlanPanel';
import './PromptEditor.css';

const WEBSOCKET_URL = 'ws://localhost:8000/ws/analysis';
const API_BASE_URL = 'http://localhost:8000';
const DEBOUNCE_MS = 300;

function PromptEditor({ enabled, onDebugData }) {
    const [text, setText] = useState('');
    const [issues, setIssues] = useState([]);
    const [analysisData, setAnalysisData] = useState(null);
    const [hoveredIssue, setHoveredIssue] = useState(null);
    const [tooltipPosition, setTooltipPosition] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [showPlanningPanel, setShowPlanningPanel] = useState(true);
    const [planPanelPosition, setPlanPanelPosition] = useState(null);
    
    const wsRef = useRef(null);
    const textareaRef = useRef(null);
    const clientIdRef = useRef(uuidv4());

    // Close tooltip when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (hoveredIssue && !e.target.closest('.suggestion-tooltip') && !e.target.closest('.highlight')) {
                setHoveredIssue(null);
                setTooltipPosition(null);
            }
        };
        
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [hoveredIssue]);

    // Handle Ctrl+Z for undo
    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                if (historyIndex > 0) {
                    const previousText = history[historyIndex - 1];
                    setText(previousText);
                    setHistoryIndex(prev => prev - 1);
                    if (enabled && previousText.trim()) {
                        sendAnalysisRequest(previousText);
                    }
                }
            }
        };
        
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [history, historyIndex, enabled]);

    // WebSocket connection
    useEffect(() => {
        if (!enabled) return;

        const ws = new WebSocket(WEBSOCKET_URL);
        wsRef.current = ws;

        ws.onopen = () => {
            setConnectionStatus('connected');
        };

        ws.onmessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                if (response.type === 'analysis_response' && response.data) {
                    const { vague_phrases } = response.data;
                    
                    // Convert vague phrases to issues format
                    const convertedIssues = vague_phrases.map(phrase => {
                        return {
                            start: phrase.start_position,
                            end: phrase.end_position,
                            text: phrase.text,
                            type: phrase.type,
                            confidence: phrase.confidence,
                            suggestions: phrase.suggestions || []
                        };
                    });
                    
                    setIssues(convertedIssues);
                    setAnalysisData(response.data);
                    onDebugData?.(response.data);
                }
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnectionStatus('error');
        };

        ws.onclose = () => {
            setConnectionStatus('disconnected');
        };

        return () => {
            ws.close();
        };
    }, [enabled, onDebugData]);

    // Debounced analysis request
    const sendAnalysisRequest = useCallback(
        debounce((content) => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                const request = {
                    type: 'analysis_request',
                    data: {
                        content,
                        options: {
                            include_suggestions: true,
                            max_suggestions_per_phrase: 3,
                            min_confidence: 0.5,
                            debounce_ms: DEBOUNCE_MS
                        }
                    }
                };
                wsRef.current.send(JSON.stringify(request));
            }
        }, DEBOUNCE_MS),
        []
    );

    // Handle text changes
    const handleTextChange = (e) => {
        const newText = e.target.value;
        
        // Add to history for undo
        setHistory(prev => [...prev.slice(0, historyIndex + 1), text]);
        setHistoryIndex(prev => prev + 1);
        
        setText(newText);
        
        // Close tooltip immediately when user types
        setHoveredIssue(null);
        setTooltipPosition(null);
        
        if (enabled && newText.trim()) {
            sendAnalysisRequest(newText);
        } else {
            setIssues([]);
            setAnalysisData(null);
        }
    };

    // Close tooltip when textarea is clicked or focused
    const handleTextareaFocus = () => {
        setHoveredIssue(null);
        setTooltipPosition(null);
        setPlanPanelPosition(null);
    };

    // Detect hover over issues by cursor position in textarea
    const handleTextareaMouseMove = (e) => {
        if (!textareaRef.current || issues.length === 0) return;
        
        const textarea = textareaRef.current;
        const cursorPos = textarea.selectionStart;
        
        // Find if cursor is within any issue
        const hoveredIssue = issues.find(issue => 
            cursorPos >= issue.start && cursorPos <= issue.end
        );
        
        if (hoveredIssue) {
            // Calculate position for tooltip
            const textBeforeCursor = text.substring(0, hoveredIssue.start);
            const lines = textBeforeCursor.split('\n');
            const currentLine = lines.length - 1;
            const charInLine = lines[lines.length - 1].length;
            
            const rect = textarea.getBoundingClientRect();
            const lineHeight = 1.6 * 16; // line-height * font-size
            const charWidth = 9.6; // approximate char width for monospace
            
            handleHighlightHover(hoveredIssue, {
                top: rect.top + (currentLine * lineHeight),
                left: rect.left + (charInLine * charWidth),
                bottom: rect.top + ((currentLine + 1) * lineHeight),
                right: rect.left + ((charInLine + hoveredIssue.text.length) * charWidth)
            });
        } else if (hoveredIssue !== null) {
            handleHighlightLeave();
        }
    };

    // Handle hover on highlighted text (like Grammarly)
    const handleHighlightHover = (issue, rect) => {
        setHoveredIssue(issue);
        
        // Calculate position - show to the RIGHT of the word
        const tooltipHeight = 200; // estimated
        const tooltipWidth = 350;
        const scrollX = window.scrollX || window.pageXOffset;
        const scrollY = window.scrollY || window.pageYOffset;
        
        // Position to the right of the word
        let left = rect.right + scrollX + 10;
        let top = rect.top + scrollY;
        
        // If not enough space on right, show on left
        if (left + tooltipWidth > window.innerWidth + scrollX) {
            left = rect.left + scrollX - tooltipWidth - 10;
        }
        
        // If still not enough space, center it below the word
        if (left < scrollX) {
            left = rect.left + scrollX;
            top = rect.bottom + scrollY + 10;
        }
        
        // Keep within viewport vertically
        if (top + tooltipHeight > window.innerHeight + scrollY) {
            top = window.innerHeight + scrollY - tooltipHeight - 20;
        }
        if (top < scrollY) {
            top = scrollY + 10;
        }
        
        setTooltipPosition({ top, left });

        // Keep planning panel adjacent to cursor and avoid viewport overflow.
        let planLeft = left + tooltipWidth + 12;
        let planTop = top;
        if (planLeft + 320 > window.innerWidth + scrollX) {
            planLeft = left - 332;
        }
        if (planLeft < scrollX + 8) {
            planLeft = scrollX + 8;
            planTop = top + 210;
        }
        setPlanPanelPosition({ top: planTop, left: planLeft });
    };

    const handleHighlightLeave = () => {
        // Small delay before closing to allow mouse to reach tooltip
        setTimeout(() => {
            setHoveredIssue(null);
            setTooltipPosition(null);
            setPlanPanelPosition(null);
        }, 100);
    };

    // Apply suggestion
    const applySuggestion = (issue, suggestion) => {
        // Save current state to history
        setHistory(prev => [...prev.slice(0, historyIndex + 1), text]);
        setHistoryIndex(prev => prev + 1);
        
        const before = text.substring(0, issue.start);
        const after = text.substring(issue.end);
        const newText = before + suggestion.improved_text + after;
        
        setText(newText);
        setHoveredIssue(null);
        setTooltipPosition(null);
        setPlanPanelPosition(null);
        
        // Update issue positions after replacement
        const lengthDiff = suggestion.improved_text.length - (issue.end - issue.start);
        setIssues(prevIssues => prevIssues.map(i => {
            if (i.start > issue.end) {
                return { ...i, start: i.start + lengthDiff, end: i.end + lengthDiff };
            }
            return i;
        }).filter(i => i.start !== issue.start || i.end !== issue.end));
        
        // Re-analyze after applying suggestion
        if (enabled) {
            sendAnalysisRequest(newText);
        }
    };

    const handleSuggestionFeedback = async (issue, suggestion, rating) => {
        if (!suggestion?.id) {
            return;
        }

        try {
            await fetch(`${API_BASE_URL}/api/suggestions/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    suggestion_id: suggestion.id,
                    phrase_text: issue.text,
                    improved_text: suggestion.improved_text,
                    rating,
                    context: text,
                    provider_used: analysisData?.provider_used || null
                })
            });
        } catch (error) {
            console.error('Failed to submit suggestion feedback:', error);
        }
    };

    return (
        <div className="prompt-editor">
            <div className="editor-header">
                <h2>Prompt Input</h2>
                <div className="connection-status">
                    <span className={`status-indicator status-${connectionStatus}`}></span>
                    <span>{connectionStatus}</span>
                    <button
                        type="button"
                        className="planning-toggle"
                        onClick={() => setShowPlanningPanel(prev => !prev)}
                    >
                        {showPlanningPanel ? 'Hide Plan' : 'Show Plan'}
                    </button>
                </div>
            </div>

            <div className="editor-container">
                <Highlighter
                    key={`highlighter-${issues.length}-${text.length}`}
                    text={text}
                    issues={issues}
                    onHover={handleHighlightHover}
                    onLeave={handleHighlightLeave}
                />
                <textarea
                    ref={textareaRef}
                    value={text}
                    onChange={handleTextChange}
                    onFocus={handleTextareaFocus}
                    onClick={handleTextareaFocus}
                    onMouseMove={handleTextareaMouseMove}
                    placeholder="Type your prompt here... (e.g., 'Write something good about AI')"
                    className="editor-textarea"
                    spellCheck={false}
                />
            </div>

            {hoveredIssue && tooltipPosition && (
                <SuggestionTooltip
                    issue={hoveredIssue}
                    position={tooltipPosition}
                    onApply={(suggestion) => applySuggestion(hoveredIssue, suggestion)}
                    onFeedback={(suggestion, rating) => handleSuggestionFeedback(hoveredIssue, suggestion, rating)}
                    onClose={() => {
                        setHoveredIssue(null);
                        setPlanPanelPosition(null);
                    }}
                />
            )}

            {showPlanningPanel && hoveredIssue && planPanelPosition && (
                <CursorPlanPanel
                    issue={hoveredIssue}
                    position={planPanelPosition}
                    onClose={() => setPlanPanelPosition(null)}
                />
            )}

            {analysisData && (
                <div className="editor-stats">
                    <span>{issues.length} issue{issues.length !== 1 ? 's' : ''} detected</span>
                    <span>·</span>
                    <span>Analysis: {analysisData.analysis_time_ms?.toFixed(1)}ms</span>
                </div>
            )}
        </div>
    );
}

export default PromptEditor;
