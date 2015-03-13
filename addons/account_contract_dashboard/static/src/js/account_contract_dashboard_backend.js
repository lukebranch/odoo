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
        }
    });

    instance.web.client_actions.add("account_contract_dashboard", "instance.web.account_contract_dashboard");
};
