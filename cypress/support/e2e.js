// ***********************************************************
// This example support/e2e.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'

// Alternatively you can use CommonJS syntax:
// require('./commands')

function printAccessibilityViolations(violations) {
    cy.task(
      "table",
      violations.map(({ id, impact, description, nodes }) => ({
        impact,
        description: `${description} (${id})`,
        nodes: nodes.map((el) => el.target).join(" / "),
      })),
    );
  }
  

  Cypress.Commands.add(
    "checkAccessibility", // define accebility test here
    {
      prevSubject: false,
    },
    ({ skipFailures = false, context = null, options = null } = {}) => {
      //  By default, exclude CKAN debugger elements
      const defaultContext = {
        exclude: [],
      };
  
      if (!context) {
        context = defaultContext;
      } else {
        context = { ...defaultContext, ...context };
      }
  
      cy.checkA11y(
        context,
        {
          ...options,
          runOnly: {
            type: "tag",
            values: ['wcag21aa', 'wcag22aa'],
          },
        },
        printAccessibilityViolations,
        skipFailures,
      );
    },
  );