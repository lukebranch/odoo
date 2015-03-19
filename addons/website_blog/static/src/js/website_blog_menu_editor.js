(function () {
    'use strict';
    var website = openerp.website;
    website.add_template_file('/website_blog/static/src/xml/website_blog.menu_snippets.xml');

    website.snippet.BuildingBlock.include({
        start: function() {
            this._super();
        },

        init_edit_menu: function(){
            this._super();
            if($(".s_blogs").length > 0){
                this.change_snippet_blogs();
            }
            if($(".s_blog_posts").length > 0){
                this.change_snippet_blog_posts();
            }
        },

        change_snippet_blogs: function(){
            $(".s_blogs").replaceWith(openerp.qweb.render("website_blog.menu_blogs"));
        },

        change_snippet_blog_posts: function(){
            $(".s_blog_posts").replaceWith(openerp.qweb.render("website_blog.menu_blog_posts"));
        },
    });

    website.EditorBar.include({
        saveElement: function($el){
            var self = this;
            var _super = this._super;
            var toCall = [];
            if($el.hasClass('top_menu') && $el.find('.s_menu_blog_posts').length > 0){
                var call1 = new openerp.jsonRpc('/website_blog/menu/blog_posts','get_blog_posts').then(function(results){
                        self.insert_blog_posts($el, results);
                    });
                toCall.push(call1);
            }
            if($el.hasClass('top_menu') && $el.find('.s_menu_blogs').length > 0){
                var call2 = new openerp.jsonRpc('/website_blog/menu/blogs','get_blogs').then(function(results){
                        self.insert_blogs($el, results);
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

        insert_blog_posts: function($el, blog_posts){
            var self = this;
            $el.find(".s_menu_blog_posts").each(function(){
                var el = $(this);
                var ul = $(document.createElement("ul"));
                ul.addClass('s_blog_posts');
                el.after(ul);
                $.each(blog_posts, function(){
                    ul.append("<li ><a href='"+this.url+"'><span>" + this.name + "</span></a></li>");
                });
                el.remove();
            });
        },

        insert_blogs: function($el, blogs){
            var self = this;
            $el.find(".s_menu_blogs").each(function(){
                var el = $(this);
                var ul = $(document.createElement("ul"));
                ul.addClass('s_blogs');
                el.after(ul);
                $.each(blogs, function(){
                    ul.append("<li ><a href='"+this.url+"'><span>" + this.name + "</span></a></li>");
                });
                el.remove();
            });
        },
    });

})();