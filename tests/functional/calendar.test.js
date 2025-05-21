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
    // Dynamically pick a unique date 15 days in the future to avoid conflicts
    const uniqueDate = new Date();
    uniqueDate.setDate(uniqueDate.getDate() + 15);
    const uniqueDateKey = uniqueDate.toISOString().split('T')[0];

    const payloads = [
        { dateKey: uniqueDateKey, name: 'User One',   phone: '111-111-1111' },
        { dateKey: uniqueDateKey, name: 'User Two',   phone: '222-222-2222' },
        { dateKey: uniqueDateKey, name: 'User Three', phone: '333-333-3333' }
    ];

    const [r1, r2, r3] = await Promise.all(
        payloads.map(p => request.post('/api/signups', { data: p }))
    );

    expect(await r1.ok()).toBeTruthy();
    expect(await r2.ok()).toBeTruthy();
    expect(await r3.ok()).toBeTruthy();

    const getResp = await request.get('/api/signups');
    expect(await getResp.ok()).toBeTruthy();
    const data = await getResp.json();

    expect(data[uniqueDateKey].name).toBe('User One');
    expect(data[uniqueDateKey].phone).toBe('111-111-1111');
});

