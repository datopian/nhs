// Add Google Analytics Event Tracking to resource download links.
this.ckan.module('google_analytics_event_tracking', function(jQuery, _) {
    return {
      
      initialize: function() {

        this.sandbox.subscribe('analytics_enabled', function (analytics_enabled) {
            
          jQuery('a.resource-url-analytics').on('click', function() {
            var resource_url = encodeURIComponent(jQuery(this).prop('href'));
            if (resource_url && analytics_enabled) {
              ga('send', 'event', 'Resource', 'Download', resource_url);
            }
          });
        });
     
      },
      teardown: function() {
        this.sandbox.unsubscribe('analytics_enabled');
      },
    }
  });