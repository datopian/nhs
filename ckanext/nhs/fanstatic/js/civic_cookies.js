ckan.module('nhs_civic_cookies', function ($) {
    return {
      initialize: function () {
        console.log("I've been initialized for element: ", this.el);
        var config = {
            apiKey: '925424c91d627482e30e3c6953e2c61a6ac7ee8d',
            product: 'COMMUNITY',
            position: 'RIGHT',
            theme: 'LIGHT'
        };
          
        CookieControl.load( config );
    }
    };
});
