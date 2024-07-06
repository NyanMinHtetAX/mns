odoo.define('jr_dashboard.JRReport', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var web_client = require('web.web_client');
    var session = require('web.session');
    var _t = core._t;
    var QWeb = core.qweb;
    var self = this;
    var currency;
    var DashBoard = AbstractAction.extend({
        contentTemplate: 'JRReport',
        events: {
            'change #top_selling_customer': function(e) {
//                e.stopPropagation();
                var $target = $(e.target);
                var value = $target.val();
                if (value=="this_year"){
                    this.onclick_this_year($target.val());
                }else if (value=="this_month"){
                    this.onclick_this_month($target.val());
                }else if (value=="this_week"){
                    this.onclick_this_week($target.val());
                }
                else if (value=="last-month"){
                    this.onclick_last_month($target.val());
                }
            },
            'change #main_db': function(e) {
                e.stopPropagation();
                var $target = $(e.target);
                var value = $target.val();
                if (value=="t-year"){
                    this.onclick-t-year($target.val());
                }else if (value=="t-month"){
                    this.onclick-t-month($target.val());
                }else if (value=="t-week"){
                    this.onclick-t-week($target.val());
                }
            },
        },
        willStart: function(){
            var self = this;
            this.login_employee = {};
            return this._super()
            .then(function() {

                var def0 =  self._rpc({
                    model: 'sale.order',
                    method: 'get_total_order',
                     args: [1],
                }).then(function(result) {
                    self.total_order = result['total_order'];
                    if (result == true){
                        self.is_manager = true;
                    }
                    else{
                        self.is_manager = false;
                    }
                });
                var def1 = self._rpc({
                    model: "sale.order",
                    method: "get_new_order",
                    args: [1],
                })
                .then(function (res) {
                    self.new_order = res['new_order'];
                });
                var def2 = self._rpc({
                    model: "sale.order",
                    method: "get_total_customer",
                    args: [1],
                })
                .then(function (res) {
                    self.total_customer = res['total_customer'];
                });
                var def3 = self._rpc({
                    model: "sale.order",
                    method: "get_total_wishlist",
                    args: [1],
                })
                .then(function (res) {
                    self.total_wishlist = res['total_wishlist'];
                });
                var def4 = self._rpc({
                    model: "sale.order",
                    method: "get_top_selling_customer",
                    args: [1],
                })
                .then(function (res) {
                    self.top_selling_customer = res['top_selling_customer'];
                });
                var def5 = self._rpc({
                    model: "sale.order",
                    method: "get_recent_order",
                    args: [1],
                })
                .then(function (res) {
                    self.recent_order = res['recent_order'];
                });
                return $.when(def0, def1, def2 ,def3 ,def4 ,def5);
            });
        },
        onclick_this_year: function (ev) {
            var self = this;
            console.log('11111111111111111111111111')
            var years = this._rpc({
                        model: 'sale.order',
                        method: 'get_this_year',
                        args: [1],
                        })
           .then(function (res) {
                self.top_selling_customer = res['top_selling_customer'];
                self.time_range = res['time_range'];
                self.total_customer = res['total_customer'];
                self.total_wishlist = res['total_wishlist'];
                self.total_order = res['total_order'];
                self.new_order = res['new_order'];
                self.$el.html(QWeb.render("JRReport", {widget: self}));
            });
            console.log('This Year Data')
//            return this.$el.html(QWeb.render("JRReport", {widget: self}));
        },
        onclick_this_month: function (ev) {
            var self = this;
            var years = this._rpc({
                        model: 'sale.order',
                        method: 'get_this_month',
                        args: [1],
                        })
           .then(function (res) {
                self.top_selling_customer = res['top_selling_customer'];
                self.time_range = res['time_range'];
                self.total_customer = res['total_customer'];
                self.total_wishlist = res['total_wishlist'];
                self.total_order = res['total_order'];
                self.new_order = res['new_order'];
                self.$el.html(QWeb.render("JRReport", {widget: self}));
            });
            console.log(self.top_selling_customer,'Tis Month Data')
        },
        onclick_this_week: function (ev) {
            var self = this;
            var years = this._rpc({
                        model: 'sale.order',
                        method: 'get_this_week',
                        args: [1],
                        })
           .then(function (res) {
                 self.top_selling_customer = res['top_selling_customer'];
                 self.time_range = res['time_range'];
                 self.total_customer = res['total_customer'];
                 self.total_wishlist = res['total_wishlist'];
                 self.total_order = res['total_order'];
                 self.new_order = res['new_order'];
                 self.$el.html(QWeb.render("JRReport", {widget: self}));
            });
            console.log(self.this_week,'This Week Data')
//            return this.$el.html(QWeb.render("JRReport", {widget: self}));
        },
        onclick_last_month: function (ev) {
            var self = this;
            var this_year = 'this_year';
            var years = this._rpc({
                        model: 'sale.order',
                        method: 'get_last_month',
                        args: [1],
                        })
           .then(function (res) {
                self.top_selling_customer = res['top_selling_customer'];
                self.time_range = res['time_range'];
                self.total_customer = res['total_customer'];
                self.total_wishlist = res['total_wishlist'];
                self.total_order = res['total_order'];
                self.new_order = res['new_order'];
                self.$el.html(QWeb.render("JRReport", {widget: self}));
            });
            console.log(self.last_month,'Last Month Dataaaaaaaaaaaaaaaaa')
//            return this.$el.html(QWeb.render("JRReport", {widget: self}));
        },
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.update_cp();
            });
        },
        fetch_data: function() {
            var self = this;

            var def0 =  self._rpc({
                model: 'sal.order',
                method: 'get_total_order',
                args: [1],
            }).then(function(result) {
                self.total_order = result['total_order'];
                if (result == true){
                    self.is_manager = true;
                }
                else{
                    self.is_manager = false;
                }
            });

            var def1 = self._rpc({
                model: "sale.order",
                method: "get_new_order",
                args: [1],
            })
            .then(function (res) {
                self.new_order = res['new_order'];
            });
            var def2 = self._rpc({
                    model: "sale.order",
                    method: "get_total_customer",
                    args: [1],
                })
                .then(function (res) {
                    self.total_customer = res['total_customer'];
                });
            var def3 = self._rpc({
                    model: "sale.order",
                    method: "get_total_wishlist",
                    args: [1],
                })
                .then(function (res) {
                    self.total_wishlist = res['total_wishlist'];
                });
            var def4 = self._rpc({
                    model: "sale.order",
                    method: "get_top_selling_customer",
                    args: [1],
                })
                .then(function (res) {
                    self.top_selling_customer = res['top_selling_customer'];
                });
             var def5 = self._rpc({
                    model: "sale.order",
                    method: "get_recent_order",
                    args: [1],
                })
                .then(function (res) {
                    self.recent_order = res['recent_order'];
                });
            return $.when(def0, def1,def2 ,def3 ,def4 ,def5);
        },

        render_dashboards: function() {
            var self = this;
            if (this.login_employee){
                var templates = []
                if( self.is_manager == true){
                    templates = ['LoginUser', 'Managercrm', 'Admincrm','JRReport'];
                }
                else{
                    templates = ['LoginUser','Managercrm'];
                }
                _.each(templates, function(template) {
                    self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
                });
            }
            else{
                self.$('.o_hr_dashboard').append(QWeb.render('EmployeeWarning', {widget: self}));
            }
        },

        on_reverse_breadcrumb: function() {
            var self = this;
            web_client.do_push_state({});
            this.update_cp();
            this.fetch_data().then(function() {
                self.$('.o_hr_dashboard').reload();
                self.render_dashboards();
            });
        },

         update_cp: function() {
            var self = this;
         },
    });

    core.action_registry.add('JRReport', DashBoard);
    return DashBoard;
});