from odoo import models, fields, api, _


class SalePricelistRecord(models.Model):
    _name = 'sale.pricelist.record'
    _description = 'Sale Pricelist History Record'
    _rec_name = 'ticket_number'
    _order = 'id desc'

    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        domain=[('supplier', '=', True)], ondelete='cascade', required=True,
        help="Customer of this product")
    sequence = fields.Integer(
        'Sequence ', default=1, help="Assigns the priority to the list of product Customer.")
    price = fields.Float(
        'Price ', default=0.0, digits='Product Price',
        required=True, help="The price to Sell a product")
    currency_id = fields.Many2one(
        'res.currency', 'Currency ',
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True)
    product_tmpl_id = fields.Many2one(
        'product.product', 'Product ',
        index=True, ondelete='cascade')
    ticket_date = fields.Datetime(string="Ticket Date ")
    ticket_number = fields.Char(string="SO Number", required=True)
    sale_qty = fields.Integer(string="Sale Quantity")



