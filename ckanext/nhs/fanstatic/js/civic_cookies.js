ckan.module('civic_cookies', function (jQuery) {
    return {
      initialize: function () {

        ckan_sandbox = this.sandbox;
        
        var config = {
            apiKey: this.options.api_key,
            product: this.options.licence_type,
            position: this.options.popup_position,
            theme: this.options.theme_color,
            initialState: this.options.initial_state,
            necessaryCookies: ['ckan','1P_JAR', 'fldt', 'auth_tkt'],
            encodeCookie: true,
            notifyOnce: true,
            rejectButton: true,
            text: {
              title: 'Our use of cookies',
              intro: 'We use necessary cookies to make our site work. For more detailed information about the cookies we use, see our Cookies page.',
              necessaryTitle: 'Necessary cookies',
              necessaryDescription: 'Necessary cookies enable core functionality such as security, network management, and accessibility. You may disable these by changing your browser settings, but this may affect how the website functions.',
            },
            optionalCookies: [
              {
                  name : 'analytics',
                  label: 'Analytical Cookies',
                  description: "We'd like to set Google Analytics cookies to help us to improve our website by collecting and reporting information on how you use it. The cookies collect information in a way that does not directly identify anyone. For more information on how these cookies work, please see our Cookies page.",
                  cookies: ['_ga', '_gid', '_gat', '__utma', '__utmt', '__utmb', '__utmc', '__utmz', '__utmv'],
                  onAccept : function(){
                    ckan_sandbox.publish('analytics_enabled', true);
                  },
                  onRevoke: function(){
                    ckan_sandbox.publish('analytics_enabled', false);
                  }
              },
            ]
        };
          
        CookieControl.load( config );
      }
    };
});