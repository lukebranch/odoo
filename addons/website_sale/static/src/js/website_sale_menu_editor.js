(function () {
    'use strict';
    var website = openerp.website;
    website.add_template_file('/website_sale/static/src/xml/website_sale.menu_snippets.xml');

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
            $(".s_products").replaceWith(openerp.qweb.render("website_sale.menu_products"));
        },
    });

    website.EditorBar.include({
        saveElement: function($el){
            if($el.hasClass('top_menu') && $el.find('.s_menu_products').length > 0){
                this.clean_menu($el);
                var self = this;
                return openerp.jsonRpc('/website_sale/menu/products','get_products').then(function(results){
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
                return this._super($el);
            }
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