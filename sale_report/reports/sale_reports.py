from odoo import models, fields, api,tools, _
import pytz
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class SaleReports(models.Model):
    _name = 'sale.cus.report'
    _description = "New Vs Existing Customer"
    _auto = False
    _rec_name = 'order_id'

    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    order_id = fields.Many2one('sale.order', string='SO Number', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    uom_id = fields.Many2one('multi.uom.line', 'UoM', readonly=True)
    price_unit = fields.Float('Price Unit', readonly=True)
    qty_order = fields.Float('QTY Order', readonly=True)
    amount_order = fields.Float('Amount of Order', readonly=True)
    deliver_qty = fields.Float('QTY Delivered', readonly=True)
    deliver_amount = fields.Float('Amount of Delivered', readonly=True)
    invoice_qty = fields.Float('QTY Invoiced', readonly=True)
    invoice_amount = fields.Float('Amount of Invoiced', readonly=True)
    qty_to_deliver = fields.Float('QTY to Deliver', readonly=True)
    amount_to_deliver = fields.Float('Amount to Deliver', readonly=True)
    qty_to_invoice = fields.Float('QTY to Invoice', readonly=True)
    amount_to_invoice = fields.Float('Amount to Invoice', readonly=True)
    discount_amount = fields.Float('Discount Amount', readonly=True)
    team_id = fields.Many2one('crm.team', string='Sale Team', readonly=True)
    user_id = fields.Many2one('res.users', string='SalesPerson', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    return_qty = fields.Float('Return of Qty', readonly=True)
    return_amount = fields.Float('Return of Amount', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        company = self.env.company
        query = """

                    SELECT  
                            SL.ID AS ID,
                            S.COMPANY_ID AS COMPANY_ID,
                            S.PARTNER_ID AS PARTNER_ID,
                            S.DATE_ORDER AS DATE,
                            S.ID AS ORDER_ID,
                            SL.MULTI_UOM_LINE_ID AS UOM_ID,
                            SL.PRODUCT_ID AS PRODUCT_ID,
                            SL.MULTI_PRICE_UNIT AS PRICE_UNIT,
                            SL.MULTI_UOM_QTY AS QTY_ORDER,
                            SL.PRICE_SUBTOTAL AS AMOUNT_ORDER,
                            SL.MULTI_QTY_DELIVERED AS DELIVER_QTY,
                            S.TEAM_ID AS TEAM_ID,
                            S.USER_ID AS USER_ID,
                            S.WAREHOUSE_ID AS WAREHOUSE_ID,
                            SL.SALE_RETURN_QTY AS RETURN_QTY,
                            CASE
                                WHEN S.STATE = 'sale' AND SL.SALE_RETURN_QTY !=0
                                THEN SL.SALE_RETURN_QTY * SL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS RETURN_AMOUNT,
                            CASE
                                WHEN S.STATE = 'sale' AND SL.MULTI_QTY_DELIVERED !=0
                                THEN SL.MULTI_QTY_DELIVERED * SL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS DELIVER_AMOUNT,
                            SL.MULTI_QTY_INVOICED AS INVOICE_QTY,
                            CASE
                                WHEN S.STATE = 'sale' AND SL.MULTI_QTY_INVOICED !=0
                                THEN SL.MULTI_QTY_INVOICED * SL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS INVOICE_AMOUNT,
                            CASE
                                WHEN S.STATE = 'sale'
                                THEN (SL.MULTI_UOM_QTY - SL.MULTI_QTY_DELIVERED)
                                ELSE 0
                            END AS QTY_TO_DELIVER,
                            CASE
                                WHEN S.STATE = 'sale'
                                THEN (SL.MULTI_UOM_QTY - SL.MULTI_QTY_DELIVERED) * SL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS AMOUNT_TO_DELIVER,
                            CASE
                                WHEN S.STATE = 'sale'
                                THEN (SL.MULTI_QTY_DELIVERED - SL.MULTI_QTY_INVOICED)
                                ELSE 0
                            END AS QTY_TO_INVOICE,
                            CASE
                                WHEN S.STATE = 'sale'
                                THEN (SL.MULTI_QTY_DELIVERED - SL.MULTI_QTY_INVOICED) * SL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS AMOUNT_TO_INVOICE,
                            SL.DISCOUNT_AMOUNT AS DISCOUNT_AMOUNT                     
                        
                    FROM    SALE_ORDER_LINE SL
                            LEFT JOIN SALE_ORDER S ON S.ID = SL.ORDER_ID
                            LEFT JOIN RES_PARTNER P ON P.ID = S.PARTNER_ID
                    WHERE   SL.STATE != 'draft'
                    GROUP BY 	SL.ID,S.PARTNER_ID,S.ID,S.DATE_ORDER,S.COMPANY_ID,S.TEAM_ID,S.USER_ID,S.WAREHOUSE_ID"""
        # self.env.cr.execute(query, tuple(company))
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, query))
