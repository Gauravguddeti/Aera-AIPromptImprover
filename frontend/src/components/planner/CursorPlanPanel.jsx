import React from 'react';
import './CursorPlanPanel.css';

const PLAN_TEMPLATES = {
    generic_term: [
        'Replace generic terms with a named entity or concrete target.',
        'Add at least one measurable constraint (length, format, or deadline).',
        'Specify expected output type (summary, checklist, code, or table).'
    ],
    subjective_qualifier: [
        'Replace subjective words with quality criteria.',
        'Define how success will be judged (accuracy, style, tone, or structure).',
        'Add one example of what good output should look like.'
    ],
    missing_context: [
        'Add domain, audience, and purpose in one sentence.',
        'Include relevant constraints or assumptions.',
        'Provide source material or key facts to anchor the response.'
    ],
    imprecise_quantity: [
        'Convert vague quantities into explicit ranges.',
        'Set token, sentence, or item count limits.',
        'Define priority order if the list is long.'
    ],
    weak_instruction: [
        'Use a direct verb at the start (analyze, draft, compare, rewrite).',
        'Break the task into numbered actions.',
        'State the final output format clearly.'
    ]
};

function getPlanSteps(issueType) {
    return PLAN_TEMPLATES[issueType] || [
        'Clarify what outcome you want from this prompt.',
        'Add concrete constraints and output structure.',
        'Provide one short example to remove ambiguity.'
    ];
}

function CursorPlanPanel({ issue, position, onClose }) {
    if (!issue || !position) {
        return null;
    }

    const steps = getPlanSteps(issue.type);

    return (
        <aside
            className="cursor-plan-panel"
            style={{ top: `${position.top}px`, left: `${position.left}px` }}
            onMouseEnter={(e) => e.stopPropagation()}
        >
            <div className="cursor-plan-header">
                <strong>Quick Plan</strong>
                <button type="button" className="cursor-plan-close" onClick={onClose}>×</button>
            </div>
            <p className="cursor-plan-context">Focused phrase: "{issue.text}"</p>
            <ol className="cursor-plan-steps">
                {steps.map((step, index) => (
                    <li key={`${issue.type}-${index}`}>{step}</li>
                ))}
            </ol>
        </aside>
    );
}

export default CursorPlanPanel;
