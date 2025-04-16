# NHS

CKAN data portal for NHS, upgraded to work with CKAN 2.11.

## Requirements

This extension requires:

* CKAN 2.11+
* Python 3.7+

## Installation

To install ckanext-nhs:

1. Activate your CKAN virtual environment:

```
. /usr/lib/ckan/default/bin/activate
```

2. Install the package:

```
cd /usr/lib/ckan/default/src/
git clone https://github.com/yourusername/ckanext-nhs.git
cd ckanext-nhs
pip install -e .
pip install -r requirements.txt
```

3. Add `nhs` and `nhs_datastore` to the `ckan.plugins` setting in your CKAN config file:

```
ckan.plugins = ... nhs nhs_datastore
```

4. Restart CKAN:

```
sudo service apache2 restart
```

## Configuration

The extension uses the following configuration options:

```
# reCAPTCHA settings
ckanext.nhs.recaptcha_site_key = YOUR_SITE_KEY
ckanext.nhs.recaptcha_secret_key = YOUR_SECRET_KEY

# Cookie control settings
ckanext.nhs.cc.api_key = YOUR_API_KEY
ckanext.nhs.cc.license_type = pro
ckanext.nhs.cc.popup_position = left
ckanext.nhs.cc.theme_color = #005eb8
ckanext.nhs.cc.initial_state = open

# S3/CloudFlare settings (if used)
ckanext.cloudflare.endpoint = YOUR_ENDPOINT
ckanext.cloudflare.access_id = YOUR_ACCESS_ID
ckanext.cloudflare.access_key = YOUR_ACCESS_KEY

# Google Analytics settings (if used)
googleanalytics.id = YOUR_GA_ID
```

## Features

* Theme customization for NHS
* Data dictionary support
* Blueprint routes with Flask views
* Custom organization pages as "Themes"
* Resource management
* Integration with Google Analytics, CloudFlare, and more

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