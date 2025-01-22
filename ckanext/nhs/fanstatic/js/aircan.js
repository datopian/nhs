
this.ckan.module('aircan', function (jQuery) {
  return {
    options: {
      resource: null,
      action: null
    },

    initialize: function () {
      setInterval(this._check_status, 30000, this);
    },

    _error_html: function (date, datastoreAction) {
      return (`
          <div class="alert alert-error">
              <span class="fa fa-exclamation-circle"></span>
              <strong>Error:</strong>&nbsp;Aircan Data ingestion has failed&nbsp;
              <span class="date" title="${date}" data-datetime="${date}">
                ${date}.
              </span>
              <span>Please check <a href="${datastoreAction}">datastore page</a>  logs for more information.</span>
          </div>
        `)
    },

    _check_status: function (cb) {
      var client = cb.sandbox.client;
      client.call('POST', 'aircan_status', { id: cb.options.resource }, function (res) {
        var status = res['result']['status']
        var datastoreAction =  cb.options.action 
        var stringDate = moment.utc(res['result']['last_updated']).fromNow()
        if (status == 'error') {
          cb.el.html(cb._error_html(stringDate, datastoreAction ))
        }
      })
    },
  }
})