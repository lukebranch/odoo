odoo.define('website_blog.editor', ['web.ajax', 'web.core', 'web.Model', 'website.contentMenu', 'website.define', 'website.editor', 'website.snippets.editor', 'website.website'], function (require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var Model = require('web.Model');
var contentMenu = require('website.contentMenu');
var website_define = require('website.define');
var editor = require('website.editor');
var snippet_editor = require('website.snippets.editor');
var website = require('website.website');


var _t = core._t;

contentMenu.EditorBarContent.include({
    new_blog_post: function() {
        website.prompt({
            id: "editor_new_blog",
            window_title: _t("New Blog Post"),
            select: "Select Blog",
            init: function () {
                return new Model('blog.blog')
                        .call('name_search', [], { context: website.get_context() });
            },
        }).then(function (cat_id) {
            document.location = '/blog/' + cat_id + '/post/new';
        });
    },
});

website.if_dom_contains('.website_blog', function() {

    editor.EditorBar.include({
        edit: function () {
            $('.popover').remove();
            this._super();
        },
        save : function() {
            var res = this._super();
            if ($('.cover').length) {
                ajax.jsonRpc("/blog/post_change_background", 'call', {
                    'post_id' : $('#blog_post_name').attr('data-oe-id'),
                    'image' : $('.cover').css('background-image').replace(/url\(|\)|"|'/g,''),
                });
            }
            return res;
        },
    });
    snippet_editor.options.many2one.include({
        select_record: function (li) {
            var self = this;
            this._super(li);
            if (this.$target.data('oe-field') === "author_id") {
                var $nodes = $('[data-oe-model="blog.post"][data-oe-id="'+this.$target.data('oe-id')+'"][data-oe-field="author_avatar"]');
                $nodes.each(function () {
                    var $img = $(this).find("img");
                    var css = window.getComputedStyle($img[0]);
                    $img.css({ width: css.width, height: css.height });
                    $img.attr("src", "/website/image/res.partner/"+self.ID+"/image");
                });
                setTimeout(function () { $nodes.removeClass('o_dirty'); },0);
            }
        }
    });

    snippet_editor.options.website_blog = snippet_editor.Option.extend({
        start : function(type, value, $li) {
            this._super();
            this.src = this.$target.css("background-image").replace(/url\(|\)|"|'/g,'').replace(/.*none$/,'');
            this.$image = $('<image src="'+this.src+'">');
        },
        clear : function(type, value, $li) {
            if (type !== 'click') return;
            this.src = null;
            this.$target.css({"background-image": '', 'min-height': $(window).height()});
            this.$image.removeAttr("src");
        },
        change : function(type, value, $li) {
            if (type !== 'click') return;
            var self = this;
            var editor  = new editor.MediaDialog(this.$image, this.$image[0], {only_images: true});
            editor.appendTo('body');
            editor.on('saved', self, function (event, img) {
                var url = self.$image.attr('src');
                self.$target.css({"background-image": url ? 'url(' + url + ')' : "", 'min-height': $(window).height()});
            });
        },
    });

    website_define.enable();
    define(['summernote/summernote'], function () {
        var enter = $.summernote.pluginEvents.enter;
        $.summernote.pluginEvents.enter = function (event, editor, layoutInfo) {
            enter.call(this, event, editor, layoutInfo);

            var r = $.summernote.core.range.create();
            var node = $.summernote.core.dom.node(r.sc);
            var $nodes = $(node).data('chatter-id') && $("p[data-chatter-id='"+$(node).data('chatter-id')+"']", layoutInfo.editable()) || $();
            if($nodes.length > 1) {
                $nodes.last().removeAttr('data-chatter-id');
            }
        };
    });
    website_define.disable();

});

});
