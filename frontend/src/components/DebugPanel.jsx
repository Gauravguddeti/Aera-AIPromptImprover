import React, { useState } from 'react';
import './DebugPanel.css';

function DebugPanel({ data }) {
    const [expanded, setExpanded] = useState(true);

    if (!data) {
        return (
            <div className="debug-panel">
                <div className="debug-header">
                    <h3>Debug Output</h3>
                </div>
                <div className="debug-content">
                    <p className="debug-empty">No analysis data yet. Start typing to see results.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="debug-panel">
            <div className="debug-header" onClick={() => setExpanded(!expanded)}>
                <h3>Debug Output</h3>
                <span className="debug-toggle">{expanded ? '▼' : '▶'}</span>
            </div>

            {expanded && (
                <div className="debug-content">
                    <div className="debug-section">
                        <h4>Analysis Summary</h4>
                        <div className="debug-field">
                            <span className="debug-label">Phrases detected:</span>
                            <span className="debug-value">{data.vague_phrases?.length || 0}</span>
                        </div>
                        <div className="debug-field">
                            <span className="debug-label">Analysis time:</span>
                            <span className="debug-value">{data.analysis_time_ms?.toFixed(1)}ms</span>
                        </div>
                        <div className="debug-field">
                            <span className="debug-label">Timestamp:</span>
                            <span className="debug-value">{new Date(data.timestamp).toLocaleTimeString()}</span>
                        </div>
                    </div>

                    <div className="debug-section">
                        <h4>Raw JSON</h4>
                        <pre className="debug-json">
                            {JSON.stringify(data, null, 2)}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    );
}

export default DebugPanel;
