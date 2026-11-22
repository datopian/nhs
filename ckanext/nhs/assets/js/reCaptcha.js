ckan.module('reCaptcha', function (jQuery) {
    return {
        options: {
            sitekey: null,
        },
        initialize: function () {
            var recaptcha = document.createElement('script');
            recaptcha.src = 'https://www.google.com/recaptcha/api.js?render=' + this.options.sitekey;
            recaptcha.async = true;
            recaptcha.defer = true;
            document.body.appendChild(recaptcha);
            $.proxyAll(this, /_on/);

            // onClick event
            this.el.on('click', this._onClick);

            // hidden input field with the token
            this.el.before('<input type="hidden" name="g-recaptcha-token" value="">');

        },
        _onClick: function (event) {
            event.preventDefault();
            var module = this;
            grecaptcha.ready(function (module) {
                return function () {
                    grecaptcha.execute(module.options.sitekey, { action: 'submit' }).then(function (token) {
                        jQuery('input[name="g-recaptcha-token"]').val(token);
                        module.el.closest('form').submit();
                    });
                };
            }(module));
        }
    };
});
