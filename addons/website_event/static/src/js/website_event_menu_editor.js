(function () {
    'use strict';
    var website = openerp.website;
    website.add_template_file('/website_event/static/src/xml/website_event.menu_snippets.xml');

    website.snippet.BuildingBlock.include({
        start: function() {
            this._super();
        },

        init_edit_menu: function(){
            this._super();
            if($(".s_events").length > 0){
                this.change_snippet_events();
            }
        },

        change_snippet_events: function(){
            $(".s_events").replaceWith(openerp.qweb.render("website_event.menu_events"));
        },
    });

    website.EditorBar.include({
        saveElement: function($el){
            var self = this;
            var _super = this._super;
            if($el.hasClass('top_menu') && $el.find('.s_menu_events').length > 0){
                return openerp.jsonRpc('/website_event/menu/events','get_events').then(function(results){
                    self.insert_events($el, results);
                    self._super = _super;
                    self._super($el);
                 });
            }else{
                return this._super($el);
            }
        },

        insert_events: function($el, events){
            var self = this;
            $el.find(".s_menu_events").each(function(){
                var el = $(this);
                var ul = $(document.createElement("ul"));
                ul.addClass('s_events');
                el.after(ul);
                $.each(events, function(){
                    ul.append("<li ><a href='"+this.url+"'><span>" + this.name + "</span></a></li>");
                });
                el.remove();
            });
        }
    });

})();