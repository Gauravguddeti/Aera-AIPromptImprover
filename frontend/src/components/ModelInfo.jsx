import React, { useState } from 'react';
import './ModelInfo.css';

function ModelInfo({ data }) {
    const [expanded, setExpanded] = useState(true);

    if (!data || data.status === 'no_models_found') {
        return (
            <div className="model-info error">
                <div className="model-header" onClick={() => setExpanded(!expanded)}>
                    <h3>⚠️ No Models Found</h3>
                    <span className="model-toggle">{expanded ? '▼' : '▶'}</span>
                </div>
                {expanded && (
                    <div className="model-content">
                        <p className="model-warning">
                            No Ollama models detected. Install a model to enable AI-powered suggestions:
                        </p>
                        <code className="model-command">ollama pull llama3:8b</code>
                    </div>
                )}
            </div>
        );
    }

    const { available_models, best_models, recommendations } = data;

    return (
        <div className="model-info">
            <div className="model-header" onClick={() => setExpanded(!expanded)}>
                <h3>🤖 Model Info</h3>
                <span className="model-toggle">{expanded ? '▼' : '▶'}</span>
            </div>

            {expanded && (
                <div className="model-content">
                    <div className="model-section">
                        <h4>Available Models</h4>
                        {available_models?.map((model, idx) => {
                            const rec = recommendations[idx];
                            return (
                                <div key={model.name} className="model-item">
                                    <div className="model-name">
                                        {model.name}
                                        <span className="model-size">{model.size}</span>
                                    </div>
                                    {rec && (
                                        <>
                                            <div className="model-suitable">
                                                {rec.suitable_for.map(task => (
                                                    <span key={task} className="model-badge">{task}</span>
                                                ))}
                                            </div>
                                            {rec.warnings.length > 0 && (
                                                <div className="model-warnings">
                                                    {rec.warnings.map((warning, i) => (
                                                        <div key={i} className="model-warning">{warning}</div>
                                                    ))}
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {best_models && (
                        <div className="model-section">
                            <h4>Best Models</h4>
                            <div className="model-best">
                                <div><strong>Analysis:</strong> {best_models.analysis || 'N/A'}</div>
                                <div><strong>Rewriting:</strong> {best_models.rewriting || 'N/A'}</div>
                                <div><strong>Inline:</strong> {best_models.inline_checks || 'N/A'}</div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default ModelInfo;
