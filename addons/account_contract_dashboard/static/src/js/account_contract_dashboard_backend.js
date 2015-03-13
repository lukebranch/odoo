openerp.account_contract_dashboard = function (instance) {

    instance.web.account_contract_dashboard = instance.web.Widget.extend({
        tagName: 'iframe',
        init: function(parent) {
            this._super(parent);
        },
        start: function() {
            var self = this;
            this._super();
            this.$el.attr({'style': 'height: 100%; width: 100%; border: 0;', 'src': '/account_contract_dashboard'});
            this.$el.load(function() {
                self.$el.contents().find('#oe_main_menu_navbar').hide();
                self.$el.contents().find('header').hide();
                self.$el.contents().find('footer').hide();
                self.$el.contents().find('#wrapwrap').addClass('no-padding');
            });
        }
    });

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