(function () {
    'use strict';
    var website = openerp.website;

    website.snippet.MenuEditor = website.snippet.BuildingBlock.include({

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
            $(".s_menu_parent:not(:has(ul))").children('a').append('<span class="caret"></span>');
            $(".s_menu_parent:not(:has(ul))").children('a').after('<ul class="dropdown-menu o_editable_menu" role="menu"></ul>');
            $(".s_menu_parent").children('a').removeAttr('data-toggle class');
            $(".s_menu_parent").addClass('open o_editable');
            $(".s_menu_parent").children('ul').css('visibility', 'hidden');
            $(".s_menu_parent").droppable({
                over:function(){self.open_dropdown_hover($(this));}
            });
            $("body").on("mouseenter", ".s_menu_parent", function () {
                self.open_dropdown_hover($(this));
            });

            $(".top_menu").addClass('o_dirty o_editable');
        },
    });


    website.EditorBar.include({
        saveElement: function($el){
            debugger;
            if($el.hasClass('top_menu')){
                var markup = $el.prop('outerHTML');
                console.log(markup);
                return openerp.jsonRpc('/website/save_menu', 'save_menu', {
                    value: markup,
                    context: website.get_context(),
                });
            }else{
                return this._super($el);
            }
        }
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
        //TODO exactly same function as menu_link start, put the same code in an external function
        start: function(){
            this._super();
            var link = this.$target.children('a');
            this.$target.addClass('o_editable');
            var new_range = $.summernote.core.range.createFromNode(link[0]);
            new_range.select();
            var linkInfo = {range: new_range};
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
                self.BuildingBlock.init_edit_menu();
            });
        },

        clean_for_save: function(){
            this.$target.children('ul').css('visibility', '');
            this.$target.off('mouseenter');
            this.$target.removeClass('open');
            if(this.$target.children('ul').children().length === 0){
                this.$target.children('a').children('.caret').remove();
                this.$target.children('ul').remove();
                this.$target.children('.dropdown-menu').remove();
            }else{
                this.$target.children('a').attr('data-toggle', 'dropdown');
                this.$target.children('a').addClass('dropdown-toggle');
            }
            debugger;
        },
    });

})();