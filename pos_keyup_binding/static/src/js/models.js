odoo.define('pos_keyup_binding.models', function(require){
    'use strict';

    var pos_models = require('point_of_sale.models');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const SelectionPopup = require('point_of_sale.SelectionPopup');
    const MultiUOMPopup = require('multi_uom.MultiUOMPopup');
    const { Gui } = require('point_of_sale.Gui');
    const { useExternalListener } = owl.hooks;

    const ProductScreenExtend = ProductScreen => class extends ProductScreen {
        constructor() {
            super(...arguments);
            useExternalListener(window, 'keyup', this._NewscreenAtEnter);
            useExternalListener(window, 'keyup', this.focusSearchInput);
        }

        // Shortcut Key For MultiUOMPopup 13 July 2023 MPP ( Key = 'm' )
        _showMultiUoMPopup(){
            const order = this.env.pos.get_order();
            const selectedOrderline = order.selected_orderline;
            if(selectedOrderline){
                const product = selectedOrderline.product;
                const productTemplate = product.product_tmpl_id;
                var multi_uom_lines = this.env.pos.multi_uom_lines.filter((e) => e.product_tmpl_id[0] === productTemplate);
                multi_uom_lines = multi_uom_lines.map(l => {
                    var price = product.get_price(order.pricelist, l.ratio, false, l);
                    if(this.env.pos.config.pricelist_mode != 'uom'){
                        price = price * l.ratio;
                    }
                    return  {...l, price: price};
                });
                multi_uom_lines.sort((a, b) => a.price > b.price);
                if(multi_uom_lines.length > 0 && product.multi_uom_ok){
                    order.showing_uom_popup = true;
                    Gui.showPopup('MultiUOMPopup', {
                            title: 'Select a UOM to change.',
                            list: multi_uom_lines,
                    });
                }
                else{
                    Gui.showPopup('ErrorPopup', {
                        confirmText: 'OK',
                        cancelText: 'Cancel',
                        title: 'Error',
                        body: 'Selected product is not available for multi UOM.',
                    });
                }
            }
            else{
                Gui.showPopup('ErrorPopup', {
                    confirmText: 'OK',
                    cancelText: 'Cancel',
                    title: 'Error',
                    body: 'Please select an order line first.',
                });
            }
        }
        // Shortcut Key For MultiUOMPopup 13 July 2023 MPP ( Key = 'm' )

        _NewscreenAtEnter(event) {
            if (event.key === ' ' && !$("[placeholder='Search Products...']").is(":focus")) {
                this._onClickPay();
            }
            // Shortcut Key For MultiUOMPopup 13 July 2023 MPP ( Key = 'm' )
            if (event.key === 'm' && !$("[placeholder='Search Products...']").is(":focus")){
                this._showMultiUoMPopup();
            }
            // Shortcut Key For MultiUOMPopup 13 July 2023 MPP ( Key = 'm' )
        }

        focusSearchInput(event){
            if(event.key === 's' || event.key === 'S' ){
                event.stopPropagation();
                var [input] = $.find(`[placeholder='Search Products...']`);
                input.focus();
            }
        }
    }

    // Shortcut Key For Selecting UOM Lines 14 July 2023 MPP ( ArrowUp & ArrowDown & ArrowRight & ArrowLeft )
    const MultiUOMPopupExtend = MultiUOMPopup => class extends MultiUOMPopup {
        constructor() {
            super(...arguments);
            useExternalListener(window, 'keyup', this._NewscreenAtEnter);
            useExternalListener(window, 'keyup', this._onClickButtonAction);
        }

        _NewscreenAtEnter(event){
            let itemId = 0;
            const list = this.props.list;
            //For UOM 2 Lines
            if (list.length > 1 && list.length < 3){
                if(event.key === 'ArrowDown'){
                    event.preventDefault();
                    itemId = list.length - 1;
                }
                else if(event.key === 'ArrowUp'){
                    event.preventDefault();
                    itemId = list.length - 2;
                }
                else{
                    return
                }
            }
            //For UOM 2 Lines

            //For UOM 3 Lines
            else if (list.length === 3){
                if(event.key === 'ArrowDown'){
                    event.preventDefault();
                    itemId = list.length - 2;
                }
                else if(event.key === 'ArrowRight'){
                    event.preventDefault();
                    itemId = list.length - 1;
                }
                else if(event.key === 'ArrowUp'){
                    event.preventDefault();
                    itemId = list.length - 3;
                }
                else{
                    return
                }
            }
            //For UOM 3 Lines

            //For UOM 4 Lines
            else if (list.length === 4){
                if(event.key === 'ArrowDown'){
                    event.preventDefault();
                    itemId = list.length - 3;
                }
                else if(event.key === 'ArrowRight'){
                    event.preventDefault();
                    itemId = list.length - 2;
                }
                else if(event.key === 'ArrowUp'){
                    event.preventDefault();
                    itemId = list.length - 1;
                }
                else if(event.key === 'ArrowLeft'){
                    event.preventDefault();
                    itemId = list.length - 4;
                }
                else{
                    return
                }
            }
            //For UOM 4 Lines
            else{
                    return
                }

            itemId = list[itemId].id
            this.selectItem(itemId)

        }
        // Shortcut Key For MultiUOM Confirm( Key = 'c' ) & Cancel( Key = 'x' ) 18 July 2023 MPP
        _onClickButtonAction(event){
            if(event.key === 'c'){
                this.confirm();
            }
            else if(event.key === 'x'){
                this.cancel();
            }
            else{
                return
            }
        }
        // Shortcut Key For MultiUOM Confirm( Key = 'c' ) & Cancel( Key = 'x' ) 18 July 2023 MPP
    }
    // Shortcut Key For Selecting UOM Lines 14 July 2023 MPP ( ArrowUp & ArrowDown & ArrowRight & ArrowLeft )

    const PaymentScreenExtend = PaymentScreen => class extends PaymentScreen {
        constructor() {
            super(...arguments);
            useExternalListener(window, 'keyup', this._NewscreenAtEnter);
        }
        _NewscreenAtEnter(event) {
            if (event.key === ' ') {
                this.validateOrder(false);
            }
        }
    }

    const ReceiptScreenExtend = ReceiptScreen => class extends ReceiptScreen {
        constructor() {
            super(...arguments);
            useExternalListener(window, 'keyup', this._NewscreenAtEnter);
        }
        _NewscreenAtEnter(event) {
            if (event.key === ' ') {
                this.orderDone();
            }
            if (event.key === 'P' || event.key === 'p') {
                this.printReceipt();
            }
        }
    }

    Registries.Component.extend(ProductScreen, ProductScreenExtend);
    Registries.Component.extend(PaymentScreen, PaymentScreenExtend);
    Registries.Component.extend(ReceiptScreen, ReceiptScreenExtend);
    Registries.Component.extend(MultiUOMPopup, MultiUOMPopupExtend);

    return ProductScreenExtend;
});