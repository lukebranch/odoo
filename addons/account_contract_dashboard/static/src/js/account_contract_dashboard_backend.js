openerp.account_contract_dashboard = function (instance) {

    // GENERIC
    instance.web.IframeBackend = instance.web.Widget.extend({
        tagName: 'iframe',
        init: function(parent, url) {
            this._super(parent);
            this.url = url;
        },
        start: function() {
            this.$el.css({height: '100%', width: '100%', border: 0});
            this.$el.attr({src: this.url});
            this.$el.on("load", this.bind_events.bind(this));
            return this._super();
        },
        bind_events: function(){
            this.$el.contents().click(this.iframe_clicked.bind(this));
        },
        iframe_clicked: function(e){
        }
    });

    // INSTANCES
    instance.web.account_contract_dashboard_main = instance.web.IframeBackend.extend({
        init: function(parent) {
            this._super(parent, '/account_contract_dashboard');
        },
        iframe_clicked: function(e){
            if (e.target.className && e.target.className.indexOf('button-to-backend') > 0){
                var action_id = e.target.getAttribute('action-id');
                var menu_id = e.target.getAttribute('menu-id');
                this.do_action(action_id, {action_menu_id: menu_id});
            }
        }
    });
    
    instance.web.account_contract_dashboard_forecast = instance.web.IframeBackend.extend({
        init: function(parent) {
            this._super(parent, '/account_contract_dashboard/forecast');
        }
    });

    instance.web.client_actions.add("account_contract_dashboard_main", "instance.web.account_contract_dashboard_main");
    instance.web.client_actions.add("account_contract_dashboard_forecast", "instance.web.account_contract_dashboard_forecast");
};
