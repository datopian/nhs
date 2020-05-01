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

### Running on Gitlab CI

A pipeline was created to run the automated test in this repo. The pipeline won't start automatically after a push, it needs to be started manually. There are two stages in this pipeline:

1. Build
2. Test