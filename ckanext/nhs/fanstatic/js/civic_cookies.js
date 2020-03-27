ckan.module('nhs_civic_cookies', function ($) {
    return {
      initialize: function () {
        var config = {
            apiKey: '925424c91d627482e30e3c6953e2c61a6ac7ee8d',
            product: 'COMMUNITY',
            position: 'RIGHT',
            theme: 'LIGHT',
            initialState: 'OPEN',
            necessaryCookies: ['ckan','auth_tkt'],
        };
          
        CookieControl.load( config );
    }
    };
});

    