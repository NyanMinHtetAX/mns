odoo.define('stock_adjustment_backdate.validate_btn_controller', function (require) {
"use strict";

var ListController = require('web.ListController');
var framework = require('web.framework');
//var displayNotification = registry.category("actions")

var AdjustmentListController = ListController.extend({

    buttons_template: 'AdjustmentLineListView',

    init: function (parent, model, renderer, params) {
        this.context = renderer.state.getContext();
        return this._super.apply(this, arguments);
    },

    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        this.$buttons.on('click', '.btn-validate-adjustment', this.validateInventoryAdjustment.bind(this));
    },

    validateInventoryAdjustment: async function () {
        if(this.context.active_id){
            framework.blockUI();
            this._rpc({
                model: 'stock.adjustment',
                method: 'btn_validate',
                args: [this.context.active_id],
            }).then(result => {
                framework.unblockUI();
                this.displayNotification({
                    message: "Inventory is successfully validated.",
                    type: 'success',
                    sticky: false,
                });
                this.trigger_up('history_back');
            }).catch(err => {
                framework.unblockUI();
            });
        }
    },
});

return AdjustmentListController;

});
