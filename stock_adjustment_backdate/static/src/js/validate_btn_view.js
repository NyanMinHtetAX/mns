odoo.define('stock_adjustment_backdate.validate_btn_view', function (require) {
"use strict";

var ListView = require('web.ListView');
var validateBtnController = require('stock_adjustment_backdate.validate_btn_controller');
var viewRegistry = require('web.view_registry');

var AdjustmentListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: validateBtnController,
    }),
});

viewRegistry.add('adjustment_list_view', AdjustmentListView);

return AdjustmentListView;

});
