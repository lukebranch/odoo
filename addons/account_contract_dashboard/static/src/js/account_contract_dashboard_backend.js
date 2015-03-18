openerp.account_contract_dashboard = function (instance) {

    instance.web.account_contract_dashboard_main = instance.web.Widget.extend({
        tagName: 'iframe',
        init: function(parent) {
            this._super(parent);
            var self = this;
            window.addEventListener("message", function(e) {
                parent.getParent().menu.menu_click(e.data['menu-id'])
                // parent.getParent().menu.open_menu(e.data['menu-id'])
                // parent.getParent().on_menu_action({action_id: e.data['action-id']})
            }, false);
        },
        start: function() {
            var self = this;
            self._super();
            self.$el.attr({'name': 'iframe_backend', 'style': 'height: 100%; width: 100%; border: 0;', 'src': '/account_contract_dashboard'});
            
            self.$el.on("load", function () {
                self.bind_events();
            })
        },
        bind_events: function(){
            var self = this;
            self.$el.contents().find('#button-to-backend').click(self.do_action);
        },
        do_action: function(e){
            window.parent.postMessage({
                'action-id': e.currentTarget.getAttribute('action-id'),
                'menu-id': e.currentTarget.getAttribute('menu-id')
            }, '*');
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
