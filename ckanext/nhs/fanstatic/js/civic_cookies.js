ckan.module('nhs_civic_cookies', function ($) {
    return {
      initialize: function () {

        var config = {
            apiKey: this.options.api_key,
            product: this.options.licence_type,
            position: this.options.popup_position,
            theme: this.options.theme_color,
            initialState: this.options.initial_state,
            necessaryCookies: ['ckan','1P_JAR', 'fldt', 'auth_tkt'],
            encodeCookie: true,
            notifyOnce: true,
            rejectButton: false
        };
          
        CookieControl.load( config );
      }
    };
});