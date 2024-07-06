odoo.define('pos_stock_realtime.extended_models', function (require) {
    "use strict";

var models = require('point_of_sale.models');
var { Gui } = require('point_of_sale.Gui');
var rpc = require('web.rpc');
models.load_fields('product.product', ['onhand_qty','is_check','type']);
models.load_models([{
    model:  'stock.quant',
    fields: ['id', 'product_id', 'location_id', 'quantity'],
    domain: function(){
        return [
            ['location_id.usage', '=', 'internal']
        ];
    },
    loaded: function(self, quants) {
        self.quants = quants;
    }
}]);
models.Product = models.Product.extend({

    get_qty_onhand: function() {
        var totalQty = 0;
        var product_id = this.id;
        var location_id = this.pos.config.stock_location_id[0];
        var stockQuants = this.pos.quants || [];
        var productQuants = stockQuants.filter((quant) => quant.product_id[0] === product_id);
        if (this.pos.config.location_only){
            var finalQuants = productQuants.filter((quant) => quant.location_id[0] === location_id);
        }
        else{
            var finalQuants = productQuants;
        }
        for(var index=0; index < finalQuants.length; index++){
            totalQty += finalQuants[index].quantity
        }
        return totalQty;

    },

    get_config: function(){
        return this.pos.config;
    },
});

 var superOrder = models.Order.prototype;
models.Order = models.Order.extend({

    add_product: async function(product, options){
        if(this._printed){
            this.destroy();
            return this.pos.get_order().add_product(product, options);
        }

        this.assert_editable();
        const onhand_qty = product.get_qty_onhand();
        const config = this.pos.config;
        if (!config.allow_out_of_stock && product.type === 'product'){
            if (product.is_check==true & product.onhand_qty == 0){
                Gui.showPopup('ErrorPopup', {
                    confirmText: 'OK',
                    cancelText: 'Cancel',
                    title: 'OUT OF STOCK!',
                    body: 'Current quantity onhand is lower than the minimum quantity defined in the configuration.',
                });
                return false;
            }
            if(onhand_qty <= 0){
                Gui.showPopup('ErrorPopup', {
                    confirmText: 'OK',
                    cancelText: 'Cancel',
                    title: 'OUT OF STOCK!',
                    body: 'Current quantity onhand is lower than the minimum quantity defined in the configuration.',
                });
                return false;
            }
        }
        return superOrder.add_product.apply(this, arguments);
    },

});


models.load_fields("stock.picking.type", "default_location_src_id");
models.load_fields("product.product", "type");

});
