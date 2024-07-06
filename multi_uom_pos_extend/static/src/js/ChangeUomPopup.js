odoo.define('multi_uom_pos_extend.ChangeUomPopup', function(require){

var { Gui } = require('point_of_sale.Gui');
var SelectionPopup = require('point_of_sale.SelectionPopup');
var Registries = require('point_of_sale.Registries');

class ChangeUomPopup extends SelectionPopup {
    async selectItem(itemId) {
        var list = this.props.list;
        for(var record of list){
            var tr = document.getElementById('multi-uom-' + record.id);
            tr.style.color = '';
            tr.style.backgroundColor = '';
        }
        var selectedIdInput = document.getElementById('selectedId');
        var selectedTr = document.getElementById('multi-uom-' + itemId);
        selectedTr.style.backgroundColor = '#b7bded';
        selectedTr.style.color = '#ffffff';
        selectedIdInput.value = itemId;
    }
    async confirm() {
        var selectedMultiUomLineId = parseInt(document.getElementById('selectedId').value);
        var orderLine = this.env.pos.get_order().selected_orderline;
        orderLine.set_multi_uom_line(selectedMultiUomLineId);
        var product = orderLine.product;
        var pricelist_qty = orderLine.get_quantity() * orderLine.multi_uom_line.ratio;
        var pricelist_data  = this.env.pos.uom_pricelist_items;
        var check_price_list_data = pricelist_data.filter(zaw => zaw.uom_id[0] === orderLine.multi_uom_line.uom_id[0] && zaw.product_id[0] === product.id);
        var keysSorted = check_price_list_data.sort((a, b) => parseFloat(a.min_quantity) - parseFloat(b.min_quantity));
        var opposite_price_list_data = check_price_list_data.filter(l => l.min_quantity <= orderLine.get_quantity());
        var last = Object.keys(opposite_price_list_data).pop();
        if(keysSorted.length>=1){
            if(orderLine.get_quantity() >1 ){
                var  divided_by_qty = (opposite_price_list_data[last].fixed_price / orderLine.quantity);
                orderLine.set_unit_price(divided_by_qty)
                console.log(divided_by_qty)
            }
            else{
                console.log(',awf,,,,awef,,',keysSorted[0].fixed_price)
                orderLine.set_unit_price(keysSorted[0].fixed_price);
                
            }
        }
        else{
            orderLine.set_unit_price(orderLine.product.get_price(orderLine.order.pricelist, pricelist_qty, orderLine.get_price_extra(), orderLine.multi_uom_line));
        }
        this.trigger('close-popup');
    }
}
ChangeUomPopup.template = 'ChangeUomPopup';
ChangeUomPopup.defaultProps = {
    confirmText: 'Confirm',
    cancelText: 'Cancel',
    title: 'Select',
    body: '',
    list: [],
};

Registries.Component.add(ChangeUomPopup);

return ChangeUomPopup;
});