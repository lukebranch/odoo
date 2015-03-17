openerp.account_contract_dashboard = function (instance) {

    instance.web.account_contract_dashboard_main = instance.web.Widget.extend({
        tagName: 'iframe',
        init: function(parent) {
            this._super(parent);
        },
        start: function() {
            var self = this;
            self._super();
            self.$el.attr({'name': 'iframe_backend', 'style': 'height: 100%; width: 100%; border: 0;', 'src': '/account_contract_dashboard'});
            self.$el.contents().find('body').delegate('submit', 'form', function(e) {
                debugger;
                self.do_action(e);
            });
        },
        do_action: function(e){
            console.log('coucou');
            console.log(e);
            console.log(this.$el.parent());
        },
    });

    instance.web.account_contract_dashboard_forecast = instance.web.Widget.extend({
        tagName: 'iframe',
        init: function(parent) {
            this._super(parent);
        },
        start: function() {
            var self = this;
            this._super();
            this.$el.attr({'style': 'height: 100%; width: 100%; border: 0;', 'src': '/account_contract_dashboard/forecast'});
        }
    });

    instance.web.client_actions.add("account_contract_dashboard_main", "instance.web.account_contract_dashboard_main");
    instance.web.client_actions.add("account_contract_dashboard_forecast", "instance.web.account_contract_dashboard_forecast");
};
