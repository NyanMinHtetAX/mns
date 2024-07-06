from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    slip_image = fields.Image('Slip Image')
    partner_class_id = fields.Many2one('partner.class', related='partner_id.partner_class_id', string='Customer Class')
    payment_type = fields.Selection(string='Payment Type', related='partner_id.payment_type')
    fleet_id = fields.Many2one('fleet.vehicle', string='Car Model')
    license_plate = fields.Char(string='License Plate', related='fleet_id.license_plate')
    remark = fields.Text('Remarks')
    foc_amount = fields.Char('FOC Amount')
    city_id = fields.Many2one('res.city', string='Cities', related='partner_id.x_city_id', store=True)
    delivery_note = fields.Text('Delivery Note')
    delivery_type = fields.Selection([('delivery', 'Delivery'),
                                      ('pickup', 'Pickup')], 'Delivery Type')
    real_due_amount = fields.Float('Credit Due Amount', default='0.0', compute='compute_real_due_amount')
    payment_due_amount = fields.Float('Payment Due Amount', default='0.0', compute='compute_payment_due_amount')
    payment_return_due_amount = fields.Float('Payment Return Due Amount', default='0.0',
                                             compute='compute_payment_due_amount')

    def unlink(self):
        for order in self:
            if order.picking_ids:
                raise UserError(_('You can not remove an order line once the sales order is delivered.'))
        return super(SaleOrder, self).unlink()

    @api.depends('credit_limit', 'total_due')
    def compute_real_due_amount(self):
        for rec in self:
            if rec.credit_limit and rec.total_due:
                if rec.credit_limit < rec.total_due:
                    rec.real_due_amount = rec.total_due - rec.credit_limit
                else:
                    rec.real_due_amount = 0.0
            else:
                rec.real_due_amount = 0.0

    @api.depends('partner_id')
    def compute_payment_due_amount(self):
        for rec in self:
            rec.payment_due_amount = 0.0
            rec.payment_return_due_amount = 0.0
            if rec.partner_id:
                invoices = self.env['account.move'].search(
                    [('partner_id', '=', rec.partner_id.id), ('amount_residual', '!=', 0), ('state', '=', 'posted')])
                today = fields.date.today()
                if invoices:
                    invoice = invoices.filtered(lambda l: l.invoice_date_due < today)
                    if invoice:
                        for inv in invoice:
                            if inv.move_type == 'out_invoice':
                                rec.payment_due_amount += inv.amount_residual
                            elif inv.move_type == 'out_refund':
                                rec.payment_return_due_amount -= inv.amount_residual
                            else:
                                rec.payment_due_amount += 0.0
                                rec.payment_return_due_amount -= 0.0
                    else:
                        rec.payment_due_amount = 0.0
                        rec.payment_return_due_amount = 0.0
                else:
                    rec.payment_due_amount = 0.0
                    rec.payment_return_due_amount = 0.0
            else:
                rec.payment_due_amount = 0.0
                rec.payment_return_due_amount = 0.0


    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'total_due': self.partner_id.amount_due,
            'fleet_id': self.fleet_id.id,
            'is_sale_order': True,
            'remark': self.remark,
            'foc_amount': self.foc_amount,
        })
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for do_pick in self.picking_ids:
            do_pick.write({
                'total_due': self.partner_id.amount_due,
                'fleet_id': self.fleet_id.id,
                'is_sale_order': True,
            })
        for order in self:
            data_payload = {
                'model': 'sale.order',
                'order_id': order.id,
                'app_order_state': "Confirmed",
            }
            order.partner_id.send_onesignal_notification('Order Processing', 'Your order is currently processing.',
                                                         data_payload)
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    total_due = fields.Float('Total Due Amount', readonly=True, store=True)
    partner_class_id = fields.Many2one('partner.class', related='partner_id.partner_class_id')

    fleet_id = fields.Many2one('fleet.vehicle', string='Model')
    license_plate = fields.Char(string='License  Plate', related='fleet_id.license_plate')

    is_sale_order = fields.Boolean(string='Is Sale Order', default=False)
    remark = fields.Text('Remarks', related='sale_id.remark')
    payment_type = fields.Selection(string='Payment Type', related='partner_id.payment_type')
