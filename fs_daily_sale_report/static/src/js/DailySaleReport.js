odoo.define('fs_daily_sale_report.DailySaleReport', function(require){

var core = require('web.core');
var Qweb = core.qweb;
var AbstractAction = require('web.AbstractAction');
var datepicker = require('web.datepicker');
var framework = require('web.framework');

var DailySaleReport = AbstractAction.extend({

    init: function(parent, context) {
        this.dateFormat = 'MM/DD/YYYY';
        this._super(parent, context);
    },

    events: {
        'click .sale-team-item': '_onClickSaleTeamItem',
        'click .route-plan-item': '_onClickRoutePlanItem',
        'click .sale-man-item': '_onClickSaleManItem',
        'click .btn-toggle': '_toggleTable',
        'click .ds-download-btn': '_downloadReport',
    },

    willStart: async function () {
        var self = this;
        var dataPromise = this._rpc({
            model: 'daily.sale.summary.report',
            method: 'get_data',
            args: [],
        }).then(result => self.report_data = result);
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
        this.$el.html(Qweb.render("DailySaleReport", {
            data: self.report_data
        }));
        this.renderDatePicker();
        this.date = moment(this.report_data.date, 'YYYY-MM-DD HH:mm:ss');
        this.team_id = this.report_data.sale_team.id;
        this.user_id = this.report_data.sale_person.id;
        this.route_plan_id = this.report_data.route_plan.id;
        this.data_available = this.report_data.data_available;
    },

    _updateData: function(){
        var self = this;
        var formattedDate = this.date.format("YYYY-MM-DD HH:mm:ss");
        this._rpc({
            model: 'daily.sale.summary.report',
            method: 'get_data',
            args: [formattedDate, self.team_id, self.user_id, self.route_plan_id],
        }).then(result => {
            self.report_data = result;
            $('.o_action').empty();
            self._renderReport();
        });
    },

    renderDatePicker: function(){
        var self = this;
        var $datetimepickers = this.$el.find('.js_account_reports_datetimepicker');
        var options = {
            locale : moment.locale(),
            format : 'L',
            icons: {
                date: "fa fa-calendar",
            },
        };
        var defaultDate = this.date ? moment(this.date, this.dateFormat) : moment();
        $datetimepickers.each(function () {
            var name = $(this).find('input').attr('name');
            $(this).datetimepicker(options);
            var dt = new datepicker.DateWidget(options);
            dt.replace($(this)).then(function () {
                dt.$el.find('input').attr('name', name);
                dt.setValue(defaultDate);
                $('<i class="fa fa-calendar ds-calendar-icon"/>').insertBefore(dt.$el.find('input'))
            });
            self.datePicker = dt;
            dt.on('datetime_changed', this, function () {
                self.date = dt.getValue();
                self._updateData();
            });
        });
    },

    _onClickSaleTeamItem: function(event){
        if(event){
            var $div = $(event.target);
            var team = $div.data();
            this.team_id = team.id;
            $('#sale-team-btn').text(team.name);
            $('#sale-team-modal').modal('hide');
            this._updateData();
        }
    },

    _onClickRoutePlanItem: function(event){
        if(event){
            var $div = $(event.target);
            var route_plan = $div.data();
            this.route_plan_id = route_plan.id;
            $('#route-plan-btn').text(route_plan.name);
            $('#route-plan-modal').modal('hide');
            this._updateData();
        }
    },

    _onClickSaleManItem: function(event){
        if(event){
            var $div = $(event.target);
            var sale_man = $div.data();
            this.user_id = sale_man.id;
            $('#sale-man-btn').text(sale_man.name);
            $('#sale-man-modal').modal('hide');
            this._updateData();
        }
    },

    _toggleTable: function(event){
        if(event){
            $btn = $(event.target);
            var $table = $($btn.data().toggle);
            var $toHide = $($btn.data().toHide);
            var $toShow = $($btn.data().toShow);
            $table.is(':visible') ? $table.hide() : $table.show();
            $toHide.addClass('d-none');
            $toShow.removeClass('d-none');
        }
    },

    _downloadReport: function(event){
        var self = this;
        var $btn = $(event.currentTarget);
        var reportType = $btn.data().reportType;
        if(!this.data_available){
            alert('You can\'t download since there is no data.');
        }
        else{
            var total_qty = total_amt = 0;
            this._rpc({
                model: 'daily.sale.summary.report',
                method: 'download_report',
                args: [reportType, self.report_data]
            })
            .then(action => self.do_action(action));
        }
    }

});

core.action_registry.add('DailySaleReport', DailySaleReport);

return DailySaleReport;

});