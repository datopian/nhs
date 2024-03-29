// Add Google Analytics Event Tracking to resource download links.
this.ckan.module('google_analytics_event_tracking', function(jQuery, _) {
    return {
      
      initialize: function() {

        this.sandbox.subscribe('analytics_enabled', function (analytics_enabled) {
            
          jQuery('a.resource-url-analytics').on('click', function() {
            var resource_name = (jQuery(this).prop('href')).split('/').pop();
            if (resource_name && analytics_enabled) {
              gtag('event', "Download", {
                  'event_category': "Resource",
                  'event_label': resource_name,
              });
            }
          });
        });
     
      },
      teardown: function() {
        this.sandbox.unsubscribe('analytics_enabled');
      },
    }
  });