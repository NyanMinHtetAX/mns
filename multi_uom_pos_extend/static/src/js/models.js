odoo.define('multi_uom_pos_extend.models', function (require) {
'use strict';

    const { useState } = owl;
    var { Gui } = require('point_of_sale.Gui');
    const models = require('point_of_sale.models');
    var utils = require('web.utils');
    const { identifyError } = require('point_of_sale.utils');


    models.load_fields('product.product', ['detailed_type','multi_uom_ok']);
    models.load_fields('product.pricelist', ['pricelist_item_uom_ids']);
    models.load_models([
        {
            model: 'ir.config_parameter',
            fields: ['key', 'value'],
            domain: [['key', '=', 'product.product_pricelist_setting']],
            loaded: function (self, param) {
                self.pricelist_mode = param.length > 0 ? param[0].value : false;
            },
        },
        {
            model: 'product.template',
            fields: ['id', 'product_variant_ids','list_price'],
            domain: [],
            loaded: function (self, templates) {
                self.product_templates = templates;
            },
        },
        {
            model: 'product.pricelist.item',
            fields: ['date_start','date_end','compute_price','product_id','product_list_price', 'multi_uom_line_id', 'fixed_price', 'total_price', 'pricelist_id','min_quantity','uom_id'],
            domain: function (self) {
                var pricelist_ids = self.pricelists.map(pricelist => pricelist.id);
                return [['pricelist_id', '=', pricelist_ids]];
            },
            loaded: function (self, items) {
                var uom_pricelist_items_by_id = {};
                var uom_pricelist_items_by_pricelist_id = {};
                var uom_pricelist_by_product = {};
                var uom_price_lists = [];
                var uom_price_lists_formula = [];
                
                for (var item of items) {
                    var today = moment(new Date());
                var start_date = item.date_start ? moment(item.date_start, 'YYYY-MM-DD') : false;
                var end_date = item.date_end ? moment(item.date_end, 'YYYY-MM-DD') : false;
                if(
                    (start_date && end_date && today >= start_date && today <= end_date) ||
                    (start_date && !end_date && today >= start_date) ||
                    (!start_date && end_date && today <= end_date) ||
                    (!start_date && !end_date)
                ){
                    
                    var pricelist_id = item.pricelist_id[0];
                    uom_pricelist_items_by_id[item.id] = item;
                    var all_items = uom_pricelist_items_by_pricelist_id[pricelist_id] || [];
                    all_items.concat(item);
                    uom_pricelist_items_by_pricelist_id[pricelist_id] = all_items;
                    var key = `${item.product_id[0]}-${item.multi_uom_line_id[0]}-${pricelist_id}`;
                    uom_pricelist_by_product[key] = item.price;
                    if (item.compute_price == "fixed"){
                        item.fixed_price = item.fixed_price
                        uom_price_lists.push({
                             product_id:item.product_id[0],
                             uom_id:item.uom_id[0],
                             price:item.fixed_price,
                             qty:item.min_quantity
                        })
                    }
                    else if (item.compute_price == "formula"){
                        item.fixed_price = item.total_price
                        uom_price_lists.push({
                             product_id:item.product_id[0],
                             uom_id:item.uom_id[0],
                             price:item.total_price,
                             qty:item.min_quantity
                        })
                    }
                }
                else
                {   console.log('thosethis',item.product_list_price)
                    uom_price_lists.push({
                             product_id:item.product_id[0],
                             uom_id:item.uom_id[0],
                             price:item.product_list_price,
                             qty:item.min_quantity
                        })
                
            }
                self.uom_pricelist_items = items;
                self.uom_pricelist_items_by_id = uom_pricelist_items_by_id;
                self.uom_pricelist_items_by_pricelist_id = uom_pricelist_items_by_pricelist_id;
                self.uom_pricelist_by_product = uom_pricelist_by_product;
                self.uom_price_lists = uom_price_lists;

            }
        },
        },
        {
            model: 'multi.uom.line',
            fields: [],
            domain: [['product_tmpl_id', '!=', false]],
            loaded: function (self, multi_uom_lines) {
                self.multi_uom_lines = multi_uom_lines;
                self.multi_uom_line_by_id = {};
                self.multi_uom_line_by_product_tmpl_id = {};
                self.multi_uom_line_by_product_id = {};
                for (var line of multi_uom_lines) {
                    self.multi_uom_line_by_id[line.id] = line;
                    var template = self.product_templates.filter(t => t.id === line.product_tmpl_id[0]);
                    if (template.length !== 1) {
                        continue
                    }
                    [template] = template;
                    var tmpl_records = self.multi_uom_line_by_product_tmpl_id[template.id] || [];
                    tmpl_records.push(line);
                    self.multi_uom_line_by_product_tmpl_id[template.id] = tmpl_records;
                    var variants = template.product_variant_ids;
                    for (var variant of variants) {
                        var variant_records = self.multi_uom_line_by_product_id[variant] || [];
                        variant_records.push(line);
                        self.multi_uom_line_by_product_id[variant] = variant_records;
                    }
                }
            },
        },
    ]);
    var superOrder = models.Order.prototype;
    models.Order = models.Order.extend({
        set_pricelist: function (pricelist) {
            var self = this;
            superOrder.set_pricelist.apply(this, arguments);
            var lines_to_recompute = _.filter(this.get_orderlines(), function (line) {
                return !line.price_manually_set;
            });
            _.each(lines_to_recompute, function (line) {
                var pricelist_qty = line.get_quantity();
                if (line.multi_uom_line) {
                    pricelist_qty = pricelist_qty * line.multi_uom_line.ratio;
                }
                line.set_unit_price(line.product.get_price(self.pricelist, pricelist_qty, line.get_price_extra()), line.multi_uom_line);
                self.fix_tax_included_price(line);
            });
            this.trigger('change');
        },
        set_orderline_options: function (orderline, options) {
            superOrder.set_orderline_options.apply(this, arguments);
            if (options.multi_uom_line_id) {
                orderline.multi_uom_line_id = options.multi_uom_line_id;
                orderline.multi_uom_line = this.pos.multi_uom_line_by_id[options.multi_uom_line_id];
                var pricelist_qty = orderline.multi_uom_line.ratio * orderline.get_quantity();
                if (options.price_extra !== undefined) {
                    orderline.price_extra = options.price_extra;
                    orderline.set_unit_price(orderline.product.get_price(this.pricelist, pricelist_qty, options.price_extra, orderline.multi_uom_line));
                    this.fix_tax_included_price(orderline);
                }
            }
        },
    });

    var superOrderLine = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            superOrderLine.initialize.apply(this, arguments);
            if (options.multi_uom_line_id) {
                this.multi_uom_line_id = options.multi_uom_line_id;
                this.multi_uom_line = this.pos.multi_uom_line_by_id[options.multi_uom_line_id];
            }
        },
        init_from_JSON: function (json) {
            superOrderLine.init_from_JSON.apply(this, arguments);
            if (json.multi_uom_line_id) {
                this.multi_uom_line_id = json.multi_uom_line_id;
                this.multi_uom_line = this.pos.multi_uom_line_by_id[json.multi_uom_line_id];
                this.price = json.price_unit * this.multi_uom_line.ratio;
                this.set_discount(json.discount * this.multi_uom_line.ratio);
                this.set_quantity(json.qty / this.multi_uom_line.ratio, 'do not recompute unit price');
            }
        },
        export_as_JSON: function () {
            var values = superOrderLine.export_as_JSON.apply(this, arguments);
            Object.assign(values, {
                multi_uom_line: this.multi_uom_line,
                multi_uom_line_id: this.multi_uom_line_id,
            });
            return values;
        },
        get_unit: function () {
            var unit = superOrderLine.get_unit.apply(this, arguments);
            if (this.multi_uom_line) {
                return this.pos.units_by_id[this.multi_uom_line.uom_id[0]];
            }
            return unit;
        },

        set_quantity: function (qty, keep_price) {

            var res = superOrderLine.set_quantity.apply(this, arguments);
            if (!keep_price && !this.price_manually_set && !(
                this.pos.config.product_configurator && _.some(this.product.attribute_line_ids, (id) => id in this.pos.attributes_by_ptal_id))) {
                var pricelist_qty = this.get_quantity();
                var price_list_data  = this.pos.uom_pricelist_items;
                var selectedOrderline = this.order.selected_orderline;
                var product = false;
                if(selectedOrderline){
                    product = selectedOrderline.product;
                }

                if (this.multi_uom_line) {
                    var check_price_list_data = price_list_data.filter(zaw => zaw.uom_id[0] === this.multi_uom_line.uom_id[0] && zaw.product_id[0] === product.id);
                    var keysSorted = check_price_list_data.sort((a, b) => parseFloat(a.min_quantity) - parseFloat(b.min_quantity));
                    var opposite_price_list_data = check_price_list_data.filter(l => l.min_quantity <= pricelist_qty);
                    var last = Object.keys(opposite_price_list_data).pop();
                    pricelist_qty = this.get_quantity() * this.multi_uom_line.ratio;
                    if(pricelist_qty >1)
                    {
                     this.set_unit_price(opposite_price_list_data[last].fixed_price);
                    }
                    else{
                        this.set_unit_price(this.product.get_price(this.order.pricelist, pricelist_qty, this.get_price_extra(), this.multi_uom_line));
                    }
                }
                else{
                    var check_price_list_data ;
                    if(product!= false){
                       check_price_list_data = price_list_data.filter(zaw => zaw.uom_id[0] === this.product.uom_id[0] && zaw.product_id[0] === product.id);
                    }
                    else{
                       check_price_list_data = false;
                    }
                    if(check_price_list_data!=false){
                          var keysSorted = check_price_list_data.sort((a, b) => parseFloat(a.min_quantity) - parseFloat(b.min_quantity));
                          var opposite_price_list_data = check_price_list_data.filter(l => l.min_quantity <= pricelist_qty);
                          var last = Object.keys(opposite_price_list_data).pop();
                    }
                    if(pricelist_qty >1)
                    {
                       if(check_price_list_data !=false && opposite_price_list_data.length>=1)
                           {
                             this.set_unit_price(opposite_price_list_data[last].fixed_price);
                           }
                        }
                    else{

                        this.set_unit_price(this.product.get_price(this.order.pricelist, pricelist_qty, this.get_price_extra(), this.multi_uom_line));
                    }

                }

                this.order.fix_tax_included_price(this);
            }
            this.trigger('change', this);
            return res;
        },
        can_be_merged_with: function (orderline) {
            var flag = superOrderLine.can_be_merged_with.apply(this, arguments);
            if (flag && orderline.multi_uom_line_id != this.multi_uom_line_id) {
                flag = false;
            }
            return flag;
        },
        set_multi_uom_line: function (multiUomLineId) {
            this.multi_uom_line_id = multiUomLineId;
            this.multi_uom_line = this.pos.multi_uom_line_by_id[multiUomLineId];
        },
    });

    var superProduct = models.Product.prototype;
    models.Product = models.Product.extend({
        get_price: function(pricelist, quantity, price_extra, multi_uom_line=false){
            if(this.pos.pricelist_mode == 'advanced'){
                if(!multi_uom_line && this.detailed_type !='service'){
                    var multi_uom_lines = this.pos.multi_uom_line_by_product_id[this.id] || [];
                    var multi_uom_line = multi_uom_lines.filter(l => l.uom_id[0] === this.uom_id[0]);
                    multi_uom_line.length === 0 ?
                       Gui.showPopup('ErrorPopup', {
                           title: 'UoM Missing',
                          body: `Base UoM is missing for product - ${this.name}.`,
                       })
                        :
                        multi_uom_line = multi_uom_line[0];
                }
                var key = `${this.id}-${multi_uom_line.id}-${pricelist.id}`;
                var price = this.pos.uom_pricelist_by_product[key] || this.lst_price;
                
                var check_order_line =this.pos.get_order().get_orderlines();

                if(check_order_line){
                    
                    var pricelist_data = this.pos.uom_price_lists;
                    var check_pricelist_data = pricelist_data.filter(lwin => lwin.product_id === this.id && lwin.uom_id === multi_uom_line.uom_id[0]);
                    var sort_check_pricelist = check_pricelist_data.sort((a, b) => a.qty> b.qty);
                    
                    if(check_pricelist_data){
                        var qty = quantity;
                        var get_pricelist_data = check_pricelist_data.filter(mar =>mar.qty >= qty);
                        var sor_pricelist_data = get_pricelist_data.sort((a, b) => a.qty >= b.qty)
                        var opposite_pricelist_data = check_pricelist_data.filter(aung => aung.qty <= qty);

                        if(sor_pricelist_data.length>=1){

                        if(qty >= sor_pricelist_data[0].qty)

                            {
                                
                                if (sor_pricelist_data){
                                    price = sor_pricelist_data[0].price;
                                }

                            }
                        else{
                             if(qty>=1){

                                  if(opposite_pricelist_data.length>1){
                                     var last = Object.keys(opposite_pricelist_data).pop();
                                    
                                    price = opposite_pricelist_data[last].price


                                  }
                                  else{
                                         price = opposite_pricelist_data[0].price

                                  }
                             }
                        }
                        }
//          
                    }

                }
                else{

                }
            }
            else{
                var price = superProduct.get_price.apply(this, arguments);
            }
            return price;
        },
    });


    return models;


});