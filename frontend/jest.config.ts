/** @type {import('jest').Config} */
const config: import("jest").Config = {
  // Use the Angular Jest builder preset
  preset: "jest-preset-angular",

  // Setup file (Angular TestBed initialization)
  setupFilesAfterSetup: ["<rootDir>/src/test-setup.ts"],

  // Only look for tests in src/
  roots: ["<rootDir>/src"],

  // Module name mapping (mirrors tsconfig paths)
  moduleNameMapper: {
    "^@app/(.*)$": "<rootDir>/src/app/$1",
    "^@core/(.*)$": "<rootDir>/src/app/core/$1",
    "^@features/(.*)$": "<rootDir>/src/app/features/$1",
    "^@shared/(.*)$": "<rootDir>/src/app/shared/$1",
    "^@env/(.*)$": "<rootDir>/src/environments/$1",
  },

  // Transform TypeScript via jest-preset-angular
  transform: {
    "^.+\\.(ts|mjs|js|html)$": [
      "jest-preset-angular",
      {
        tsconfig: "<rootDir>/tsconfig.spec.json",
        stringifyContentPathRegex: "\\.(html|svg)$",
      },
    ],
  },

  // File extensions to resolve
  moduleFileExtensions: ["ts", "js", "html", "json", "mjs"],

  // Ignore transforms for node_modules except ESM Angular packages
  transformIgnorePatterns: [
    "node_modules/(?!.*\\.mjs$|@angular|@ngrx|rxjs)",
  ],

  // Coverage configuration
  collectCoverageFrom: [
    "src/app/**/*.ts",
    "!src/app/**/*.spec.ts",
    "!src/app/**/*.module.ts",
    "!src/app/**/index.ts",
    "!src/main.ts",
    "!src/polyfills.ts",
  ],

  coverageDirectory: "<rootDir>/coverage",

  coverageReporters: ["text", "text-summary", "lcov", "json-summary"],

  // Coverage thresholds — practical for NGO project
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 75,
      statements: 75,
    },
    // Stricter thresholds for financial and auth code
    "src/app/core/services/**/*.ts": {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    "src/app/core/auth/**/*.ts": {
      branches: 85,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },

  // Test match patterns
  testMatch: ["**/*.spec.ts"],

  // Faster teardown
  testEnvironment: "jsdom",

  // Display individual test results
  verbose: true,

  // Fail on console.error/warn in tests (catches real issues)
  // Uncomment once tests are stable:
  // silent: false,
};

export default config;
