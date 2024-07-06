from odoo import api, models, fields
from odoo.osv import expression


class StockLocation(models.Model):

    _inherit = 'stock.location'

    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if not args:
            args = []
        context = self.env.context
        if context.get('stock_request', False):
            if context.get('team_id', False):
                team_id = self.env['crm.team'].browse(self.env.context.get('team_id', False))
                if context.get('req_source', False):
                    domain = [('usage', '=', 'internal'),
                              ('id', 'in', team_id.allowed_location_ids.ids)]
                else:
                    domain = [('usage', '=', 'internal'),
                              ('id', '=', team_id.van_location_id.id)]
            else:
                domain = [('id', 'in', [])]
            args = expression.AND([
                args, domain
            ])
        return super(StockLocation, self)._search(args, offset, limit, order, count, access_rights_uid)
