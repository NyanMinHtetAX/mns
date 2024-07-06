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
            try {
                if (navigator.onLine) {
                    // Check stock quantity before validation
                    var error_message = await this.env.pos.rpc({
                        model: 'pos.order',
                        method: 'check_on_hand_qty',
                        args: [this.currentOrder.export_as_JSON(), this.env.pos.config_id],
                    });
                    if (error_message) {
                        return this.showPopup('ErrorPopup', {
                            title: this.env._t('Insufficient Stock!'),
                            body: this.env._t(error_message),
                        });
                    }

                    var res = await super.validateOrder(isForceValidate);
                    var lines = this.currentOrder.get_orderlines();

                    // Check on-hand quantity for each order line
                    for (let line of lines) {
                        var error_message1 = await this.env.pos.rpc({
                            model: 'pos.order',
                            method: 'check_on_hand_qty1',
                            args: [line.product.id, this.env.pos.config_id],
                        });
                        console.log(error_message1, 'sssssssssssssssssssssssssss');
                        line.product.onhand_qty = error_message1;
                        line.product.is_check = true;
                    }

                    return res;
                } else {
                    // Skip stock checking when offline
                    return await super.validateOrder(isForceValidate);
                }
            } catch (error) {
                if (this.isConnectionError(error)) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to save changes.'),
                    });
                    return await super.validateOrder(isForceValidate);
                } else {
                    throw error;
                }
            }
        }

        isConnectionError(error) {
            // Add logic to determine if the error is related to connection issues
            return typeof error.message === 'string' && error.message.includes('Check the internet connection');
        }

        async saveChanges(event) {
            var team_id = this.env.pos.config.crm_team_id ? this.env.pos.config.crm_team_id[0] : false;
            try {
                let partnerId = await this.rpc({
                    model: 'res.partner',
                    method: 'create_from_ui',
                    args: [event.detail.processedChanges],
                    kwargs: { team_id: team_id },
                });
                await this.env.pos.load_new_partners();
                this.state.selectedClient = this.env.pos.db.get_partner_by_id(partnerId);
                this.state.detailIsShown = false;
                this.render();
            } catch (error) {
                if (this.isConnectionError(error)) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to save changes.'),
                    });
                } else {
                    throw error;
                }
            }
        }
    };

    Registries.Component.extend(PaymentScreen, PaymentScreenExtend);

    return PaymentScreenExtend;
});
