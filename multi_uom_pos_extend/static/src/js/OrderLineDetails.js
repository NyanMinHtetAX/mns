odoo.define('multi_uom_pos_extend.OrderlineDetails', function(require){

var Registries = require('point_of_sale.Registries');
var OrderlineDetails = require('point_of_sale.OrderlineDetails');

var OrderlineDetailsExtend = Component => class extends OrderlineDetails{
    get unit() {
        var unit = super.unit;
        if(this.line.multi_uom_line){
            return this.env.pos.units_by_id[this.line.multi_uom_line.uom_id[0]];
        }
        return unit;
    }
};

Registries.Component.extend(OrderlineDetails, OrderlineDetailsExtend);

return OrderlineDetailsExtend;

});