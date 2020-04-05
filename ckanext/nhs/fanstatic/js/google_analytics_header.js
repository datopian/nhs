ckan.module('google_analytics_header',  function(jQuery, _) {
    return {
      initialize: function () {

        googleanalytics_id = this.options.googleanalytics_id
        
        this.sandbox.subscribe('analytics_enabled', function (analytics_enabled) {
          if(analytics_enabled){
            (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
                (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
                m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
                })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
              
                  
                  ga('create', googleanalytics_id, 'auto');
                  ga('set', 'anonymizeIp', true);
                  ga('send', 'pageview');

          }
        });
      }  
    }
});