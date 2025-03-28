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
      },

    initialize: function () {
      this.showMoreBtn = jQuery('#showMoreBtn');
      this.list = this.el[0];

      if (this.list.children.length <= this.options.defaultShow) {
        this.showMoreBtn.hide();
      }
  
      for (let i = this.options.defaultShow; i < this.list.children.length; i++) {
        jQuery(this.list.children[i]).hide();
      }
      
      this.showMoreBtn.on('click', this._onClick.bind(this));
    },
    
    _onClick: function () {
      if (this.showMoreBtn.text() == 'Show First ' + this.options.defaultShow) {
        for (let i = this.options.defaultShow; i < this.list.children.length; i++) {
          jQuery(this.list.children[i]).slideUp(1000);
        }
        this.showMoreBtn.html('Show All');
      } else {
        for (let i = 0; i < this.list.children.length; i++) {
          jQuery(this.list.children[i]).slideDown(1000);
        }
        this.showMoreBtn.html('Show First ' + this.options.defaultShow);
      }
    }
  };
});


this.ckan.module('dashboard-tabs-slider', function($) {
  return {
    initialize: function() {
      const dashboardTabs = document.querySelector('.dashboard-tabs');
      const navTabs = document.querySelector('.nav-tabs');
      const leftArrow = document.querySelector('.left-arrow');
      const rightArrow = document.querySelector('.right-arrow');
    
      const sliderWidth = dashboardTabs.offsetWidth;
      const navTabsWidth = navTabs.offsetWidth;
      const maxOffset = navTabsWidth - sliderWidth;
    
      let offset = 0;
      leftArrow.style.opacity = '0.5';
    
      leftArrow.addEventListener('click', () => {
    
        if (offset < 0) {
          offset += 270;
          if (offset > 0) offset = 0;
          navTabs.style.transition = 'transform 0.5s ease-out';
          navTabs.style.transform = `translateX(${offset}px)`;
          leftArrow.style.opacity = offset == 0 ? '0.5' : '1';
          rightArrow.style.opacity = '1';
        }
      });
    
      rightArrow.addEventListener('click', () => {
        console.log(maxOffset)
        if (offset > -maxOffset) {
          offset -= 270;
          if (offset < -maxOffset) offset = -maxOffset;
          navTabs.style.transition = 'transform 0.5s ease-out';
          navTabs.style.transform = `translateX(${offset}px)`;
          rightArrow.style.opacity = offset == -maxOffset ? '0.5' : '1';
          leftArrow.style.opacity = '1';
        }
      });

      navTabs.addEventListener('transitionend', () => {
        navTabs.style.transition = '';
      });

    }
  };
});


this.ckan.module('dashboard-user-table', function ($) {
  return {
    initialize: function () {

      $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
        // Get the date from the third column of the table (assuming dates are in column 3)
        var dateString = data[2];
        var dateParts = dateString.split('T')[0].split('-');
        var date = new Date(dateParts[0], dateParts[1] - 1, dateParts[2]);

        // Get the current date and subtract the selected number of days or months
        var today = new Date();
        var daysAgo = new Date();
        var selectedValue = $('#date-filter-select').val();

        if (selectedValue === '3d') {
          daysAgo.setDate(today.getDate() - 3);
        } else if (selectedValue === '7d') {
          daysAgo.setDate(today.getDate() - 7);
        } else if (selectedValue === '1m') {
          daysAgo.setMonth(today.getMonth() - 1);
        } else {
          return true;
        }

        // Check if the date is within the selected range
        if (date >= daysAgo && date <= today) {
          return true;
        }

        return false;
      });

      var table = this.el.DataTable(
        {
          select: {
            style: 'single',
            items: [
              { text: 'All', value: 'all' },
              { text: 'Last 3 days', value: '3d' },
              { text: 'Last 7 days', value: '7d' },
              { text: 'This month', value: '1m' }
            ]
          },
          initComplete: function () {
            // Hide search input field
            $(this).closest('.dataTables_wrapper').find('.dataTables_filter').hide();
          },
          lengthChange: false, 
          pageLength: 10,
          language: {
            paginate: {
              next: '»', 
              previous: '«' 
            }
          },
          columnDefs: [
            {
              targets: 0, // The index of the user column
              render: function (data, type, row, meta) {
                // Format the user name as a link
                return `<a href="/user/${data}">${data}</a>`;
              }
            },
            {
              targets: 1,
              width: "25%",
            },
            {
              targets: 2, // The index of the Registration date column
              width: "15%",
              render: function (data, type, row, meta) {
                // Format the date as YYYY-MM-DD
                var date = new Date(data);
                var month = '' + (date.getMonth() + 1);
                var day = '' + date.getDate();
                var year = date.getFullYear();

                if (month.length < 2) month = '0' + month;
                if (day.length < 2) day = '0' + day;

                return [year, month, day].join('-');
              }
            },
            {
              targets: 3, // The index of the Subscribed column
              render: function (data, type, row, meta) {
                // Format the boolean value as Yes or No
                return data == 'True' ? '<span class="text-success">Yes</span>' : '<span class="text-danger">No</span>';
              } 
            },
          ]
        });

     // Add a header with the total number of users and subscribed members
      var totalUsers = table.rows().count();
      var totalSubscribedMembers = table.columns(3).data()[0].filter((value) => value === 'True').length;
      // Update column headers with total count and subscribed count
      table.column(0).header().textContent = 'User (' + totalUsers + ')';
      table.column(3).header().textContent = 'Subscribed Member (' + totalSubscribedMembers + ')';


      // Add event listener for select dropdown to trigger filter
      $('#date-filter-select').on('change', function () {
        table.draw();
        // Recalculate the total number of users and subscribed members and update the header
        var totalUsers = table.rows({ search: 'applied' }).count();
        var totalSubscribedMembers = table.columns(3, { search: 'applied' }).data()[0].filter((value) => value === 'True').length;
        table.column(0).header().textContent = 'User (' + totalUsers + ')';
        table.column(3).header().textContent = 'Subscribed Member (' + totalSubscribedMembers + ')';
      });
      
    }
  };
});

