$( document ).ready(function() {
    document.getElementById('frame-resource-view').onload = function() {
        var ifrm = document.getElementById('frame-resource-view');
        var doc = ifrm.contentDocument? ifrm.contentDocument: ifrm.contentWindow.document;
        var cookie_control_div = doc.getElementById('cookie-control');
        cookie_control_div.setAttribute('data-module', '');
        cookie_control_div.setAttribute('data-module-api_key','');
        cookie_control_div.setAttribute('data-module-licence_type','');
        cookie_control_div.setAttribute('data-module-popup_position','');
        cookie_control_div.setAttribute('data-module-theme_color','');
        cookie_control_div.setAttribute('data-module-initial_state','');
    }
});