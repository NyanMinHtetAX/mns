from odoo import models, fields, api, tools

class StockAgeReport(models.Model):
    _name = "stock_age_report.stock_age_sql_report"
    _description = "Stock Age Repot"
    _auto = False

    order_name = fields.Char(string='Order')
    supplier_id = fields.Many2one('res.partner', string='Supplier Name')
    move_id = fields.Many2one('stock.move', string='Stock Move')
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one('res.currency', string='Currency')
    to_location = fields.Many2one('stock.location', 'To')
    product_id = fields.Many2one('product.product', string='Product Name')
    internal_reference = fields.Char(string='Internal Reference')
    purchase_date = fields.Date(string='Purchase Date')
    purchase_datetime = fields.Datetime(string='Purchase DateTime')
    stock_aged_days = fields.Integer(default=0, string='Stock Aged Days')
    available_qtys = fields.Integer(string='Available', compute='_compute_multi_uom_onhand_qty')
    earlier_purchase_qtys = fields.Integer(string='Earlier Purchase', compute='_compute_multi_uom_onhand_qty')
    multi_uom_onhand_qty = fields.Char(string='Multi UOM Onhand Qty', compute="_compute_multi_uom_onhand_qty")
    onhand_qtys_in_pcs = fields.Integer(default=0, string='On Hand Qty (PCS)', compute='_compute_multi_uom_onhand_qty')
    qtys = fields.Integer(default=0, string='Stock In Qtys')
    out_qtys = fields.Integer(default=0, string='OutMove Qtys', compute='_compute_outmove_qtys')
    purchase_price = fields.Monetary(default=0, string='Purchase Price', currency_field='currency_id')
    total_amount = fields.Monetary(default=0, string='Total Amount', currency_field='currency_id',
                                   compute='_compute_multi_uom_onhand_qty')

    def _compute_outmove_qtys(self):
        for report in self:
            # Get All outmoves (Sale, Adj out, Scrap)
            out_domain = [
                ('product_id', '=', report.product_id.id),
                ('state', '=', 'done'),
                ('location_id.usage', '=', 'internal'),
                ('location_id', '=', report.to_location.id)
            ]
            out_moves = report.env['stock.move'].search(out_domain)
            report.out_qtys = sum([m.product_qty for m in out_moves])

    # Method from multi_uom_module
    def convert_to_multi_uom(self, product, qty_in_pcs):
        total_consumed_qty = 0
        multi_uom_qty = ''

        if product.multi_uom_ok and product.multi_uom_line_ids:
            lines = product.multi_uom_line_ids
            lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
            remaining_qty = qty_in_pcs
            for line in lines:
                if total_consumed_qty == qty_in_pcs:
                    break

                converted_qty = remaining_qty / line.ratio
                if abs(converted_qty) >= 1:
                    multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                    consumed_qty = int(converted_qty) * line.ratio
                    remaining_qty -= consumed_qty
                    total_consumed_qty += consumed_qty

        else:
            multi_uom_qty = f'{qty_in_pcs} {product.uom_id.name}'

        return multi_uom_qty if multi_uom_qty else f'{qty_in_pcs} {product.uom_id.name}'

    def _compute_multi_uom_onhand_qty(self):
        for report in self:
            # Earlier Purchase Moves / Adj In
            earlier_moves = self.env['stock.move'].search([
                ('product_id', '=', report.product_id.id),
                ('state', '=', 'done'),
                ('date', '<=', report.purchase_date),
                ('id', '<', report.move_id.id),
                # ('to_refund', '=', False),
                ('location_dest_id', '=', report.to_location.id)
            ])

            earlier_purchased_qtys = sum(
                [m.product_qty for m in earlier_moves])

            # If you wanna show Multi Uom Onhand qty as negative value, use this
            # max([report.qtys - (report.out_qtys - earlier_purchased_qtys), 0  if len(later_moves) != 0 else report.qtys - (report.out_qtys - earlier_purchased_qtys)])
            qtys_in_pcs = max([report.qtys - (report.out_qtys - earlier_purchased_qtys),
                               0]) if not earlier_purchased_qtys >= report.out_qtys else report.qtys
            # report.qtys
            report.multi_uom_onhand_qty = report.convert_to_multi_uom(report.product_id, qtys_in_pcs)
            report.onhand_qtys_in_pcs = qtys_in_pcs
            report.available_qtys = report.product_id.qty_available
            report.total_amount = report.product_id.standard_price * qtys_in_pcs
            report.earlier_purchase_qtys = earlier_purchased_qtys

    def _select(self):
        return """
			SELECT
				sm.id AS ID,
				sm.id as move_id,
				COALESCE(SM.origin, SM.reference) AS order_name, 
				SM.company_id AS company_id, 
				POL.partner_id AS supplier_id,
				POL.currency_id AS currency_id,
				PP.id AS product_id,
				PP.default_code AS internal_reference,
				SL.id AS to_location,
				SM.date AS purchase_date,
				SM.date AS purchase_datetime,
				CURRENT_DATE - SM.DATE::DATE AS stock_aged_days,
				-- Get Qty from purchase_order_line to get (Received - Returned)
				SM.product_qty AS qtys,
				POL.multi_price_unit AS purchase_price

				From stock_move as SM
					LEFT JOIN purchase_order_line AS POL ON POL.ID = SM.purchase_line_id
					LEFT JOIN res_partner AS  RP ON RP.ID = SM.partner_id
					LEFT JOIN product_product AS PP ON PP.ID = SM.product_id
					LEFT JOIN stock_location AS SL ON SL.ID = SM.location_dest_id
					LEFT JOIN stock_location AS SDL ON SDL.ID = SM.location_id
					WHERE SM.state = 'done' AND SL.usage = 'internal'
					-- Not include sale Lines
					-- AND SM.SALE_LINE_ID IS NULL
					-- Not include adjusment lines
					-- AND SM.ADJUSTMENT_ID IS NULL
					-- Not internal Transfers
					-- AND SDL.usage != 'internal'
					AND SM.PRODUCT_ID IN %(ids)s
					ORDER BY SM.date
		"""

    def init(self):
        ids = self.env['product.product'].search(
            [('product_tmpl_id', 'in', self.env['product.template'].search([('qty_available', '>', 0)]).ids)]).ids
        table = "stock_age_report_stock_age_sql_report"
        tools.drop_view_if_exists(self.env.cr, table)

        query = '''
			CREATE OR REPLACE VIEW %s AS (
				%s
			)
		''' % (table, self._select())

        self.env.cr.execute(query, {'ids': tuple(ids)})

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(StockAgeReport, self).search(args, offset, None, order, count)
        return res.filtered(lambda l: l.onhand_qtys_in_pcs > 0)