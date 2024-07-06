odoo.define('multi_uom_pos_extend.ButtonChangeUom', function(require){

var models = require('point_of_sale.models');
var Component = require('point_of_sale.PosComponent');
var Registries = require('point_of_sale.Registries');
var ProductScreen = require('point_of_sale.ProductScreen');
var { useListener } = require('web.custom_hooks');
var { Gui } = require('point_of_sale.Gui');

class ButtonChangeUom extends Component{
    constructor() {
        super(...arguments);
        useListener('click', this._onClick);
    }
    _onClick(){
        var order = this.env.pos.get_order();
        var selectedOrderline = order.selected_orderline;
        if(selectedOrderline){
            var product = selectedOrderline.product;
            var multi_uom_lines = this.env.pos.multi_uom_line_by_product_id[product.id];
            var pricelist_data  = this.env.pos.uom_pricelist_items;
            var price=0;
            multi_uom_lines = multi_uom_lines.map(l => {
                var check_pricelist_data = pricelist_data.filter(zaw => zaw.uom_id[0] === l.uom_id[0] && zaw.product_id[0] === product.id);

                var keysSorted = check_pricelist_data.sort((a, b) => parseFloat(a.pricelist_qty) - parseFloat(b.pricelist_qty));
                if (keysSorted.length >=1){
                    console.log('selected order line',selectedOrderline.quantity)
                    console.log('fixed_price',keysSorted)
                    var last_index = keysSorted.length - 1;
                    for (let i = 0; i < keysSorted.length; i++) {

                          if (keysSorted[i].fixed_price == 0) {
                              price = keysSorted[i].product_list_price;
                          }
                          else{
                                if (selectedOrderline.quantity == keysSorted[i].min_quantity){
                                         price = keysSorted[i].fixed_price;
                                }else if (selectedOrderline.quantity > keysSorted[0].min_quantity){
                                          price = keysSorted[0].fixed_price;
                                }else if (selectedOrderline.quantity < keysSorted[0].min_quantity && selectedOrderline.quantity > 1){
                                          price = keysSorted[1].fixed_price;
                                }else if (selectedOrderline.quantity < keysSorted[0].min_quantity && keysSorted[i].min_quantity > selectedOrderline.quantity){
                                          price = keysSorted[i].fixed_price
                                }
                          }
                        }
                }
                else{
                   var price = product.get_price(order.pricelist, l.ratio, 0, l);
                }
                return  {...l, price: price};
            });
            multi_uom_lines.sort((a, b) => a.ratio > b.ratio);
            
            if(multi_uom_lines.length > 0){
                Gui.showPopup('ChangeUomPopup', {
                    title: 'Select a Unit of Measure.',
                    list: multi_uom_lines,
                });
            }
            else{
                Gui.showPopup('ErrorPopup', {
                    confirmText: 'OK',
                    cancelText: 'Cancel',
                    title: 'Error',
                    body: 'Selected product is not available for multi UOM.',
                });
            }
        }
        else{
            Gui.showPopup('ErrorPopup', {
                confirmText: 'OK',
                cancelText: 'Cancel',
                title: 'Error',
                body: 'Please select an order line first.',
            });
        }
    }
}

ButtonChangeUom.template = 'ButtonChangeUom';

ProductScreen.addControlButton({
    component: ButtonChangeUom,
    condition: function () {
        return true;
    },
});
Registries.Component.add(ButtonChangeUom);
return ButtonChangeUom;

});