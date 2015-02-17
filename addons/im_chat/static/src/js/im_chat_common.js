(function(){

    "use strict";

    var _t = openerp._t;
    var _lt = openerp._lt;
    var QWeb = openerp.qweb;
    var NBR_LIMIT_HISTORY = 20;
    var im_chat = openerp.im_chat = {};

    im_chat.ConversationManager = openerp.Widget.extend({
        init: function(parent, options) {
            var self = this;
            this._super(parent);
            this.options = _.clone(options) || {};
            _.defaults(this.options, {
                inputPlaceholder: _t("Say something..."),
                defaultMessage: null,
                defaultUsername: _t("Visitor"),
                force_open: false,
                load_history: true,
                focus: false,
            });
            // business
            this.sessions = {};
            this.bus = openerp.bus.bus;
            this.bus.on("notification", this, this.on_notification);
            this.bus.options["im_presence"] = true;

            // ui
            this.set("right_offset", 0);
            this.set("bottom_offset", 0);
            this.on("change:right_offset", this, this.calc_positions);
            this.on("change:bottom_offset", this, this.calc_positions);

            this.set("window_focus", true);
            this.on("change:window_focus", self, function(e) {
                self.bus.options["im_presence"] = self.get("window_focus");
            });
            this.set("waiting_messages", 0);
            this.on("change:waiting_messages", this, this.window_title_change);
            $(window).on("focus", _.bind(this.window_focus, this));
            $(window).on("blur", _.bind(this.window_blur, this));
            this.window_title_change();
        },
        on_notification: function(notification, options) {
            var self = this;
            var channel = notification[0];
            var message = notification[1];
            var regex_uuid = new RegExp(/(\w{8}(-\w{4}){3}-\w{12}?)/g);

            // Concern im_chat : if the channel is the im_chat.session or im_chat.status, or a 'private' channel (aka the UUID of a session)
            if((Array.isArray(channel) && (channel[1] === 'im_chat.session' || channel[1] === 'im_chat.presence')) || (regex_uuid.test(channel))){
                // message to display in the chatview
                if (message.type === "message" || message.type === "meta") {
                    self.message_receive(message);
                }
                // activate the received session
                if(message.uuid){
                    this.session_apply(message, options);
                }
                // TODO : could be remove ?
                // user status notification
                if(message.im_status){
                    self.trigger("im_new_user_status", [message]);
                }
            }
        },

        // window focus unfocus beep and title
        window_focus: function() {
            this.set("window_focus", true);
            this.set("waiting_messages", 0);
        },
        window_blur: function() {
            this.set("window_focus", false);
        },
        window_beep: function() {
            if (typeof(Audio) === "undefined") {
                return;
            }
            var audio = new Audio();
            var ext = audio.canPlayType("audio/ogg; codecs=vorbis") ? ".ogg" : ".mp3";
            var kitten = jQuery.deparam !== undefined && jQuery.deparam(jQuery.param.querystring()).kitten !== undefined;
            audio.src = openerp.session.url("/im_chat/static/src/audio/" + (kitten ? "purr" : "ting") + ext);
            audio.play();
        },
        window_title_change: function() {
            if (this.get("waiting_messages") !== 0) {
                this.window_beep();
            }
        },

        // sessions and messages
        session_apply: function(active_session, options){
            // options used by this function : force_open and focus (load_history can be usefull)
            var self = this;
            options = _.extend(_.clone(this.options), options || {});
            // force open
            var session = _.clone(active_session);
            if(options['force_open']){
                session.state = 'open';
            }
            // create/get the conversation widget
            var conv = this.sessions[session.uuid];
            if (! conv) {
                if(session.state !== 'closed'){
                    conv = new im_chat.Conversation(this, this, session, options);
                    conv.appendTo($("body"));
                    conv.on("destroyed", this, _.bind(this.session_delete, this));
                    this.sessions[session.uuid] = conv;
                    this.calc_positions();
                }
            }else{
                conv.set("session", session);
            }
            // if force open, broadcast it
            if(options['force_open'] && active_session.state !== 'open'){
                conv.session_update_state('open');
            }
            // apply the focus
            if (options['focus']){
                conv.focus();
            }
            return conv;
        },
        session_delete: function(uuid){
            delete this.sessions[uuid];
            this.calc_positions();
        },
        message_receive: function(message) {
            var self = this;
            var session_id = message.to_id[0];
            var uuid = message.to_id[1];
            var from_id = message['from_id'] ? message['from_id'][0] : false;
            if (! this.get("window_focus") && from_id != this.get_current_uid()) {
                this.set("waiting_messages", this.get("waiting_messages") + 1);
            }
            var conv = this.sessions[uuid];
            if(!conv){
                // fetch the session, and init it with the message
                var def_session = new openerp.Model("im_chat.session").call("session_info", [], {"ids" : [session_id]}).then(function(session){
                    conv = self.session_apply(session, {'force_open': true});
                    conv.message_receive(message);
                });
            }else{
                conv.message_receive(message);
            }
        },
        get_current_uid: function(){
            return openerp.session && !_.isUndefined(openerp.session.uid) ? openerp.session.uid : false;
        },
        calc_positions: function() {
            var self = this;
            var current = this.get("right_offset");
            _.each(this.sessions, function(s) {
                s.set("bottom_position", self.get("bottom_offset"));
                s.set("right_position", current);
                current += s.$().outerWidth(true);
            });
        },
        destroy: function() {
            $(window).off("unload", this.unload);
            $(window).off("focus", this.window_focus);
            $(window).off("blur", this.window_blur);
            return this._super();
        }
    });

    im_chat.Conversation = openerp.Widget.extend({
        // TODO JEM: remove 'oe_im_chatview'. Kept for backward compatibility
        className: "oe_im_chatview o_im_chatview",
        events: {
            "keydown input": "keydown",
            "click .button_close": "click_close",
            "click .o_im_chatview_header": "click_header"
        },
        init: function(parent, c_manager, session, options) {
            this._super.apply(this, arguments);
            this.c_manager = c_manager;
            this.options = options || {};
            // business
            this.loading_history = true;
            this.set("messages", []);
            this.set("session", session);
            // ui
            this.set("right_position", 0);
            this.set("bottom_position", 0);
            this.set("pending", 0);
            this.inputPlaceholder = this.options.inputPlaceholder;
        },
        start: function() {
            var self = this;
            self._super.apply(this, arguments);
            self.prepare_action_menu();
            // ui
            self.$().append(openerp.qweb.render("im_chat.Conversation", {widget: self}));
            self.on("change:right_position", self, self.calc_pos);
            self.on("change:bottom_position", self, self.calc_pos);
            self.on("change:pending", self, _.bind(function() {
                if (self.get("pending") === 0) {
                    self.$(".o_im_chatview_header.nbr_messages").text("");
                } else {
                    self.$(".o_im_chatview_header.nbr_messages").text("(" + self.get("pending") + ")");
                }
            }, self));
            self.full_height = self.$().height();
            self.calc_pos();
            // business
            self.on("change:session", self, self.session_update);
            self.on("change:messages", self, self.render_messages);
            self.bind_action_menu();
            if(self.options['load_history']){ // load history if asked
                self.message_history();
            }
            self.$('.o_im_chatview_content').on('scroll', function(){
                if($(this).scrollTop() === 0){
                    self.message_history();
                }
            });
            // prepare the header and the correct state
            self.session_update();
        },
        // action menu
        _add_action: function(label, style_class, icon_fa_class, callback){
            this.actions.push({
                'label': label,
                'class': style_class,
                'icon_class': icon_fa_class,
                'callback': callback,
            });
        },
        prepare_action_menu: function(){
            // override this method to add action with _add_action()
            this.actions = [];
        },
        bind_action_menu: function(){
            var self = this;
            _.each(this.actions, function(action){
                if(action.callback){
                    self.$('.button_option_group .' + action.class).on('click', _.bind(action.callback, self));
                }
            });
        },
        // ui
        show: function(){
            this.$().animate({
                height: this.full_height
            });
            this.set("pending", 0);
        },
        hide: function(){
            this.$().animate({
                height: this.$(".o_im_chatview_header").outerHeight()
            });
        },
        calc_pos: function() {
            this.$().css("right", this.get("right_position"));
            this.$().css("bottom", this.get("bottom_position"));
        },
        // session
        session_update_state: function(state){
            return new openerp.Model("im_chat.session").call("update_state", [], {"uuid" : this.get("session").uuid, "state" : state});
        },
        session_update: function(){
            var self = this;
            // built the name
            var names = [];
            _.each(this.get("session").users, function(user){
                if(self.c_manager.get_current_uid() !== user.id){
                    names.push(user.name);
                }
            });
            this.$(".o_im_chatview_header .header_name").text(names.join(", "));
            this.$(".o_im_chatview_header .header_name").attr('title', names.join(", "));
            // update the fold state
            if(this.get("session").state){
                if(this.get("session").state === 'closed'){
                    this.destroy();
                }else{
                    if(this.get("session").state === 'open'){
                        this.show();
                    }else{
                        this.hide();
                    }
                }
            }
        },
        // messages
        message_history: function(){
            var self = this;
            if(this.loading_history){
                var data = {uuid: self.get("session").uuid, limit: NBR_LIMIT_HISTORY};
                if(_.first(this.get("messages"))){
                    data["last_id"] = _.first(this.get("messages")).id;
                }
                openerp.session.rpc("/im_chat/history", data).then(function(messages){
                    if(messages){
                        self.message_insert(messages);
    					if(messages.length != NBR_LIMIT_HISTORY){
                            self.loading_history = false;
                        }
                    }else{
                        self.loading_history = false;
                    }
                });
            }
        },
        message_receive: function(message) {
            if (this.get('session').state === 'open') {
                this.set("pending", 0);
            } else {
                this.set("pending", this.get("pending") + 1);
            }
            this.message_insert([message]);
            this._go_bottom();
        },
        message_send: function(message, type) {
            var self = this;
            var send_it = function() {
                return openerp.session.rpc("/im_chat/post", {uuid: self.get("session").uuid, message_type: type, message_content: message});
            };
            var tries = 0;
            send_it().fail(function(error, e) {
                e.preventDefault();
                tries += 1;
                if (tries < 3)
                    return send_it();
            });
        },
        message_insert: function(messages){
        	var self = this;
            // avoid duplicated messages
        	messages = _.filter(messages, function(m){ return !_.contains(_.pluck(self.get("messages"), 'id'), m.id);});
            // preporcess message to make sure the from_id is an array and the date format is correct (+ correct timezone)
            _.map(messages, function(m){
                if(!m.from_id){
                    m.from_id = [false, self.get_anonymous_name()];
                }
                m.from_id[2] = openerp.session.url(_.str.sprintf("/im_chat/image/%s/%s", self.get('session').uuid, m.from_id[0]));
                m.create_date = moment.utc(m.create_date).format('YYYY-MM-DD HH:mm:ss');
                return m;
            });
            messages = _.sortBy(this.get("messages").concat(messages), function(m){ return m.id; });
           	this.set("messages", messages);
        },
        render_messages: function(){
            var self = this;
            var messages = this.get("messages");
            // add display informations
            _.map(messages, function(m){
                m['hour'] = moment(m.create_date).format('HH:mm');
                m['class'] = 'left';
                console.log("m.from_id[0] ",m.from_id[0]);
                console.log("sfds", self.c_manager.get_current_uid());
                if(m.from_id[0] === self.c_manager.get_current_uid()){
                    m['class'] = 'right';
                }
                return m;
            });
            // group the messages by day
            var grouped_messages = _.groupBy(messages, function(m){
                return m.create_date.split(" ")[0];
            });
            // generate date labels
            var date_labels = {};
            _.each(_.keys(grouped_messages), function(d){
                date_labels[d] = moment(d).format('LL');
            });
            // group messages by minute, then find suite of same user
            var msg_group_date_minute = {};
            var msg_group_date_day = _.clone(grouped_messages);
            _.each(_.keys(msg_group_date_day), function(msg_day){
                var messages = msg_group_date_day[msg_day];
                msg_group_date_minute[msg_day]
                var messages_by_min = _.groupBy(messages, function(m){
                    return moment(m.create_date).format('HH:mm');
                });
                var group_by_user_minute = {};
                _.each(_.keys(messages_by_min), function(minute){
                    group_by_user_minute[minute] = self._message_group_by_user(messages_by_min[minute]);
                });
                msg_group_date_minute[msg_day] = group_by_user_minute
            });
            // render messages template
            this.$('.container_messages').html($(openerp.qweb.render("im_chat.Conversation_content", {
                'messages_grouped': msg_group_date_minute,
                'date_labels': date_labels
            })));
        },
        _message_group_by_user: function(messages){
            var result = [];
            var last_uid = -1;
            var current = [];
            _.each(messages, function(m){
                if(m.from_id[0] !== last_uid){
                    if(!_.isEmpty(current)){
                        result.push(current);
                    }
                    current = [];
                }
                current.push(m);
                last_uid = m.from_id[0];
            });
            if(!_.isEmpty(current)){
                result.push(current);
            }
            return result;
        },
        // utils and events
        keydown: function(e) {
            if(e && e.which == 27) {
                if(this.$el.prev().find('.o_im_chat_input').length > 0){
                    this.$el.prev().find('.o_im_chat_input').focus();
                }else{
                    this.$el.next().find('.o_im_chat_input').focus();
                }
                e.stopPropagation();
                this.session_update_state('closed');
            }
            if(e && e.which !== 13) {
                return;
            }
            var mes = this.$("input").val();
            if (! mes.trim()) {
                return;
            }
            this.$("input").val("");
            this.message_send(mes, "message");
        },
        _go_bottom: function() {
            this.$(".o_im_chatview_content").scrollTop(this.$(".o_im_chatview_content").get(0).scrollHeight);
        },
        get_anonymous_name: function(){
            var name = this.options["defaultUsername"];
            _.each(this.get('session').users, function(u){
                if(!u.id){
                    name = u.name;
                }
            });
            return name;
        },
        focus: function() {
            this.$(".o_im_chat_input").focus();
        },
        click_header: function(event){
            var classes = event.target.className.split(' ');
            if(_.contains(classes, 'header_name') || _.contains(classes, 'o_im_chatview_header')){
                this.session_update_state();
            }
        },
        click_close: function(event) {
            this.session_update_state('closed');
        },
        destroy: function() {
            this.trigger("destroyed", this.get('session').uuid);
            return this._super();
        }
    });

    return im_chat;
})();
