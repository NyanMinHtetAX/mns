odoo.define('packaging_barcodes.models', function (require) {
'use strict';
    const models = require('point_of_sale.models');

    models.load_fields('product.packaging', ['use_in_pos','multi_uom_id']);
    models.load_fields('product.product', ['related_barcodes']);

    return models;
});