odoo.define('pos_extend.ClientListScreen', function(require){

var ClientListScreen = require('point_of_sale.ClientListScreen');
var Registries = require('point_of_sale.Registries');

var ClientListScreenExtend = Component => class extends Component{

    async saveChanges(event) {
        var team_id = this.env.pos.config.crm_team_id ? this.env.pos.config.crm_team_id[0] : false;
        try {
            let partnerId = await this.rpc({
                model: 'res.partner',
                method: 'create_from_ui',
                args: [event.detail.processedChanges],
                kwargs: {team_id: team_id },
            });
            await this.env.pos.load_new_partners();
            this.state.selectedClient = this.env.pos.db.get_partner_by_id(partnerId);
            this.state.detailIsShown = false;
            this.render();
        } catch (error) {
            if (isConnectionError(error)) {
                await this.showPopup('OfflineErrorPopup', {
                    title: this.env._t('Offline'),
                    body: this.env._t('Unable to save changes.'),
                });
            } else {
                throw error;
            }
        }
    }

};

Registries.Component.extend(ClientListScreen, ClientListScreenExtend);

return ClientListScreenExtend;

});