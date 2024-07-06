odoo.define('fs_route_plan.RoutePlan', function(require){

var core = require('web.core');
var Qweb = core.qweb;
var AbstractAction = require('web.AbstractAction');
var datepicker = require('web.datepicker');
var time = require('web.time');
var dialogs = require('web.view_dialogs');

var RoutePlan = AbstractAction.extend({

    init: function(parent, context) {
        this.precision = {minimumFractionDigits: 2, maximumFractionDigits: 2};
        this._super(parent, context);
    },

    events: {
        'click .rp-ts-limit-table tr': '_onChangeLimit',
        'click #my-back-button': '_onReady',
        'change .rp-ts-limit-input-container input': '_onChangeLimitManual',
        'keyup .rp-ts-limit-input-container input': '_onEnter',
    },

    willStart: async function () {
        var self = this;
        var dataPromise = this._rpc({
            model: 'route.plan',
            method: 'get_data',
            args: [this.options],
        }).then(result => {
            self.data = result;
            self.options = result.options;
        });

        var parentPromise = this._super(...arguments);
        return Promise.all([dataPromise, parentPromise]);
    },

    start: function(){
        var self = this;
        return this._super().then(function() {
            self._renderReport();
        });
    },

    _renderReport: function(){
        var self = this;
        console.log(',,,,,,,,,',self.data)
        this.$el.html(Qweb.render("RoutePlan", { data: self.data, precision: self.precision }));
        var limit = self.data.options.limit || 5;
        var rows = $($('.rp-ts-main-table').children('tbody')).children();
        var rowsToShow = rows.slice(0, limit);
        var rowsToHide = rows.slice(limit);
        rowsToShow.show();
        rowsToHide.hide();
    },

    
    _onEnter: function(event){
        if(event.keyCode === 13){
            this._onChangeLimitManual(event);
        }
    },

    _onChangeLimit: function(event){
        var $tr = $(event.currentTarget);
        this.options.limit = $tr.data().value;
        $('#rp-ts-limit-input').val($tr.data().value);
        $('#rp-ts-limit-modal').modal('toggle');
        $('.rp-ts-limit-input-container input').change();
    },

    _onChangeLimitManual: function(event){
        var limit = parseInt($(event.currentTarget).val());
        this.options.limit = limit;
        var rows = $($('.rp-ts-main-table').children('tbody')).children();
        var rowsToShow = rows.slice(0, limit);
        var rowsToHide = rows.slice(limit);
        rowsToShow.show();
        rowsToHide.hide();
    },

    _updateReport: function(){
        var self = this;
        this._rpc({
            model: 'route.plan',
            method: 'get_data',
            args: [this.options],
        }).then(result => {
            self.data = result;
            self.options = result.options;
            self._renderReport();
        });
    },
    _onReady: function (event) {
        console.log('...,,,,,....,,.,.mmm')
        if(event){
        window.history.back();
        return false;
}
}


});

core.action_registry.add('RoutePlan', RoutePlan);

var RouteWebView = RoutePlan.extend({
    init: function(parent, context) {
        this.options = {
            date_from: moment().startOf('month').format('YYYY-MM-DD'),
            date_to: moment().endOf('month').format('YYYY-MM-DD'),
            title: 'Route Plan Customers',
            report_by: 'sale_team',
            root_select: 'ID, NAME, INVOICED_TARGET',
            root_group_by: 'ID, NAME, INVOICED_TARGET',
            select: 'ST.ID, ST.NAME, COALESCE(ST.INVOICED_TARGET, 0) AS INVOICED_TARGET',
            group_by: 'ST.ID, ST.NAME, ST.INVOICED_TARGET',
            order_by: 'total',
            limit: 5,
            context : context,
        };
        console.log('connnnnnnnnnn',)
        this._super(parent, context);
    },
});

core.action_registry.add('RouteWebView', RouteWebView);



return {
    RoutePlan,
    RouteWebView,
};

});