from odoo import api, models, fields


class RoutePlan(models.Model):

    _inherit = 'route.plan'

    def notify_to_sale_team(self):
        context = dict(self.env.context)
        context.update({
            'default_title': 'Route Plan Assign Notification',
            'default_message': f'{self.name} with reference {self.code} has been assigned to you.',
            'default_team_id': self.sale_team_id.id,
            'write_log': True,
        })
        return {
            'name': 'Notify',
            'type': 'ir.actions.act_window',
            'res_model': 'notify.wizard',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }
