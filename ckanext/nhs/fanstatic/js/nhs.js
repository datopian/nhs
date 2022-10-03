this.ckan.module('report-dataset', function (jQuery) {
    return {
      initialize: function () {
        var message = this._('There are unsaved modifications to this form');
  
        $.proxyAll(this, /_on/);
  
        this.el.incompleteFormWarning(message);
  
        // Disable the submit button on form submit, to prevent multiple
        // consecutive form submissions.
        this.el.on('submit', this._onSubmit);
      },
      _onSubmit: function () {
        var description_el = this.el.find('#field-description')
        if(description_el.val().length < 200) {
            this.el.find('.error-block').remove();
            description_el.after('<span class="error-block">Description must be at least 200 characters long</span>');
            return false;
        } 
        setTimeout(function() {
            this.el.find('button[type="submit"]').attr('disabled', true);
        }.bind(this), 0);    
      }
    };
  });
  