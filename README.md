# Missionary Calendar

A calendar application for missionary scheduling built with Node.js, Express, and PostgreSQL.

## Continuous Integration

This repository uses GitHub Actions and Heroku Review Apps for testing and review. Every pull request triggers:

1. Unit tests run with Vitest.
2. After the Heroku review app for the pull request is ready, Playwright functional tests execute against the live review app.

Test reports are uploaded as workflow artifacts so you can inspect failures directly from the pull request.

To allow the workflow to access Heroku, add these repository secrets:

- `HEROKU_API_KEY` – API key for a Heroku account that can create review apps
- `HEROKU_PIPELINE` – the name of the Heroku pipeline hosting the review apps

## Development

### Prerequisites

- Node.js
- npm
- PostgreSQL

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   export DATABASE_URL=your_postgres_connection_string
   export PORT=3000
   ```

4. Start the server:
   ```bash
   node app.js
   ```

### Running Tests

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run functional tests locally
npm run test:functional

# Run functional tests against staging environment
npm run test:functional:staging
```

The new workflow runs tests in the following order:
1. Unit tests run first as a quick sanity check
2. The workflow waits for the Heroku review app to be available
3. Functional tests run against the live code in the review app

This ensures that functional tests are run against the actual deployed application, providing more accurate test results.

## License

ISC
