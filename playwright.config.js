const { defineConfig, devices } = require('@playwright/test');

const python = process.platform === 'win32'
  ? '.\\.venv\\Scripts\\python.exe'
  : 'python';

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: {
    timeout: 8_000
  },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }]
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:8021',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  webServer: process.env.E2E_BASE_URL ? undefined : {
    command: `${python} -m uvicorn backend.app:app --host 127.0.0.1 --port 8021`,
    url: 'http://127.0.0.1:8021',
    reuseExistingServer: true,
    timeout: 15_000
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ]
});
