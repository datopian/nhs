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
        var issue_type_el = this.el.find('#field-type')
        var error = false;

        this.el.find('.error-block').remove();

        if($("#field-type option:selected").text() == 'Select an issue type from the list') {
          issue_type_el.after('<span class="error-block">Please select an issue type from the list</span>');
          error = true
        }

        if(description_el.val().length == 0 ) {
            description_el.after('<span class="error-block">Please enter a description.</span>');
            error = true
        } 
        
        if(error) return false;

        setTimeout(function() {
            this.el.find('button[type="submit"]').attr('disabled', true);
        }.bind(this), 0);    
      }
    };
  });
  