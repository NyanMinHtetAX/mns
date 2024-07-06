odoo.define('expired_lots.ExpiredLotsDashboardRenderer', function (require) {
"use strict";

var KanbanRenderer = require('web.KanbanRenderer');
var core = require('web.core');
var Qweb = core.qweb;
var Widget = require('web.Widget');
var rpc = require('web.rpc');
var durationData = {
    'days': 'Days',
    'months': 'Months',
    'years': 'Years',
};

var ExpiredLotsWidget = Widget.extend({

    template: 'ExpiredLotsDashboard',

    events: {
        'click .expired-lots-dashboard-card': '_onClickExpireLotsCard',
    },

    init: function  (parent, options) {
        this.a_ids = [];
        this.b_ids = [];
        this.c_ids = [];
        this.d_ids = [];
        this._super.apply(this, arguments);
    },

    renderElement: function () {
        var self = this;
        this._super();
        rpc.query({
            model: 'stock.production.lot',
            method: 'get_expired_products',
            args: [],
        }).then(function (data){
            self.update_content(data);
        });
    },

    update_content: function (data) {
        var blocks = ['a', 'b', 'c'];
        for(var block of blocks){
            var blockData = data[`block_${block}`];
            var $count = $(`.expired-lots-${block}-count`);
            var $duration = $(`.expired-lots-${block}-duration`);
            var $unit = $(`.expired-lots-${block}-unit`);
            $count.text(blockData.count);
            $count.closest('div').css('background', blockData.color);
            $duration.text(blockData.duration);
            $unit.text(durationData[blockData.unit]);
            this[`${block}_ids`] = blockData.ids;
        }
        var blockDData = data['block_d'];
        var $DCount = $('.expired-lots-d-count');
        $DCount.text(blockDData.count);
        $DCount.closest('div').css('background', blockDData.color);
        this.d_ids = blockDData.ids;
    },

    _onClickExpireLotsCard: function (event) {
        var $block = $(event.currentTarget);
        var blockName = $block.data().blockName;
        this.do_action({
            'type': 'ir.actions.act_window',
            'name': 'Lots',
            'res_model': 'stock.production.lot',
            'views': [[false, 'list'],[false, 'form']],
            'view_mode': "list",
            'target': 'current',
            'domain': [['id', 'in', this[`${blockName}_ids`]]]
        });
    },

});


var ExpiredLotsDashboardRenderer = KanbanRenderer.extend({
    _renderView: function () {
        var self = this;
        return this._super.apply(this, arguments).then(res => {
            $('.expired-lots-dashboard-container').remove();
            new ExpiredLotsWidget(self).insertBefore(self.$el);
        });
    },
});

return ExpiredLotsDashboardRenderer;

});
