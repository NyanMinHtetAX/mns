odoo.define('packaging_barcodes.ProductsWidgetControlPanel', function (require) {
    'use strict';

	var Registries = require('point_of_sale.Registries');
    const ProductsWidgetControlPanel = require('point_of_sale.ProductsWidgetControlPanel');

	var ProductsWidgetControlPanelExtend = ProductsWidgetControlPanel => class extends ProductsWidgetControlPanel{
        updateSearch(event) {
            var res = super.updateSearch(...arguments);
            // 
            var db = this.env.pos.db
            var product_barcodes = Object.keys(db.product_by_barcode || {})
            var product_packaging_barcodes = Object.keys(db.product_packaging_by_barcode || {})
            var barcodes = [...product_barcodes, ...product_packaging_barcodes]
            var userInput = event.target.value;

            if(barcodes.includes(userInput)) {
            	var uom_pricelist_by_product = this.env.pos.uom_pricelist_by_product || {}
            	var product_by_barcode = db.product_by_barcode || {}
            	var product_packaging_by_barcode = db.product_packaging_by_barcode || {}
            	var pricelist_id = this.env.pos?.config?.pricelist_id[0]
            	var package_ = product_packaging_by_barcode[userInput];
            	var product_ = product_by_barcode[userInput] || db.get_product_by_id(package_?.product_id[0]);

            	var multi_uom_line_id = undefined
            	var price = undefined
            	if(package_ && pricelist_id && package_.use_in_pos === true)
                {
                	multi_uom_line_id = package_.multi_uom_id[0]
                	var key = `${package_.product_id[0]}-${multi_uom_line_id}-${pricelist_id}`;
                	price = this.env.pos.uom_pricelist_by_product[key]

		            if (!this.env.pos.get_order()) {
		                this.env.pos.add_new_order();
		            }
                    this.env.pos.get_order().add_product(product_, {'multi_uom_line_id': multi_uom_line_id, 'price': price})
                    event.target.value = '';
                    this.trigger('clear-search')
                }
                
                if(package_ === undefined) {
                    this.env.pos.get_order().add_product(product_, {})
                    event.target.value = '';
                    this.trigger('clear-search')
                }
            }

            return res
        }
    };
	Registries.Component.extend(ProductsWidgetControlPanel, ProductsWidgetControlPanelExtend);

	return ProductsWidgetControlPanelExtend;
});
