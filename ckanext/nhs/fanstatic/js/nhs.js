this.ckan.module('report-dataset', function (jQuery) {
  return {
    initialize: function () {
      var message = this._('There are unsaved modifications to this form');
      var issue_type_el = this.el.find('#field-type')
      var description_el = this.el.find('#field-description')
      $.proxyAll(this, /_on/);

      this.el.incompleteFormWarning(message);

      // Disable the submit button on form submit, to prevent multiple
      // consecutive form submissions.
      this.el.on('submit', this._onSubmit);
      issue_type_el.on('change', this._onIssueTypeChange);
      description_el.keypress(function () {
        description_el.next('.error-block').remove();
      });
    },
    _onSubmit: function () {
      var description_el = this.el.find('#field-description')
      var issue_type_el = this.el.find('#field-type')
      var error = false;

      this.el.find('.error-block').remove();

      if ($("#field-type option:selected").text() == 'Select an issue type from the list') {
        issue_type_el.after('<span class="error-block">Please select an issue type from the list</span>');
        error = true
      }

      if (description_el.val().length == 0) {
        description_el.after('<span class="error-block">Please enter a description.</span>');
        error = true
      }

      if (error) return false;

      setTimeout(function () {
        this.el.find('button[type="submit"]').attr('disabled', true);
      }.bind(this), 0);
    },
    _onIssueTypeChange: function () {
      var issue_type_el = this.el.find('#field-type')
      issue_type_el.next('.error-block').remove();
    }
  };
});

this.ckan.module('resource-list-view', function (jQuery) {
  return {
    showMoreBtn: null,
    list: null,
    options: {
      defaultShow: 12,
      itemsPerPage: 12,
      currentPage: 1,
      maxPage: null
    },

    initialize: function () {
      this.showMoreBtn = jQuery('#showMoreBtn');
      this.list = this.el[0];
      this.options.maxPage = Math.ceil(this.list.children.length / this.options.itemsPerPage);
    
      if (this.list.children.length <= this.options.defaultShow) {
        this.showMoreBtn.hide();
      }
    
      for (let i = this.options.defaultShow; i < this.list.children.length; i++) {
        jQuery(this.list.children[i]).hide();
        if ((this.list.children.length - this.options.defaultShow) > this.options.itemsPerPage) {
          this.showMoreBtn.html(`Show ${this.options.itemsPerPage} more`);
        } else {
          this.showMoreBtn.html(`Show ${this.list.children.length - this.options.itemsPerPage} more`);
        }
      }
    
      this.showMoreBtn.on('click', this._onClick.bind(this));
    },
    
    _onClick: function () {
      if (this.showMoreBtn.text() == 'Show less') {
        for (let i = this.options.defaultShow; i < this.list.children.length; i++) {
          jQuery(this.list.children[i]).slideUp();
        }
        this.showMoreBtn.html('Show more');
        this.options.currentPage = 1;
        return;
      }
    
      let startIndex = this.options.currentPage  * this.options.itemsPerPage;
      let endIndex = startIndex + this.options.itemsPerPage;
    
      for (let i = startIndex; i < endIndex; i++) {
        if (i >= this.list.children.length) {
          break;
        }
        jQuery(this.list.children[i]).slideDown();
      }
    
      // Update page and check if it's the last page
      this.options.currentPage++;
      if (this.options.currentPage > this.options.maxPage - 1) {
        this.showMoreBtn.text('Show less');
      } else {
        // Update button text to show how many more items are left to display
        let remainingItems = this.list.children.length - endIndex;
    
        if (remainingItems < this.options.itemsPerPage) {
          this.showMoreBtn.html(`Show ${remainingItems} more`);
        } else {
          this.showMoreBtn.html(`Show ${this.options.itemsPerPage} more`);
        }
      }
    }
  };
});
