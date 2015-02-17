(function(){

    "use strict";

    var _t = openerp._t;
    var QWeb = openerp.qweb;
    var instance = openerp;

    // constants
    var NBR_LIMIT_HISTORY = 20;
    var USERS_LIMIT = 20;

    // ########## CONVERSATION extentions ###############

    instance.im_chat.Conversation.include({
        // user actions
        _start_action_menu: function(){
            this._add_action(_t('Shortcuts'), 'im_chat_option_shortcut', 'fa fa-info-circle', this.action_shorcode);
            this._add_action(_t('Quit discussion'), 'im_chat_option_quit', 'fa fa-minus-square', this.action_quit_session);
            return this._super();
        },
        action_shorcode: function(e){
            return instance.client.action_manager.do_action({
                type: 'ir.actions.act_window',
                name : _t('Shortcode'),
                res_model: 'im_chat.shortcode',
                view_mode: 'tree,form',
                view_type: 'tree',
                views: [[false, 'list'], [false, 'form']],
                target: "new",
                limit: 80,
                flags: {
                    action_buttons: true,
                    pager: true,
                }
            });
        },
        action_quit_session: function(e){
            var self = this;
            var Session = new openerp.Model("im_chat.session");
            return Session.call("quit_user", [this.get("session").uuid]).then(function(res) {
               if(! res){
                    self.do_warn(_t("Warning"), _t("You are only 2 identified users. Just close the conversation to leave."));
               }
            });
        },
        // window title
        window_title_change: function() {
            this.super();
            var title = undefined;
            if (this.get("waiting_messages") !== 0) {
                title = _.str.sprintf(_t("%d Messages"), this.get("waiting_messages"))
            }
            openerp.webclient.set_title_part("im_messages", title);
        },
        // TODO : change this way
        add_user: function(user){
            return new openerp.Model("im_chat.session").call("add_user", [this.get("session").uuid , user.id]);
        },
    });


    // ###### BACKEND : contact panel, top menu button #########

    /**
     * Widget for the user Card in the 'contact' list
     */
    instance.im_chat.UserWidget = openerp.Widget.extend({
        template: "im_chat.UserWidget",
        events: {
            "click": "on_click_user",
        },
        init: function(parent, user) {
            this._super(parent);
            this.set("id", user.id);
            this.set("name", user.name);
            this.set("im_status", user.im_status);
            this.set("image_url", user.image_url);
        },
        start: function() {
            this.$el.data("user", {id:this.get("id"), name:this.get("name")});
            this.$el.draggable({helper: "clone"});
            this.on("change:im_status", this, this.update_status);
            this.update_status();
        },
        update_status: function(){
            this.$(".o_im_chat_status").toggle(this.get('im_status') !== 'offline');
            var img_src = (this.get('im_status') == 'away' ? '/im_chat/static/src/img/yellow.png' : '/im_chat/static/src/img/green.png');
            this.$(".o_im_chat_status").attr('src', img_src);
        },
        on_click_user: function() {
            this.trigger("user_clicked", this.get("id"));
        },
    });

    /**
     * Widget for chat sidebar.
     * This manage the user search.
     */
    instance.im_chat.InstantMessaging = openerp.Widget.extend({
        template: "im_chat.InstantMessaging",
        events: {
            "keydown .o_im_chat_user_search_box": "input_change",
            "keyup .o_im_chat_user_search_box": "input_change",
            "change .o_im_chat_user_search_box": "input_change",
        },
        init: function(parent){
            this._super(parent);
            // ui
            this.shown = false;
            this.set("right_offset", 0);
            // business
            this.user_widgets = {};
            this.set("current_search", "");
            this.conv_manager = new openerp.im_chat.ConversationManager(this);
            // listen bus
            this.bus = openerp.bus.bus;
            this.bus.on("notification", this, this.on_notification);
        },
        start: function(){
            var self = this;
            // ui
            this.on("change:right_offset", this.conv_manager, _.bind(function() {
                this.conv_manager.set("right_offset", this.get("right_offset"));
            }, this));
            $(window).scroll(_.bind(this.position_compute, this));
            $(window).resize(_.bind(this.position_compute, this));
            this.position_compute();
            this.$el.css("right", -this.$el.outerWidth());
            // bind events
            this.on("change:current_search", this, this.user_search);

            // TODO : remove this feature, and create group conversation !
            // add a drag & drop listener
            /*
            self.conv_manager.on("im_session_activated", self, function(conv) {
                conv.$el.droppable({
                    drop: function(event, ui) {
                        conv.add_user(ui.draggable.data("user"));
                    }
                });
            });
            */

            // fetch the unread message and the recent activity (e.i. to re-init in case of refreshing page)
            return openerp.session.rpc("/im_chat/init", {}).then(function(notifications){
                _.each(notifications, function(notif){
                    self.conv_manager.on_notification(notif);
                });
                // start polling
                self.bus.start_polling();
            });
        },
        on_notification: function(notification){
            var channel = notification[0];
            var message = notification[1];
            // user status notification
            if(channel[1] === 'im_chat.presence'){
                if(message.im_status){
                    this.user_update_status([message]);
                }
            }
        },
        // ui
        position_compute: function(){
            var $topbar = window.$('#oe_main_menu_navbar'); // .oe_topbar is replaced with .navbar of bootstrap3
            var top = $topbar.offset().top + $topbar.height();
            top = Math.max(top - $(window).scrollTop(), 0);
            this.$el.css("top", top);
            this.$el.css("bottom", 0);
        },
        switch_display: function(){
            this.position_compute();
            var fct =  _.bind(function(place) {
                this.set("right_offset", place + this.$el.outerWidth());
                this.$(".o_im_chat_user_search_box").focus();
            }, this);
            var opt = {
                step: fct,
            };
            if(this.shown){
                this.$el.animate({
                    right: -this.$el.outerWidth(),
                }, opt);
            }else{
                if(! openerp.bus.bus.activated){
                    this.do_warn(_t("Instant Messaging is not activated on this server. Try later."));
                    return;
                }
                this.user_search(); // update the list of user status when show the IM
                this.$el.animate({
                    right: 0,
                }, opt);
            }
            this.shown = !this.shown;
        },
        input_change: function(){
            this.set("current_search", this.$(".o_im_chat_user_search_box").val());
        },
        // user methods
        user_search: function(e){
            var self = this;
            var Users = new openerp.Model('res.users');
            return Users.call('im_search', [this.get("current_search"), USERS_LIMIT]).then(function(result){
                self.$(".oe_im_input").val("");
                var old_widgets = self.user_widgets;
                self.user_widgets = {};
                _.each(result, function(user){
                    user.image_url = openerp.session.url('/web/binary/image', {model:'res.users', field: 'image_small', id: user.id});
                    var widget = new openerp.im_chat.UserWidget(self, user);
                    widget.on("user_clicked", self, self.user_clicked);
                    widget.appendTo(self.$(".o_im_chat_users"));
                    self.user_widgets[user.id] = widget;
                });
                _.each(old_widgets, function(w){
                    w.destroy();
                });
            });
        },
        user_clicked: function(user_id){
            var self = this;
            var Sessions = new openerp.web.Model("im_chat.session");
            return Sessions.call("session_get", [user_id]).then(function(session) {
                self.conv_manager.activate_session(session, true);
            });
        },
        user_update_status: function(user_list){
            var self = this;
            _.each(users_list, function(el) {
                if(self.widgets[el.id]){
                    self.widgets[el.id].set("im_status", el.im_status);
                }
            });
        }
    });


    instance.im_chat.ImTopButton = openerp.Widget.extend({
        template: 'im_chat.ImTopButton',
        events: {
            "click": "clicked",
        },
        start: function(parent) {
            // Create the InstantMessaging widget and put it in the DOM
            var im = new instance.im_chat.InstantMessaging(self);
            instance.im_chat.single = im;
            im.appendTo(openerp.client.$el);
            // Bind the click action to the ImTopButton
            this.on("clicked", im, im.switch_display);
            return this._super(parent);
        },
        clicked: function(ev) {
            ev.preventDefault();
            this.trigger("clicked");
        },
    });


    // Guard: only for the backend
    if (openerp.web && openerp.web.Model) {
        // Put the ImTopButton widget in the systray menu if the user is an employee
        var Users = new openerp.web.Model('res.users');
        Users.call('has_group', ['base.group_user']).done(function(is_employee) {
            if (is_employee) {
                openerp.web.SystrayItems.push(openerp.im_chat.ImTopButton);
            }
        });
    }

    return instance.im_chat;
})();
