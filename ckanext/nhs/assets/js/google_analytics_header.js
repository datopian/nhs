ckan.module('google_analytics_header',  function(jQuery, _) {
    return {
      initialize: function () {

        googleanalytics_id = this.options.googleanalytics_id
        
        this.sandbox.subscribe('analytics_enabled', function (analytics_enabled) {
          if(analytics_enabled){
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', googleanalytics_id);
          }
        });
      },
      teardown: function() {
        this.sandbox.unsubscribe('analytics_enabled');
      },
    }
});