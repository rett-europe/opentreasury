/**
 * Jest test setup for Angular.
 *
 * This file is run after the test framework is installed in the environment
 * but before tests execute. It initializes the Angular testing environment.
 */

import "jest-preset-angular/setup-jest";

/**
 * Suppress known Angular warnings in test output.
 * Add patterns here as needed to keep test output clean.
 */
const SUPPRESSED_WARNINGS = [
  /Could not find Angular Material core theme/,
  /Angular is running in development mode/,
];

const originalWarn = console.warn;
console.warn = (...args: unknown[]) => {
  const message = args.join(" ");
  if (SUPPRESSED_WARNINGS.some((pattern) => pattern.test(message))) {
    return;
  }
  originalWarn(...args);
};

/**
 * Mock window.matchMedia (used by Angular Material, not available in jsdom).
 */
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

/**
 * Mock IntersectionObserver (not available in jsdom, used by some Material components).
 */
class MockIntersectionObserver {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  value: MockIntersectionObserver,
});

/**
 * Mock ResizeObserver (not available in jsdom).
 */
class MockResizeObserver {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  value: MockResizeObserver,
});
