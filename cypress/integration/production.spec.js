//All of the UAT in staging website
context('Production Website', function(){
  
    // it runs before each test
    beforeEach(function(){
      cy.visit('https://opendata.nhsbsa.net/')
    })
  
    describe('Testing links to resources', function(){
  
      it('English Prescribing Data - Dataset', function(){  
        //check if contains "Datasets" menu and click it
        cy.contains('Datasets').click()
        //check if contains "Engligh Prescribing Data" and click it
        cy.contains('English Prescribing Data').click()
        
        //get and iterate over all of the resources links
        cy.get('.dropdown-menu li a').each(function($el, index, $list){
          cy.wrap($el).should('have.attr', 'href')
            .then(function(href){
              //test if the resource link is working
              cy.request('HEAD', href)
            })
        })
      })
  
      it('Prescription Cost Analysis in England (PCA) - Dataset', function(){
        //check if contains "Datasets" menu and click it
        cy.contains('Datasets').click()
        //check if contains "Engligh Prescribing Data" and click it
        cy.contains('Prescription Cost Analysis in England (PCA)').click()
        
        //get and iterate over all of the resources links
        cy.get('.dropdown-menu li a').each(function($el, index, $list){
          cy.wrap($el).should('have.attr', 'href')
            .then(function(href){
              //test if the resource link is working
              cy.request('HEAD', href)
            })
        })
      })
  
    })
  
  })
  
  