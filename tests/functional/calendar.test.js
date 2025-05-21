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

test('Simultaneous signup POSTs should preserve first-writer wins', async ({ browser, request, page }) => {
    // 1. Grab dateKey via UI (as you already do)
    await page.goto('/');
    await page.waitForSelector('td:not(.past-day) .day-content');
    const dateKey = await page.locator('td:not(.past-day) .day-content').first().getAttribute('data-date');

    // 2. Fire three POSTs concurrently
    const payloads = [
        { dateKey, name: 'User One',   phone: '111-111-1111' },
        { dateKey, name: 'User Two',   phone: '222-222-2222' },
        { dateKey, name: 'User Three', phone: '333-333-3333' }
    ];

    const [r1, r2, r3] = await Promise.all(
        payloads.map(p => request.post('/api/signups', { data: p }))
    );

    // all should return 200
    expect(await r1.ok()).toBeTruthy();
    expect(await r2.ok()).toBeTruthy();
    expect(await r3.ok()).toBeTruthy();

    // 3. Fetch the canonical state
    const getResp = await request.get('/api/signups');
    expect(await getResp.ok()).toBeTruthy();
    const data = await getResp.json();

    // 4. Assert that the "first" payload wins
    expect(data[dateKey].name).toBe('User One');
    expect(data[dateKey].phone).toBe('111-111-1111');
});

