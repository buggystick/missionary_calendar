import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests/functional',
    timeout: 30000,
    retries: 0,
    use: {
        baseURL: 'http://localhost:3000',
        headless: true,
    },
    webServer: {
        command: 'NODE_ENV=test  node app.js',
        port: 3000,
        timeout: 10000,
        reuseExistingServer: !process.env.CI,
    },
});
