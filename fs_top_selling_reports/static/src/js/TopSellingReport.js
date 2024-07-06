odoo.define('fs_top_selling_reports.TopSellingReport', function(require){

var core = require('web.core');
var Qweb = core.qweb;
var AbstractAction = require('web.AbstractAction');
var datepicker = require('web.datepicker');
var time = require('web.time');
var dialogs = require('web.view_dialogs');

var TopSellingReport = AbstractAction.extend({

    init: function(parent, context) {
        this.precision = {minimumFractionDigits: 2, maximumFractionDigits: 2};
        this._super(parent, context);
    },

    events: {
        'click .rp-ts-limit-table tr': '_onChangeLimit',
        'click .rp-ts-download-report': '_downloadReport',
        'change .rp-ts-limit-input-container input': '_onChangeLimitManual',
        'keyup .rp-ts-limit-input-container input': '_onEnter',
    },

    willStart: async function () {
        var self = this;
        var dataPromise = this._rpc({
            model: 'top.selling.report',
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
        this.$el.html(Qweb.render("TopSellingReport", { data: self.data, precision: self.precision }));
        this._renderDatePickers();
        var limit = self.data.options.limit || 5;
        var rows = $($('.rp-ts-main-table').children('tbody')).children();
        var rowsToShow = rows.slice(0, limit);
        var rowsToHide = rows.slice(limit);
        rowsToShow.show();
        rowsToHide.hide();
    },

    _renderDatePickers: function(){
        var self = this;
        var $datetimepickers = this.$el.find('.js_account_reports_datetimepicker');
        var options = {
            locale : moment.locale(),
            format : 'L',
            icons: {
                date: "fa fa-calendar",
            },
        };
        var defaultDateFrom = this.options.date_from ? moment(this.options.date_from, 'YYYY-MM-DD') : moment();
        var defaultDateTo = this.options.date_from ? moment(this.options.date_to, 'YYYY-MM-DD') : moment();
        $datetimepickers.each(function () {
            var inputId = $(this).find('input').attr('id');
            var name = $(this).find('input').attr('name');
            $(this).datetimepicker(options);
            var dt = new datepicker.DateWidget(options);
            dt.replace($(this)).then(function () {
                var defaultDate = inputId === 'rp-ts-date-from' ? defaultDateFrom : defaultDateTo;
                dt.$el.find('input').attr('name', name);
                dt.setValue(defaultDate);
            });
            dt.on('datetime_changed', this, function () {
                var value = moment(dt.getValue()).format('YYYY-MM-DD');
                inputId === 'rp-ts-date-from' ? self.options.date_from = value : self.options.date_to = value;
                self._updateReport();
            });
        });
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
            model: 'top.selling.report',
            method: 'get_data',
            args: [this.options],
        }).then(result => {
            self.data = result;
            self.options = result.options;
            self._renderReport();
        });
    },

    _downloadReport: function(event){
        var $btn = $(event.currentTarget);
        var reportType = $btn.data().reportType;
        var self = this;
        this._rpc({
            model: 'top.selling.report',
            method: 'download_report',
            args: [reportType, this.data],
        }).then(result => {
            self.do_action(result);
        });
    },

});

core.action_registry.add('TopSellingReport', TopSellingReport);

var TopSellingReportBySaleTeam = TopSellingReport.extend({
    init: function(parent, context) {
        this.options = {
            date_from: moment().startOf('month').format('YYYY-MM-DD'),
            date_to: moment().endOf('month').format('YYYY-MM-DD'),
            title: 'Top Selling Report By Sales Team',
            report_by: 'sale_team',
            root_select: 'ID, NAME, INVOICED_TARGET',
            root_group_by: 'ID, NAME, INVOICED_TARGET',
            select: 'ST.ID, ST.NAME, COALESCE(ST.INVOICED_TARGET, 0) AS INVOICED_TARGET',
            group_by: 'ST.ID, ST.NAME, ST.INVOICED_TARGET',
            order_by: 'total',
            limit: 5,
        };
        this._super(parent, context);
    },
});

core.action_registry.add('TopSellingReportBySaleTeam', TopSellingReportBySaleTeam);

var TopSellingReportByCustomer = TopSellingReport.extend({
    init: function(parent, context) {
        this.options = {
            date_from: moment().startOf('month').format('YYYY-MM-DD'),
            date_to: moment().endOf('month').format('YYYY-MM-DD'),
            title: 'Top Selling Report By Customer',
            report_by: 'customer',
            root_select: 'ID, NAME, REF',
            root_group_by: 'ID, NAME, REF',
            select: "CUSTOMER.ID, CUSTOMER.NAME, COALESCE(CUSTOMER.REF, '-') AS REF",
            group_by: 'CUSTOMER.ID, CUSTOMER.NAME, CUSTOMER.REF',
            order_by: 'total',
            limit: 5,
        };
        this._super(parent, context);
    },
});

core.action_registry.add('TopSellingReportByCustomer', TopSellingReportByCustomer);

var TopSellingReportBySalesman = TopSellingReport.extend({
    init: function(parent, context) {
        this.options = {
            date_from: moment().startOf('month').format('YYYY-MM-DD'),
            date_to: moment().endOf('month').format('YYYY-MM-DD'),
            title: 'Top Selling Report By Salesman',
            report_by: 'salesman',
            root_select: 'ID, NAME, TEAM',
            root_group_by: 'ID, NAME, TEAM',
            select: "US.ID, RP.NAME, ST.NAME AS TEAM",
            group_by: 'US.ID, RP.NAME, ST.ID, ST.NAME',
            order_by: 'total',
            limit: 5,
        };
        this._super(parent, context);
    },
});

core.action_registry.add('TopSellingReportBySalesman', TopSellingReportBySalesman);

var TopSellingReportByProduct = TopSellingReport.extend({
    init: function(parent, context) {
        this.options = {
            date_from: moment().startOf('month').format('YYYY-MM-DD'),
            date_to: moment().endOf('month').format('YYYY-MM-DD'),
            title: 'Top Selling Report By Product',
            report_by: 'product',
            root_select: 'ID, NAME, CODE, UOM',
            root_group_by: 'ID, NAME, CODE, UOM',
            select: 'PP.ID, PP.DEFAULT_CODE AS CODE, PT.NAME, UOM.NAME AS UOM',
            group_by: 'PP.ID, PP.DEFAULT_CODE, PT.NAME, UOM.NAME',
            order_by: 'qty',
            limit: 5,
        };
        this._super(parent, context);
    },
});

core.action_registry.add('TopSellingReportByProduct', TopSellingReportByProduct);

return {
    TopSellingReport,
    TopSellingReportBySaleTeam,
    TopSellingReportByCustomer,
    TopSellingReportBySalesman,
    TopSellingReportByProduct,
};

});