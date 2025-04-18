import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests/functional',
    timeout: 30000,
    retries: 1,
    use: {
        // This will be overridden by the CI pipeline with the actual Heroku app URL
        baseURL: process.env.STAGING_URL || 'https://your-staging-app.herokuapp.com',
        headless: true,
    },
    // No webServer section as we're testing against a deployed app
    webServer: {
        reuseExistingServer: true,
    },
});