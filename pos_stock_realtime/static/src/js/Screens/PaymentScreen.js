odoo.define('pos_stock_realtime.PaymentScreen', function(require){
    'use strict';

    var PaymentScreen = require('point_of_sale.PaymentScreen');
    var Registries = require('point_of_sale.Registries');
    var { Gui } = require('point_of_sale.Gui');
    var { useErrorHandlers, useAsyncLockedMethod } = require('point_of_sale.custom_hooks');


    var PaymentScreenExtend = PaymentScreen => class extends PaymentScreen{
        constructor() {
            super(...arguments);
            useErrorHandlers();
        }

        async validateOrder(isForceValidate) {

            var error_message = await this.env.pos.rpc({
                model: 'pos.order',
                method: 'check_on_hand_qty',
                args: [this.currentOrder.export_as_JSON(), this.env.pos.config_id],
            });
            if(error_message){
                return this.showPopup('ErrorPopup', {
                    title: this.env._t('Insufficient Stock!'),
                    body: this.env._t(error_message),
                });
            }
            var res = await super.validateOrder(this, arguments);
            var lines = this.currentOrder.get_orderlines();
            var index = 0;
            for(var index=0; index < lines.length; index++){
                var line = lines[index];
                  var error_message1 = await this.env.pos.rpc({
                model: 'pos.order',
                method: 'check_on_hand_qty1',
                args: [line.product.id, this.env.pos.config_id],
                });
                console.log(error_message1,'sssssssssssssssssssssssssss')
                line.product.onhand_qty=error_message1;
                line.product.is_check=true;
            }
            return res
        }
    };

    Registries.Component.extend(PaymentScreen, PaymentScreenExtend);

    return PaymentScreenExtend;

});