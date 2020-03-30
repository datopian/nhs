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
            rejectButton: false,
            text: {
              title: 'Our use of cookies',
              intro: 'We use necessary cookies to make our site work. For more detailed information about the cookies we use, see our Cookies page.',
              accept: 'Save and close',
              acceptSettings: 'Save and close',
              necessaryTitle: 'Necessary cookies',
              necessaryDescription: 'Necessary cookies enable core functionality such as security, network management, and accessibility. You may disable these by changing your browser settings, but this may affect how the website functions.',
            }
        };
          
        CookieControl.load( config );
      }
    };
});