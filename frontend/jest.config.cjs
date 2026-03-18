module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  testMatch: [
    '<rootDir>/tests/unit/**/*.test.js',
    '<rootDir>/tests/unit/**/*.spec.js'
  ],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.config.js',
    '!src/main.js'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@libs/(.*)$': '<rootDir>/src/libs/$1',
    '^@pages/(.*)$': '<rootDir>/src/pages/$1',
    '\\.(css|less|scss|sass)$': '<rootDir>/tests/styleMock.js'
  },
  transform: {
    '^.+\\.jsx?$': 'babel-jest',
  },
  globals: {
    'jest': true
  }
};
