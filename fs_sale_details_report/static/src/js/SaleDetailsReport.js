odoo.define('fs_sale_details_report.SaleDetailsReport', function(require){

var core = require('web.core');
var Qweb = core.qweb;
var AbstractAction = require('web.AbstractAction');
var datepicker = require('web.datepicker');
var time = require('web.time');
var dialogs = require('web.view_dialogs');

var SaleDetailsReport = AbstractAction.extend({

    init: function(parent, context) {
        this.dateFormat = time.getLangDateFormat();
        this.options = {};
        this._super(parent, context);
    },

    events: {
        'click .sale-details-cp-btn': 'openM2MSelectionBox',
        'click .select-report-handler': 'clickReportHandler',
        'click .sale-details-download-report': '_downloadReport',
    },

    willStart: async function () {
        var self = this;
        var dataPromise = this._rpc({
            model: 'van.sale.details.report',
            method: 'get_data',
            args: [this.options],
        }).then(result => {
            self.report_data = result;
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

    _updateReport: function(){
        var self = this;
        console.log('OPTIONS', this.options)
        this._rpc({
            model: 'van.sale.details.report',
            method: 'get_data',
            args: [this.options],
        }).then(result => {
            self.report_data = result;
            self.options = result.options;
            self._renderReport();
        });
    },

    _renderReport: function(){
        var self = this;
        this.$el.html(Qweb.render("SaleDetailsReport", {
            data: self.report_data
        }));
        this.renderDatePickers();
    },

    renderDatePickers: function(){
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
                var defaultDate = inputId === 'sale-details-date-from' ? defaultDateFrom : defaultDateTo;
                dt.$el.find('input').attr('name', name);
                dt.setValue(defaultDate);
            });
            self.datePicker = dt;
            dt.on('datetime_changed', this, function () {
                var value = moment(dt.getValue()).format('YYYY-MM-DD');
                inputId === 'sale-details-date-from' ? self.options.date_from = value : self.options.date_to = value;
                self._updateReport();
            });
        });
    },

    openM2MSelectionBox: function(event){
        var self = this;
        var $btn = $(event.target);
        var btnData = $btn.data();
        var res_model = btnData.resModel;
        var optionKey = btnData.optionKey;
        var title = btnData.title;
        var selectedIds = this.options[optionKey] || [];
        var whitelistIds = this.report_data[optionKey];
        new dialogs.SelectCreateDialog(this, {
            res_model: res_model,
            domain: [['id', 'in', whitelistIds]],
            context: {},
            title: title,
            no_create: true,
            on_selected: function (records) {
                var resIDs = _.pluck(records, 'id');
                var newIDs = _.difference(resIDs, selectedIds);
                var updatedIds = selectedIds.concat(newIDs);
                self.options[optionKey] = resIDs;
                self._updateReport();
            }
        }).open();
    },

    clickReportHandler: function(event){
        var $tr = $(event.currentTarget);
        var $table = $($tr.parent().closest('table'));
        var tableData = $table.data();
        var $btn = $(tableData.btn);
        var trData = $tr.data();
        this.options[tableData.field] = trData.value;
        console.log('clickReportHandler', this.options);
        $btn.text(trData.label);
        $(tableData.modal).modal('toggle');
        var callback = this[$btn.data().callback];
        if(callback){
            callback(this, tableData.field);
        }
        this._updateReport();
    },

    resetReportByOptions: function(self, selectedReportBy){
        var allFields = ['team_ids', 'sale_man_ids', 'category_ids'];
        var fieldsToClear = _.difference(allFields, [selectedReportBy]);
        for(var fieldToClear of fieldsToClear){
            self.options[fieldToClear] = [];
        }
    },

    _downloadReport: function(event){
        var $btn = $(event.currentTarget);
        var reportType = $btn.data().reportType;
        var self = this;
        this._rpc({
            model: 'van.sale.details.report',
            method: 'download_report',
            args: [reportType, this.report_data],
        }).then(result => {
            self.do_action(result);
        });
    },

});

core.action_registry.add('SaleDetailsReport', SaleDetailsReport);

return SaleDetailsReport;

});