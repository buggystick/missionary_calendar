// tests/functional/calendar.test.js
import { test, expect } from '@playwright/test';

test('User can open modal and submit a signup', async ({ page, baseURL }) => {
    await page.goto('/');

    // Wait for calendar to appear
    await page.waitForSelector('.calendar-container');

    // Click on the first available day cell
    const futureDay = await page.locator('td:not(.past-day) .day-content').first();
    await futureDay.click();

    // Modal should appear
    const modal = page.locator('#modalOverlay');
    await expect(modal).toBeVisible();

    // Fill form
    await page.fill('#nameInput', 'Functional Test User');
    await page.fill('#phoneInput', '123-456-7890');

    // Submit form
    await page.click('#saveBtn');

    // Modal should disappear
    await expect(modal).toBeHidden();
});
