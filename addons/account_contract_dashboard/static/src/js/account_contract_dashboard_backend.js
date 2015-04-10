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
            if ($(e.target).hasClass('button-to-backend')){
                var action_id = $(e.target).data('action-id');
                var end_date = this.$el.contents().find('input[name="end_date"').val();
                this.do_action(action_id, {
                    additional_context: {
                        'search_default_asset_end_date': moment(end_date).toDate(),
                        'search_default_asset_start_date': moment(end_date).toDate(),
                    }
                });
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
