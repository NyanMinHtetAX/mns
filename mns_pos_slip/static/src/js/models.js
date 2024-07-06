odoo.define('mns_pos_slip.models', function(require){
    'use strict';
    var models = require('point_of_sale.models');

    models.load_models([
    {
        label: 'Counter Logo',
        loaded: function (self) {
            self.config.logo = `data:image/png;base64,${self.config.logo}`;
        },
    },
    ]);

    return models;

});