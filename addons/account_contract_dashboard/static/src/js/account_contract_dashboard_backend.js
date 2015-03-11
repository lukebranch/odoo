openerp.account_contract_dashboard = function (instance) {

    instance.web.account_contract_dashboard = function() {
        $(document).ready(function() {
            var $iframe = $('<iframe>', {'style': 'position: absolute; height: 100%; width: 100%', 'src': '/account_contract_dashboard'});
            $('div .oe-view-manager-content').append($iframe);
            $('iframe').load(function() {
                $iframe.contents().find('#oe_main_menu_navbar').hide();
                $iframe.contents().find('header').hide();
                $iframe.contents().find('footer').hide();
                $iframe.contents().find('#wrapwrap').addClass('no-padding');
            });
        });
    };

    instance.web.client_actions.add("account_contract_dashboard", "instance.web.account_contract_dashboard");

};

// CORRECT VERSION

// (function() {
//     openerp.account_contract = {};

//     openerp.account_contract.account_contract_dashboard = openerp.web.FrontendInBackend.extend({
//         get_url: function() {
//             return '/account_contract_dashboard';
//         },
//         posprocess_iframe: function() {
//             var myIframe = $('iframe').contents();
//             myIframe.find('#oe_main_menu_navbar').hide();
//             myIframe.find('header').hide();
//             myIframe.find('footer').hide();
//         },        
//     });

//     openerp.web.client_actions.add("account_contract_dashboard", "openerp.account_contract.account_contract_dashboard");
// })();