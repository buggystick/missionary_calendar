// playwright.staging.config.js

import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests/functional',
    timeout: 30000,
    retries: 1,
    use: {
        // This can be overridden by environment variables in .gitlab-ci.yml
        baseURL: process.env.STAGING_URL,
        headless: true,
    },
    reporter: [
        ['html', { outputFolder: process.env.PLAYWRIGHT_HTML_REPORT || 'playwright-report-staging' }]
    ],
});
