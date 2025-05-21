import { describe, it, expect, vi } from 'vitest';
import request from 'supertest';

vi.mock('heroku-ssl-redirect', () => ({
    default: {
        default: () => (req, res, next) => next()
    }
}));

vi.mock('pg', () => {
    const mockQuery = vi.fn().mockResolvedValue({
        rows: [
            { date_key: '2025-04-06', name: 'Sister Smith', phone: '555-1234' }
        ],
        rowCount: 1
    });

    const mockClient = {
        query: mockQuery,
        release: vi.fn()
    };

    return {
        default: {
            Pool: vi.fn(() => ({
                query: mockQuery,
                connect: vi.fn().mockResolvedValue(mockClient),
                end: vi.fn()
            }))
        }
    };
});


import app from '../../app.js';

describe('Missionary Calendar API', () => {
    it('GET /api/signups returns signups in JSON format', async () => {
        const res = await request(app).get('/api/signups');
        expect(res.statusCode).toBe(200);
        expect(res.body).toHaveProperty('2025-04-06');
        expect(res.body['2025-04-06']).toEqual({
            name: 'Sister Smith',
            phone: '555-1234'
        });
    });

    it('POST /api/signups saves a new signup', async () => {
        const res = await request(app)
            .post('/api/signups')
            .send({
                dateKey: '2025-04-07',
                name: 'Brother Jones',
                phone: '555-5678'
            });

        expect(res.statusCode).toBe(200);
        expect(res.body.message).toMatch(/Saved sign-up/);
    });
});
