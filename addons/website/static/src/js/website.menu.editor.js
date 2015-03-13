(function () {
    'use strict';
    var website = openerp.website;

    website.snippet.BuildingBlock.include({

        start: function() {
            this._super();
            this.init_edit_menu();
        },

        open_dropdown_hover: function(snippet){
            if(!snippet.hasClass('oe_current_dropdown')){
                $('.oe_current_dropdown').children('ul').css('visibility', 'hidden');
                $('.oe_current_dropdown').removeClass("oe_current_dropdown");
                snippet.addClass("oe_current_dropdown");
                snippet.children('ul').css('visibility', 'visible');
                this.make_active(false);
            }
        },

        init_edit_menu: function(){
            var self = this;
            $("#wrapwrap").click(function(event){
                if(!$(event.target).hasClass('.dropdown-menu') &&
                    $(event.target).parents('.dropdown-menu').length === 0){
                    $('.oe_current_dropdown').children('ul').css('visibility', 'hidden');
                    $('.oe_current_dropdown').removeClass("oe_current_dropdown");
                }
            });
            $(".s_menu_parent").each(function(){
                self.transform_menu_dropdown($(this));
            });
            $(".top_menu").addClass('o_dirty o_editable');
        },

        transform_menu_dropdown: function(el){
            var self = this;
            el.removeClass('o_editable o_is_inline_editable');
            el.removeAttr("data-oe-xpath data-oe-type data-oe-expression data-oe-field data-oe-id data-oe-translate data-oe-model");
            el.not(":has(ul)").children('a').append('<span class="caret"></span>');
            el.not(":has(ul)").children('a').after('<ul class="dropdown-menu o_editable_menu" role="menu"></ul>');
            el.children('a').removeAttr('data-toggle class');
            el.addClass('open');
            el.children('ul').css('visibility', 'hidden');
            el.droppable({
                over:function(){self.open_dropdown_hover($(this));}
            });
            el.on("mouseenter", function () {
                self.open_dropdown_hover($(this));
            });
        },
    });


    website.EditorBar.include({
        saveElement: function($el){
            if($el.hasClass('top_menu')){
                this.clean_menu($el);
                var markup = $el.prop('outerHTML');
                return openerp.jsonRpc('/website/save_menu', 'save_menu', {
                    view_id: $el.data('oe-id'),
                    value: markup,
                    xpath: $el.data('oe-xpath') || null,
                    context: website.get_context(),
                });
            }else{
                return this._super($el);
            }
        },

        clean_menu: function($el){
            $el.find(".s_menu_parent").each(function(){
                var el = $(this);
                el.children('ul').css('visibility', '');
                el.off('mouseenter');
                el.removeClass('open');
                if(el.children('ul').children().length === 0){
                    el.children('a').children('.caret').remove();
                    el.children('ul').remove();
                    el.children('.dropdown-menu').remove();
                }else{
                    el.children('a').attr('data-toggle', 'dropdown');
                    el.children('a').addClass('dropdown-toggle');
                }
            });
            $el.find(".ui-droppable").removeClass("ui-droppable");
            $el.find(".oe_current_dropdown").removeClass("oe_current_dropdown");
        },
    });

    website.snippet.options.menu_link = website.snippet.Option.extend({
        start: function(){
            this._super();
            var link = this.$target.children('a');
            var new_range = $.summernote.core.range.createFromNode(link[0]);
            new_range.select();
            var linkInfo = {range: new_range};
            var editor = new website.editor.LinkDialog(link, linkInfo);
            editor.appendTo(document.body);

            editor.on("save", this, function (linkInfo) {
                var link = this.$target.children('a');
                link.addClass(linkInfo.className);
                link.removeClass('o_default_snippet_text');
                link.text(linkInfo.text);
                link.attr('href',linkInfo.url);
                if(linkInfo.newWindow){
                    link.attr('target', '_blank');
                }
            });
        },
    });

    website.snippet.options.menu_parent = website.snippet.Option.extend({
        start: function(){
            this._super();
            var link = this.$target.children('a');
            var new_range = $.summernote.core.range.createFromNode(link[0]);
            new_range.select();
            var linkInfo = {range: new_range};
            //TODO error with the open in new window option, when desactivated the change in not done in the html
            var editor = new website.editor.LinkDialog(link, linkInfo);
            editor.appendTo(document.body);
            var self = this;
            editor.on("save", this, function (linkInfo) {
                var link = this.$target.children('a');
                link.addClass(linkInfo.className);
                link.removeClass('o_default_snippet_text');
                link.text(linkInfo.text);
                link.attr('href',linkInfo.url);
                if(linkInfo.newWindow){
                    link.attr('target', '_blank');
                }
                self.BuildingBlock.transform_menu_dropdown(this.$target);
            });
        },
    });

})();