this.ckan.module("example_field_popup", function ($) {
  return {
    initialize: async function () {
      jQuery.proxyAll(this, /_on/);
      let dropdownId = this.options.id;
      let containingElement = document.querySelector(`#${dropdownId}`);

      if (containingElement) {
        containingElement.addEventListener("click", (event) => {
          this.toggleLoading(true);
          this.showFullPageLoader();
          this.getRandomResourceField(this.options.bq_table_name);
        });
      } else {
        console.error("Dropdown element not found:", dropdownId);
      }
    },

    toggleLoading: function (loading) {
      if (loading) {
        this.el.button("loading");
      } else {
        this.el.button("reset");
      }
    },

    showFullPageLoader: function () {
      let loader = jQuery('<div class="full-page-loader" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.7); z-index: 9999; display: flex; justify-content: center; align-items: center;">' +
        '<div class="spinner-border" role="status">' +
        '<span class="visually-hidden">Loading...</span>' +
        '</div>' +
        '</div>');

      jQuery('body').append(loader);
    },

    hideFullPageLoader: function () {
      jQuery('.full-page-loader').remove();
    },

    show: function (template) {
      var sandbox = this.sandbox,
          module = this;

      if (this.modal) {
        return this.modal.modal("show");
      }

      this.loadTemplate(template).done(function (html) {
        module.modal = jQuery(html);
        module.modal
          .find(".modal-header :header")
          .append('<button class="close" >×</button>');

        module.modal.find(".close").on("click", function () {
          module.hide();
        });

        module.modal.on("click", function (event) {
          if (event.target === module.modal[0]) {
            module.hide();
          }
        });

        module.modal.modal().appendTo(sandbox.body);
      });
    },

    hide: function () {
      if (this.modal) {
        this.modal.removeClass('fade').addClass('fade-out');

        var backdrop = jQuery('.modal-backdrop');
        backdrop.removeClass('fade').addClass('fade-out');

        setTimeout(() => {
          this.modal.remove();
          backdrop.remove();
          this.modal = null;
        }, 300);
      }
    },

    loadTemplate: function (template) {
      if (!this.options.template) {
        this.sandbox.notify(
          this._("There is no API data to load for this resource")
        );
        return jQuery.Deferred().reject().promise();
      }

      if (!this.promise) {
        this.promise = jQuery.get(template);
        this.promise.then(this._onTemplateSuccess, this._onTemplateError);
      }
      return this.promise;
    },

    _onTemplateSuccess: function () {
      // Template loaded successfully, can implement any additional logic here
    },

    _onTemplateError: function () {
      this.sandbox.notify(this._("Failed to load data API information"));
    },

    getRandomResourceField: function (res_id) {
      const url = "/api/3/action/datastore_search";
      const params = {
        resource_id: res_id,
        limit: 0,
      };

      // Fetch the resource data from the API
      return fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(params),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.result.fields && data.result.fields.length > 0) {
            const randomIndex = Math.floor(Math.random() * data.result.fields.length);
            const exampleField = data.result.fields[randomIndex];

            const baseUrl = "/api/1/util/snippet/api_info.html";
            const pr = {
              resource_id: res_id,
              example_field_id: exampleField.id,
              example_field_type: exampleField.type,
            };

            const queryParams = new URLSearchParams(pr).toString();
            let apiInfoUrl = `${baseUrl}?${queryParams}`;

            const link = document.getElementById(res_id);
            this.show(apiInfoUrl);

            if (!link) {
              console.error("Link element not found for resourceId:", res_id);
            }
          } else {
            console.error("No fields found.");
          }
        })
        .catch((error) => {
          console.error("Error fetching resource fields:", error);
        })
        .finally(() => {
          this.toggleLoading(false);
          this.hideFullPageLoader();
        });
    },
  };
});
