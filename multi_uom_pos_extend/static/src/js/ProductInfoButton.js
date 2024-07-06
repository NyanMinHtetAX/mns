odoo.define('multi_uom_pos_extend.ProductInfoButton', function(require) {
    'use strict';

var ProductInfoButton = require('point_of_sale.ProductInfoButton');
var Registries = require('point_of_sale.Registries');

var ProductInfoButtonExtend = Component => class extends Component{
    onClick() {
        var orderline = this.env.pos.get_order().get_selected_orderline();
        if (orderline) {
            var product = orderline.get_product();
            var quantity = orderline.get_quantity();
            if(orderline.multi_uom_line){
                quantity *= orderline.multi_uom_line.ratio;
            }
            this.showPopup('ProductInfoPopup', { product, quantity });
        }
    }
};

Registries.Component.extend(ProductInfoButton, ProductInfoButtonExtend);

return ProductInfoButtonExtend;
});
