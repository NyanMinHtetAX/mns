odoo.define('pos_stock_realtime.ProductScreenExtend', function(require) {
    'use strict';
    
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { Gui } = require('point_of_sale.Gui');
    const NumberBuffer = require('point_of_sale.NumberBuffer');

    const ProductScreenExtend = ProductScreen => class extends ProductScreen {
        async _clickProduct(event) {
            const product = event.detail;
            const onhand_qty = product.get_qty_onhand();
            const config = this.env.pos.config;
            console.log('product.type', product.type);
            if (!config.allow_out_of_stock && product.type === 'product'){
                if(onhand_qty <= config.limit_qty){
                    Gui.showPopup('ErrorPopup', {
                        confirmText: 'OK',
                        cancelText: 'Cancel',
                        title: 'OUT OF STOCK!',
                        body: 'Current quantity onhand is lower than the minimum quantity defined in the configuration.',
                    });
                }
                else{
                    if (!this.currentOrder) {
                        this.env.pos.add_new_order();
                    }
                    const options = await this._getAddProductOptions(product);
                    // Do not add product if options is undefined.
                    if (!options) return;
                    // Add the product after having the extra information.
                    this.currentOrder.add_product(product, options);
                    NumberBuffer.reset();
                }
            }
            else{
                if (!this.currentOrder) {
                    this.env.pos.add_new_order();
                }
                const options = await this._getAddProductOptions(product);
                // Do not add product if options is undefined.
                if (!options) return;
                // Add the product after having the extra information.
                this.currentOrder.add_product(product, options);
                NumberBuffer.reset();
            }

        }
    }


    Registries.Component.extend(ProductScreen, ProductScreenExtend);

    return ProductScreenExtend;
});
