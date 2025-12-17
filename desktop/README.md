# Aera Desktop

Desktop application wrapper for the Aera AI Prompt Enhancement Tool using Tauri.

## Prerequisites

- [Rust](https://rustup.rs/) 1.70+
- [Node.js](https://nodejs.org/) 18+
- Platform-specific dependencies:
  - **Windows**: Microsoft C++ Build Tools
  - **macOS**: Xcode Command Line Tools
  - **Linux**: `build-essential`, `libgtk-3-dev`, `libwebkit2gtk-4.0-dev`

## Setup

1. Install Tauri CLI:
```bash
npm install
```

2. Install Rust dependencies:
```bash
cd src-tauri
cargo fetch
```

## Development

Run in development mode:
```bash
npm run dev
```

This will:
1. Start the frontend development server
2. Start the backend API server  
3. Launch the desktop application

## Building

Build for production:
```bash
npm run build
```

Build debug version:
```bash
npm run build:debug
```

## Architecture

The desktop application:
- Wraps the web frontend in a native window
- Provides system integration (notifications, file system)
- Manages the backend Python process
- Offers offline capabilities

## Platform Support

- ✅ Windows 10+
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 18.04+, Fedora 30+)

## Features

- Native window management
- System tray integration
- Auto-start backend process
- Cross-platform distribution
- Secure local processing