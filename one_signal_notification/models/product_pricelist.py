from odoo import api, models, fields


class ProductPricelist(models.Model):

    _inherit = 'product.pricelist'

    def notify_to_sale_team(self):
        context = dict(self.env.context)
        context.update({
            'default_title': 'Pricelist Notification',
            'default_message': f'A new pricelist {self.name} has arrived.',
        })
        return {
            'name': 'Notify',
            'type': 'ir.actions.act_window',
            'res_model': 'notify.wizard',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }
