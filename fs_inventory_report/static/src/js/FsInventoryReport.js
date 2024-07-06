odoo.define('fs_inventory_report.FsInventoryReport', function(require){

var core = require('web.core');
var Qweb = core.qweb;
var AbstractAction = require('web.AbstractAction');
var datepicker = require('web.datepicker');
var time = require('web.time');
var dialogs = require('web.view_dialogs');

var m2xOptionsData = {
    'crm.team': {
        key: 'team_ids',
        title: 'Select Sales Teams',
        domain: [['is_van_team', '=', true]],
    },
};

var FsInventoryReport = AbstractAction.extend({

    init: function(parent, context) {
        this.options = {
            date: moment().format('YYYY-MM-DD HH:mm:ss'),
            team_ids: [],
        };
        this.backendModel = 'fs.inventory.report';
        this.precision = {minimumFractionDigits: 2, maximumFractionDigits: 2};
        this._super(parent, context);
    },

    events: {
        'click .rp-ts-limit-table tr': '_onChangeLimit',
        'click .rp-iv-m2x-btn': 'openM2MSelectionBox',
        'click .btn-download-excel': '_downloadReport',
        'click .btn-download-pdf': '_downloadReport',
        'change .rp-ts-limit-input-container input': '_onChangeLimitManual',
        'keyup .rp-ts-limit-input-container input': '_onEnter',
    },

    willStart: async function () {
        var self = this;
        var dataPromise = this._rpc({
            model: this.backendModel,
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
        var grouped_transactions = _.groupBy(self.data.transactions, 'location_id');
        function addCommasToNumber(number) {
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
        for(var loc_id in grouped_transactions){
            var rec = {};
            var lines = grouped_transactions[loc_id];
            rec.opening_qty = lines.reduce((total, p) => total += p.opening_qty, 0);
            rec.opening_value = lines.reduce((total, p) => total += p.opening_value, 0);
            rec.sale_qty = lines.reduce((total, p) => total += p.sale_qty, 0);
            rec.sale_value = lines.reduce((total, p) => total += p.sale_value, 0);
            rec.sale_return_qty = lines.reduce((total, p) => total += p.sale_return_qty, 0);
            rec.sale_return_value = lines.reduce((total, p) => total += p.sale_return_value, 0);
            rec.transfer_qty = lines.reduce((total, p) => total += p.transfer_qty, 0);
            rec.transfer_value = lines.reduce((total, p) => total += p.transfer_value, 0);
            rec.scrap_qty = lines.reduce((total, p) => total += p.scrap_qty, 0);
            rec.scrap_value = lines.reduce((total, p) => total += p.scrap_value, 0);
            rec.closing_qty = lines.reduce((total, p) => total += p.closing_qty, 0);
            rec.closing_value = lines.reduce((total, p) => total += p.closing_value, 0);
            rec.lines = lines;
            if(rec.opening_qty != null){
                rec.opening_qty = addCommasToNumber(rec.opening_qty.toFixed(2).toLocaleString());
            }
            if(rec.opening_value != null){
                rec.opening_value = addCommasToNumber(rec.opening_value.toFixed(2).toLocaleString());
            }
            if(rec.sale_qty != null){
                rec.sale_qty = addCommasToNumber(rec.sale_qty.toFixed(2).toLocaleString());
            }
            if(rec.sale_value != null){
                rec.sale_value = addCommasToNumber(rec.sale_value.toFixed(2).toLocaleString());
            }
            if(rec.sale_return_qty != null){
                rec.sale_return_qty = addCommasToNumber(rec.sale_return_qty.toFixed(2).toLocaleString());
            }
            if(rec.sale_return_value != null){
                rec.sale_return_value = addCommasToNumber(rec.sale_return_value.toFixed(2).toLocaleString());
            }
            if(rec.transfer_qty != null){
                rec.transfer_qty = addCommasToNumber(rec.transfer_qty.toFixed(2).toLocaleString());
            }
            if(rec.transfer_value != null){
                rec.transfer_value = addCommasToNumber(rec.transfer_value.toFixed(2).toLocaleString());
            }
            if(rec.scrap_qty != null){
                rec.scrap_qty = addCommasToNumber(rec.scrap_qty.toFixed(2).toLocaleString());
            }
            if(rec.scrap_value != null){
                rec.scrap_value = addCommasToNumber(rec.scrap_value.toFixed(2).toLocaleString());
            }
            if(rec.closing_qty != null){
                rec.closing_qty = addCommasToNumber(rec.closing_qty.toFixed(2).toLocaleString());
            }
            if(rec.closing_value != null){
                rec.closing_value = addCommasToNumber(rec.closing_value.toFixed(2).toLocaleString());
            }
            grouped_transactions[loc_id] = rec;
        }
        this.data.grouped_transactions = grouped_transactions;
        this.$el.html(Qweb.render("FsInventoryReport", {
            teams: self.data.teams,
            transactions: grouped_transactions,
            precision: self.precision,
        }));
        this._renderDatePickers();
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
        var defaultDate = moment(this.options.date, 'YYYY-MM-DD');
        $datetimepickers.each(function () {
            var inputId = $(this).find('input').attr('id');
            var name = $(this).find('input').attr('name');
            $(this).datetimepicker(options);
            var dt = new datepicker.DateWidget(options);
            dt.replace($(this)).then(function () {
                dt.$el.find('input').attr('name', name);
                console.log('DEFAULT DATE', defaultDate);
                dt.setValue(defaultDate);
            });
            dt.on('datetime_changed', this, function () {
                var value = moment(dt.getValue()).format('YYYY-MM-DD HH:mm:ss');
                self.options.date = value;
                self._updateReport();
            });
        });
    },

    openM2MSelectionBox: function(event){
        var self = this;
        var $btn = $(event.currentTarget);
        var btnData = $btn.data();
        var res_model = btnData.resModel;
        var selectionData = m2xOptionsData[res_model];
        var optionKey = selectionData.key;
        var title = selectionData.title;
        var selectedIds = this.options[optionKey] || [];
        var domain = selectionData.domain || [];
        new dialogs.SelectCreateDialog(this, {
            res_model: res_model,
            domain: domain,
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
        var rows = $($('.rp-ts-main-table').children('tbody')).children();
        var rowsToShow = rows.slice(0, limit);
        var rowsToHide = rows.slice(limit);
        rowsToShow.show();
        rowsToHide.hide();
    },

    _updateReport: function(){
        var self = this;
        this._rpc({
            model: this.backendModel,
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
            model: 'fs.inventory.report',
            method: 'download_report',
            args: [reportType, {
                teams: this.data.teams,
                options: this.data.options,
                transactions: this.data.grouped_transactions,
            }],
        }).then(result => {
            self.do_action(result);
        });
    },

});

core.action_registry.add('FsInventoryReport', FsInventoryReport);

return FsInventoryReport;

});