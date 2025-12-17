import React, { useState, useEffect } from 'react';
import PromptEditor from './components/editor/PromptEditor';
import DebugPanel from './components/DebugPanel';
import ModelInfo from './components/ModelInfo';
import './App.css';

function App() {
    const [analysisEnabled, setAnalysisEnabled] = useState(true);
    const [debugData, setDebugData] = useState(null);
    const [modelInfo, setModelInfo] = useState(null);
    const [showDebug, setShowDebug] = useState(true);

    useEffect(() => {
        // Fetch model information on startup
        fetch('http://localhost:8000/api/models/discover')
            .then(res => res.json())
            .then(data => setModelInfo(data))
            .catch(err => console.error('Failed to fetch model info:', err));
    }, []);

    return (
        <div className="app">
            <header className="app-header">
                <h1>Aera Prompt Improver</h1>
                <div className="header-controls">
                    <label className="toggle">
                        <input
                            type="checkbox"
                            checked={analysisEnabled}
                            onChange={(e) => setAnalysisEnabled(e.target.checked)}
                        />
                        <span>Analysis {analysisEnabled ? 'ON' : 'OFF'}</span>
                    </label>
                    <button 
                        className="debug-toggle"
                        onClick={() => setShowDebug(!showDebug)}
                    >
                        {showDebug ? 'Hide' : 'Show'} Debug
                    </button>
                </div>
            </header>

            <div className="app-content">
                <div className="editor-section">
                    <PromptEditor
                        enabled={analysisEnabled}
                        onDebugData={setDebugData}
                    />
                </div>

                {showDebug && (
                    <aside className="sidebar">
                        {modelInfo && <ModelInfo data={modelInfo} />}
                        <DebugPanel data={debugData} />
                    </aside>
                )}
            </div>
        </div>
    );
}

export default App;
