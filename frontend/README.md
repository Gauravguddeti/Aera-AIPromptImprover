# Aera Frontend

Frontend interface for the Aera AI Prompt Enhancement Tool.

## Setup

1. Install dependencies:
```bash
npm install
```

## Development

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Testing

Run unit tests:
```bash
npm test
```

Run E2E tests:
```bash
npm run test:e2e
```

Run tests with UI:
```bash
npm run test:e2e:ui
```

## Code Quality

Lint code:
```bash
npm run lint
```

Fix linting issues:
```bash
npm run lint:fix
```

Format code:
```bash
npm run format
```

Check formatting:
```bash
npm run format:check
```

## Building

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Architecture

- **Components**: Reusable UI components (editor, tooltip, toggle)
- **Services**: API clients and utility services  
- **Pages**: Main application pages
- **Libs**: Independent UI component libraries

## API Integration

The frontend connects to the backend API at http://localhost:8000 and uses WebSocket for real-time analysis.