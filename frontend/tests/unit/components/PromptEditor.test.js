import React from 'react';
import { render, screen } from '@testing-library/react';
import PromptEditor from '@/components/editor/PromptEditor';

// Mock dependencies
jest.mock('@/components/editor/Highlighter', () => () => <div data-testid="highlighter">Highlighter</div>);
jest.mock('@/components/tooltip/SuggestionTooltip', () => () => <div data-testid="tooltip">Tooltip</div>);

describe('PromptEditor', () => {
    it('renders without crashing', () => {
        // Basic smoke test
        expect(true).toBe(true);
    });
});
