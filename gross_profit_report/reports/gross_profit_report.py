from odoo import models, fields, api, tools


class GrossProfitReport(models.Model):
    _name = "gross.profit.sql.view"
    _description = 'Gross Profit Report'
    _auto = False
    _rec_name = 'product_id'

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    product_id = fields.Many2one('product.product', string='Product')
    product_category = fields.Many2one('product.category', string='Product Category')
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one('res.currency', string='Currency')
    uom = fields.Many2one('multi.uom.line', string='Sale UOM')
    uom_ratio = fields.Float(default=0, string='UOM Ratio')
    sale_price = fields.Monetary(string='Sale Price', currency_field='currency_id')
    purchased_uom = fields.Many2one('multi.uom.line', string='Purchased UOM')
    purchased_uom_ratio = fields.Float(default=0, string='Purchased UOM Ratio')
    purchased_price = fields.Monetary(string='Purchase Price', currency_field='currency_id')
    gp_amount = fields.Monetary(default=0, string='GP', currency_field='currency_id')
    gp_perc = fields.Float(string='GP(%)')

    def _select(self):
        return """
			SELECT
				ROW_NUMBER() OVER () as ID,
				PL.ID AS pricelist_id ,
				PIU.PRODUCT_ID AS product_id ,
				PT.CATEG_ID AS product_category ,
				PL.COMPANY_ID AS COMPANY_ID, 
				PL.CURRENCY_ID AS currency_id,
				mul.ID AS uom,
				mul.RATIO AS uom_ratio,

				CASE
					WHEN PIU.PRICE > 0 THEN ROUND(CAST(PIU.PRICE AS NUMERIC), 2)
					ELSE 0
				END AS sale_price,

				pmul.ID AS purchased_uom,
				pmul.RATIO AS purchased_uom_ratio,
				ROUND(CAST((PT.last_purchase_price_unit * MUL.RATIO) AS NUMERIC), 2) AS purchased_price,

				CASE 
					WHEN PT.last_purchase_price_unit > 0 THEN ROUND(CAST(PIU.PRICE - (PT.last_purchase_price_unit * MUL.RATIO) AS NUMERIC) , 2) 
					ELSE 0
				END AS gp_amount ,

				CASE
					WHEN PT.last_purchase_price_unit > 0 AND piu.price > 0 THEN ROUND((((PIU.PRICE - (PT.last_purchase_price_unit * MUL.RATIO)) / PIU.PRICE) * 100)::NUMERIC, 2) 
					ELSE 0
				END AS gp_perc

				FROM product_product AS PP
				LEFT JOIN product_template AS PT ON PP.PRODUCT_TMPL_ID = PT.ID 

				CROSS JOIN product_pricelist as PL
				LEFT JOIN pricelist_item_uom AS PIU ON PIU.PRODUCT_ID = PP.ID AND PIU.PRICELIST_ID = PL.ID
				LEFT JOIN multi_uom_line AS mul ON mul.id = piu.multi_uom_line_id
				LEFT JOIN uom_uom AS SU ON SU.id = mul.uom_id

				LEFT JOIN multi_uom_line AS pmul ON pmul.id = PT.last_purchase_multi_uom_id
				LEFT JOIN uom_uom AS mulpoluu ON mulpoluu.id = pmul.uom_id
				WHERE PT.type = 'product' AND PIU.product_id is not null AND PL.active = true
		"""

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'gross_profit_sql_view')

        query = '''
			CREATE OR REPLACE VIEW %s AS (
				%s
			)
		''' % ('gross_profit_sql_view', self._select())

        self.env.cr.execute(query)
