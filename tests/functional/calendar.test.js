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

/**
 * This test verifies that the application properly handles concurrent scheduling attempts.
 * 
 * EXPECTED BEHAVIOR:
 * This test is designed to FAIL with the current implementation, as it checks that
 * data from the first user isn't simply overwritten by subsequent users.
 * 
 * The failure of this test demonstrates the need for implementing proper concurrency
 * handling in the application, such as:
 * 1. Optimistic locking
 * 2. Conflict detection and resolution
 * 3. User notifications about conflicts
 * 
 * When this issue is fixed, this test should pass, indicating that the application
 * properly handles concurrent scheduling attempts.
 */
test('Multiple concurrent users can schedule the same day without data override', async ({ browser, baseURL }) => {
    // Create three contexts to simulate three different users
    const userContext1 = await browser.newContext();
    const userContext2 = await browser.newContext();
    const userContext3 = await browser.newContext();

    // Create pages for each user
    const page1 = await userContext1.newPage();
    const page2 = await userContext2.newPage();
    const page3 = await userContext3.newPage();

    // Navigate all users to the application
    await page1.goto('/');
    await page2.goto('/');
    await page3.goto('/');

    // Wait for calendar to appear on all pages
    await page1.waitForSelector('.calendar-container');
    await page2.waitForSelector('.calendar-container');
    await page3.waitForSelector('.calendar-container');

    // All users select the same day (first available day)
    const daySelector = 'td:not(.past-day) .day-content';

    // Get the date key of the day we're testing with
    const dateKey = await page1.locator(daySelector).first().getAttribute('data-date');
    console.log(`Testing with date: ${dateKey}`);

    // All users click on the same day
    await page1.locator(daySelector).first().click();
    await page2.locator(daySelector).first().click();
    await page3.locator(daySelector).first().click();

    // All users should see the modal
    await expect(page1.locator('#modalOverlay')).toBeVisible();
    await expect(page2.locator('#modalOverlay')).toBeVisible();
    await expect(page3.locator('#modalOverlay')).toBeVisible();

    // Each user fills out the form with different information
    await page1.fill('#nameInput', 'User One');
    await page1.fill('#phoneInput', '111-111-1111');

    await page2.fill('#nameInput', 'User Two');
    await page2.fill('#phoneInput', '222-222-2222');

    await page3.fill('#nameInput', 'User Three');
    await page3.fill('#phoneInput', '333-333-3333');

    // All users submit their forms nearly simultaneously
    await Promise.all([
        page1.click('#saveBtn'),
        page2.click('#saveBtn'),
        page3.click('#saveBtn')
    ]);

    // Wait for all modals to close
    await expect(page1.locator('#modalOverlay')).toBeHidden();
    await expect(page2.locator('#modalOverlay')).toBeHidden();
    await expect(page3.locator('#modalOverlay')).toBeHidden();

    // Wait a moment for any WebSocket updates to propagate
    await page1.waitForTimeout(1000);

    // Refresh all pages to ensure they have the latest data
    await page1.reload();
    await page2.reload();
    await page3.reload();

    // Wait for calendar to appear again
    await page1.waitForSelector('.calendar-container');
    await page2.waitForSelector('.calendar-container');
    await page3.waitForSelector('.calendar-container');

    // Check the signup data for the day on all pages
    // We'll click on the day again to see the current data
    await page1.locator(`td[data-date="${dateKey}"] .day-content`).click();
    await expect(page1.locator('#modalOverlay')).toBeVisible();

    // Get the current values in the form
    const nameValue = await page1.inputValue('#nameInput');
    const phoneValue = await page1.inputValue('#phoneInput');

    // Close the modal
    await page1.click('#cancelBtn');

    // The test should verify that the data wasn't simply overwritten by the last user
    // If the system is working correctly, it should have some conflict resolution mechanism
    // or show an error to subsequent users

    // This assertion will fail if the data was simply overwritten by the last user (User Three)
    expect(nameValue).not.toBe('User Three');
    expect(phoneValue).not.toBe('333-333-3333');

    // Clean up
    await userContext1.close();
    await userContext2.close();
    await userContext3.close();
});
