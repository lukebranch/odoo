(function () {
    'use strict';
    var website = openerp.website;
    website.add_template_file('/website_forum/static/src/xml/website_forum.menu_snippets.xml');

    website.snippet.BuildingBlock.include({
        start: function() {
            this._super();
        },

        init_edit_menu: function(){
            this._super();
            if($(".s_forums").length > 0){
                this.change_snippet_forums();
            }
            if($(".s_forum_posts").length > 0){
                this.change_snippet_forum_posts();
            }
        },

        change_snippet_forums: function(){
            $(".s_forums").replaceWith(openerp.qweb.render("website_forum.menu_forums"));
        },

        change_snippet_forum_posts: function(){
            $(".s_forum_posts").replaceWith(openerp.qweb.render("website_forum.menu_forum_posts"));
        },
    });

    website.EditorBar.include({
        saveElement: function($el){
            var self = this;
            var _super = this._super;
            var toCall = [];
            if($el.hasClass('top_menu') && $el.find('.s_menu_forum_posts').length > 0){
                var call1 = new openerp.jsonRpc('/website_forum/menu/forum_posts','get_forum_posts').then(function(results){
                        self.insert_forum_posts($el, results);
                    });
                toCall.push(call1);
            }
            if($el.hasClass('top_menu') && $el.find('.s_menu_forums').length > 0){
                var call2 = new openerp.jsonRpc('/website_forum/menu/forums','get_forums').then(function(results){
                        self.insert_forums($el, results);
                    });
                toCall.push(call2);
            }
            var defer = $.Deferred();
            $.when.apply($, toCall).done(function(result1, result2) {
                self._super = _super;
                self._super($el).then(function(){
                    defer.resolve();
                });
            });
            return defer;
        },

        insert_forum_posts: function($el, forum_posts){
            var self = this;
            $el.find(".s_menu_forum_posts").each(function(){
                var el = $(this);
                var ul = $(document.createElement("ul"));
                ul.addClass('s_forum_posts');
                el.after(ul);
                $.each(forum_posts, function(){
                    ul.append("<li ><a href='"+this.url+"'><span>" + this.name + "</span></a></li>");
                });
                el.remove();
            });
        },

        insert_forums: function($el, forums){
            var self = this;
            $el.find(".s_menu_forums").each(function(){
                var el = $(this);
                var ul = $(document.createElement("ul"));
                ul.addClass('s_forums');
                el.after(ul);
                $.each(forums, function(){
                    ul.append("<li ><a href='"+this.url+"'><span>" + this.name + "</span></a></li>");
                });
                el.remove();
            });
        },
    });

})();