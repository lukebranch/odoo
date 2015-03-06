(function () {
    'use strict';
    var website = openerp.website;

    website.snippet.BuildingBlock.include({

        start: function() {
            this._super();
        },

        init_edit_menu: function(){
            this._super();
            if($(".s_products").length > 0){
                this.change_snippet_products();
            }
        },

        change_snippet_products: function(){
            //add_template after call render
            //définir dans static src xml le template js
            $(".s_products").replaceWith(openerp.qweb.render("website.menu.products"));
        },
    });


    website.EditorBar.include({
        saveElement: function($el){
            if($el.hasClass('top_menu')){
                this.clean_menu($el);
                if($el.find('.s_menu_products').length > 0){
                    var self = this;
                    return openerp.jsonRpc('/website/menu/products','get_products').then(function(results){
                        self.insert_products($el, results);
                        var markup = $el.prop('outerHTML');
                        console.log(markup);
                        return openerp.jsonRpc('/website/save_menu', 'save_menu', {
                            view_id: $el.data('oe-id'),
                            value: markup,
                            xpath: $el.data('oe-xpath') || null,
                            context: website.get_context(),
                        });
                     });
                }else{
                    var markup = $el.prop('outerHTML');
                    return openerp.jsonRpc('/website/save_menu', 'save_menu', {
                        view_id: $el.data('oe-id'),
                        value: markup,
                        xpath: $el.data('oe-xpath') || null,
                        context: website.get_context(),
                    });
                }   
            }else{
                return this._super($el);
            }
        },

        clean_menu: function($el){
            $el.find("[data-oe-field]").removeAttr("data-oe-type data-oe-expression data-oe-field data-oe-id data-oe-translate data-oe-model");
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

        insert_products: function($el, products){
            var self = this;
            $el.find(".s_menu_products").each(function(){
                var el = $(this);
                var ul = $(document.createElement("ul"));
                ul.addClass('s_products');
                el.after(ul);
                $.each(products, function(){
                    ul.append("<li ><a href='/page/homepage'><span>" + this + "</span></a></li>");
                });
                el.remove();
            });
        }
    });

})();