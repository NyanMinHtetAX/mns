odoo.define("dynamic_access_rights.controls", function(require) {
    let FormController = require('web.FormController');
    let ListRenderer = require('web.ListRenderer');

    FormController.include({
        _onQuickEdit: function () {},
    });


    ListRenderer.include({

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            if (this.getParent() && this.getParent().mode !== 'edit') {
                this.creates = [];
                this.addTrashIcon = false;
            }
        },

    });

})

