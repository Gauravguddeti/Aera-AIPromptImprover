// Jest setup file for DOM testing
import 'jest-environment-jsdom';

// Mock WebSocket for testing
global.WebSocket = class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 0);
  }
  
  send(data) {
    // Mock send implementation
  }
  
  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose();
  }
};

WebSocket.CONNECTING = 0;
WebSocket.OPEN = 1;
WebSocket.CLOSING = 2;
WebSocket.CLOSED = 3;

// Mock fetch for API testing
global.fetch = jest.fn();

// Console error suppression for expected test errors
const originalError = console.error;
console.error = (...args) => {
  if (args[0]?.includes && args[0].includes('Warning: ReactDOM.render')) {
    return;
  }
  originalError.call(console, ...args);
};