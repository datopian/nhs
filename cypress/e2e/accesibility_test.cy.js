import 'cypress-axe';
import pages from '../routes.json';


const replaceParams = (route) => {
    return route;
};


describe('NHS Accessibility Testing', () => { // define testing
    pages.forEach((route) => {
        const page = replaceParams(route);
        
        it(`Has no WCAG 2.1 and 2.2 violation rules in route: ${page}`, () => {
          cy.visit(page);
          cy.injectAxe();
          cy.checkAccessibility();
        });
    });
});
