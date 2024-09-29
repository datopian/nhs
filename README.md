# NHS

CKAN data portal for NHS.

## Automated UAT 

We used [Cypress](https://www.cypress.io/) to automate some user tests. Cypress is a desktop application that is installed on your computer.

### Running locally

**Install Cypress**

Cypress is a Node application. Node versions can be managed using [nvm](https://github.com/nvm-sh/nvm). To install Cypress in this project we use Node ```v.8.17.0```. This version can be installed using nvm:

```nvm install v.8.17.0```

Install Cypress via npm:

```npm install cypress --save-dev```

**Executing Tests**

Opening Cypress with npx:

```npx cypress open```

This will open a desktop application where you can browse the test files. We create two test files, one for staging website and another one for production website. They can be found inside ```cypress/integration``` directory. Just click on the file that you want to run and the test will start.

Here’s a more comprehensive README section with instructions for running Cypress tests using the `package.json` scripts that allow for automated switching between different environments.

---

## Cypress Setup and Test Execution

### Install Cypress

To install Cypress via npm, run:

```bash
npm install cypress --save-dev
```

### Running Cypress Tests

You can run Cypress tests either in **interactive mode** or **headless mode**. You can also specify different environments like **development** and **production** with predefined scripts.

#### Opening Cypress in Interactive Mode

To open Cypress with npx, use the following command:

```bash
npx cypress open
```

This will open the Cypress desktop application where you can browse and run test files. In the project, you’ll find two test files—one for the **staging** website and one for the **production** website. These files are located inside the `cypress/integration` directory. Simply click on the file you want to run, and the test will begin.

#### Running Cypress Tests Using `package.json` Scripts

To automate the process of running tests in different environments (such as development or production), we’ve added custom scripts in the `package.json` file.

The following scripts are available:

### Running Tests for Local Development (http://ckan-dev:5000)

- **Headless Mode**:
  ```bash
  npm run cypress:run:dev
  ```
  This will run Cypress tests headlessly (without the UI) against the development environment (`http://ckan-dev:5000`).

- **Interactive Mode**:
  ```bash
  npm run cypress:open:dev
  ```
  This will open the Cypress interactive mode with the development environment base URL set.

### Running Tests for Production (https://opendata.nhsbsa.net)

- **Headless Mode**:
  ```bash
  npm run cypress:run:prod
  ```
  This will run Cypress tests headlessly against the production environment (`https://opendata.nhsbsa.net`).

- **Interactive Mode**:
  ```bash
  npm run cypress:open:prod
  ```
  This will open the Cypress interactive mode with the production environment base URL set.

### Reporting

Cypress is configured to generate reports in **JUnit** format. The reports will be saved in the `cypress/reports/` directory with a unique filename (using a hash). You can configure the report settings by editing the `cypress.config.js` file.

---
### Running on Gitlab CI

A pipeline was created to run the automated test in this repo. The pipeline won't start automatically after a push, it needs to be started manually. There are two stages in this pipeline:

1. Build
2. Test