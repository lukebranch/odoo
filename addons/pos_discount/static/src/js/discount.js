odoo.define('pos_discount.pos_discount', ['point_of_sale.screens'], function (require) {
"use strict";

var screens = require('point_of_sale.screens');

var DiscountButton = screens.ActionButtonWidget.extend({
    template: 'DiscountButton',
    button_click: function(){
        var order    = this.pos.get_order();
        var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
        var discount = - this.pos.config.discount_pc/ 100.0 * order.get_total_with_tax();
        if( discount < 0 ){
            order.add_product(product, { price: discount });
        }
    },
});

screens.define_action_button({
    'name': 'discount',
    'widget': DiscountButton,
    'condition': function(){
        return this.pos.config.discount_product_id;
    },
});


});
