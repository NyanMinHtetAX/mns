odoo.define('expired_lots.ExpiredLotsDashboardView', function (require) {
"use strict";

var KanbanView = require('web.KanbanView');
var ExpiredLotsDashboardRenderer = require('expired_lots.ExpiredLotsDashboardRenderer');
var viewRegistry = require('web.view_registry');

var ExpiredLotsDashboardView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Renderer: ExpiredLotsDashboardRenderer,
    }),
});

viewRegistry.add('expired_lots', ExpiredLotsDashboardView);

return ExpiredLotsDashboardView;

});
