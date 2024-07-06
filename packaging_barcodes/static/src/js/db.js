odoo.define('packaging_barcodes.db', function (require) {
    'use strict';

    const PosDB = require('point_of_sale.DB');
    PosDB.include({
        _product_search_string: function(product){
            var str = product.display_name;
            if (product.barcode) {
                str += '|' + product.barcode;
            }
            if (product.default_code) {
                str += '|' + product.default_code;
            }
            if (product.description) {
                str += '|' + product.description;
            }
            if (product.description_sale) {
                str += '|' + product.description_sale;
            }
            if (product.related_barcodes) {
                str += '|' + product.related_barcodes;
            }
            str = product.id + ':' + str.replace(/[\n:]/g,'') + '\n';
            return str;
        },
    });
});
