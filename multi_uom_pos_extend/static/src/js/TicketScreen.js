odoo.define('multi_uom_pos_extend.TicketScreen', function(require){

var Registries = require('point_of_sale.Registries');
var TicketScreen = require('point_of_sale.TicketScreen');
var { useState } = owl.hooks;
var models = require('point_of_sale.models');
var IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');
var NumberBuffer = require('point_of_sale.NumberBuffer');
var { useListener, useAutofocus } = require('web.custom_hooks');
var { posbus } = require('point_of_sale.utils');
var { parse } = require('web.field_utils');

var TicketScreenExtend = Component => class extends Component{
    // Complete Override of _onDoRefund for multi-uom purposes
    async _onDoRefund() {
        const order = this.getSelectedSyncedOrder();
        if (!order) {
            this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
            return this.render();
        }

        if (this._doesOrderHaveSoleItem(order)) {
            this._prepareAutoRefundOnOrder(order);
        }

        const customer = order.get_client();

        // Select the lines from toRefundLines (can come from different orders)
        // such that:
        //   - the quantity to refund is not zero
        //   - if there is customer in the selected paid order, select the items
        //     with the same orderPartnerId
        //   - it is not yet linked to an active order (no destinationOrderUid)
        const allToRefundDetails = Object.values(this.env.pos.toRefundLines).filter(
            ({ qty, orderline, destinationOrderUid }) =>
                !this.env.pos.isProductQtyZero(qty) &&
                (customer ? orderline.orderPartnerId == customer.id : true) &&
                !destinationOrderUid
        );
        if (allToRefundDetails.length == 0) {
            this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
            return this.render();
        }

        // The order that will contain the refund orderlines.
        // Use the destinationOrder from props if the order to refund has the same
        // customer as the destinationOrder.
        const destinationOrder =
            this.props.destinationOrder && customer === this.props.destinationOrder.get_client()
                ? this.props.destinationOrder
                : this.env.pos.add_new_order({ silent: true });

        // Add orderline for each toRefundDetail to the destinationOrder.
        for (const refundDetail of allToRefundDetails) {
            const { qty, orderline } = refundDetail;
            await destinationOrder.add_product(this.env.pos.db.get_product_by_id(orderline.productId), {
                quantity: -qty,
                price: orderline.price,
                lst_price: orderline.price,
                extras: { price_manually_set: true },
                merge: false,
                refunded_orderline_id: orderline.id,
                tax_ids: orderline.tax_ids,
                discount: orderline.discount,
                multi_uom_line_id: orderline.multi_uom_line_id, // Added multi_uom_line_id
            });
            refundDetail.destinationOrderUid = destinationOrder.uid;
        }

        // Set the customer to the destinationOrder.
        if (customer && !destinationOrder.get_client()) {
            destinationOrder.set_client(customer);
        }

        this._onCloseScreen();
    }

    _getToRefundDetail(orderline) {
        var toRefundDetail = super._getToRefundDetail(orderline);
        toRefundDetail.orderline.multi_uom_line = orderline.multi_uom_line;
        toRefundDetail.orderline.multi_uom_line_id = orderline.multi_uom_line_id;
        return toRefundDetail;
    }
};

Registries.Component.extend(TicketScreen, TicketScreenExtend);

return TicketScreenExtend;

});