import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      on('task', {
        table(violations) {  
          console.table(violations);
          return null;
        },
      });

      const baseUrl = config.env.baseUrl || 'https://opendata.nhsbsa.net';
      config.baseUrl = baseUrl;

      return config;
    },
    baseUrl: 'https://opendata.nhsbsa.net',
    pageLoadTimeout: 60000,
    reporter: 'junit',
    reporterOptions: {
      mochaFile: 'cypress/reports/junit-[hash].xml',
      toConsole: true, 
    },
  },
});
