# Missionary Calendar

A calendar application for missionary scheduling built with Node.js, Express, and PostgreSQL.

## Migration from GitHub/Heroku to GitLab

This repository has been configured to work with GitLab CI/CD and Heroku pipelines. Follow the steps below to complete the migration.

### Step 1: Create a GitLab Repository

1. Create a new repository on GitLab
2. Push your code to the new GitLab repository:
   ```bash
   git remote add gitlab https://gitlab.com/your-username/missionary-calendar.git
   git push -u gitlab main
   ```

### Step 2: Set Up GitLab CI/CD

1. The `.gitlab-ci.yml` file is already configured to run tests and deploy to Heroku
2. In your GitLab repository, go to Settings > CI/CD > Variables
3. Add the following variables:
   - `HEROKU_API_KEY`: Your Heroku API key
   - `HEROKU_APP_STAGING`: Name of your Heroku staging app
   - `HEROKU_APP_PRODUCTION`: Name of your Heroku production app

### Step 3: Set Up Branch Protection Rules

1. In your GitLab repository, go to Settings > Repository > Protected Branches
2. Add a rule for the `main` branch:
   - Allow merge requests when pipeline succeeds
   - Allow only maintainers to merge

### Step 4: Set Up Heroku Pipeline

1. Create a new Heroku pipeline:
   ```bash
   heroku pipelines:create missionary-calendar
   ```

2. Create staging and production apps:
   ```bash
   heroku apps:create your-app-name-staging
   heroku apps:create your-app-name-production
   ```

3. Add the apps to the pipeline:
   ```bash
   heroku pipelines:add missionary-calendar -a your-app-name-staging -s staging
   heroku pipelines:add missionary-calendar -a your-app-name-production -s production
   ```

4. Configure the PostgreSQL addon for both apps:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev -a your-app-name-staging
   heroku addons:create heroku-postgresql:hobby-dev -a your-app-name-production
   ```

5. Update the repository URL in `app.json` to point to your GitLab repository

### Step 5: Working with Development Branches

1. Create a development branch (any name is acceptable):
   ```bash
   git checkout -b your-branch-name
   ```

2. Make your changes and push to GitLab:
   ```bash
   git push -u gitlab your-branch-name
   ```

3. The GitLab CI/CD pipeline will automatically:
   - Run unit tests as a quick sanity check
   - Deploy to your staging app on Heroku when unit tests pass
   - Run functional tests against the live code in Heroku

4. Create a merge request on GitLab
5. Once the merge request is approved and merged, you can promote the staging app to production:
   ```bash
   heroku pipelines:promote -a your-app-name-staging
   ```

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

### Python backend

The Django backend lives alongside the existing Node application and can be used
to migrate functionality incrementally.

1. Create and activate the virtual environment (already committed to `.gitignore`):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Provide Django with a database connection string:
   ```bash
   export DATABASE_URL=postgres://username:password@localhost:5432/missionary_calendar
   ```

4. Run Django management commands as needed, for example to apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the Django development server. It defaults to port 8000 and can run in
   parallel with the Node server or replace it during the migration period:
   ```bash
   python manage.py runserver
   ```

   When running both servers simultaneously, continue to start the Node process
   on port 3000 while Django listens on port 8000. If you prefer to switch to
   Django entirely, stop the Node server and expose Django on the desired port
   using `python manage.py runserver 0.0.0.0:3000`.

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
2. If unit tests pass, the code is deployed to Heroku staging
3. Functional tests run against the live code in Heroku staging

This ensures that functional tests are run against the actual deployed application, providing more accurate test results.

## License

ISC
