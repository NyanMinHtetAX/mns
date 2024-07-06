from odoo import models, fields, api,tools, _
import pytz
import logging
from itertools import groupby

_logger = logging.getLogger(__name__)


class PurchaseReports(models.Model):
    _name = 'purchase.lines.sql.report'
    _description = "New Vs Existing Vendor"
    _auto = False
    _rec_name = 'order_id'

    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    order_id = fields.Many2one('purchase.order', string='PO Number', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    uom_id = fields.Many2one('multi.uom.line', 'UoM', readonly=True)
    price_unit = fields.Float('Price Unit', readonly=True)
    qty_to_get = fields.Float('Qty Order', readonly=True)
    amount_of_buy = fields.Float('Amount of Order', readonly=True)
    received_qty = fields.Float('Qty Received', readonly=True)
    received_amount = fields.Float('Amount of Received', readonly=True)
    billed_qty = fields.Float('Qty Billed', readonly=True)
    billed_amount = fields.Float('Amount of Billed', readonly=True)
    qty_to_receive = fields.Float('Qty to Receive', readonly=True)
    amount_to_receive = fields.Float('Amount to Receive', readonly=True)
    qty_to_bill = fields.Float('Qty to Bill', readonly=True)
    amount_to_bill = fields.Float('Amount to Bill', readonly=True)
    discount_amount = fields.Float('Discount Amount', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    purchaser_id = fields.Many2one('res.users', string='Purchaser')
    return_qty = fields.Float('Return of Qty', readonly=True)
    return_amount = fields.Float('Return of Amount', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        company = self.env.company
        query = """

                    SELECT  
                            PL.ID AS ID,
                            P.COMPANY_ID AS COMPANY_ID,
                            P.PARTNER_ID AS PARTNER_ID,
                            P.DATE_ORDER AS DATE,
                            P.ID AS ORDER_ID,
                            PL.MULTI_UOM_LINE_ID AS UOM_ID,
                            PL.PRODUCT_ID AS PRODUCT_ID,
                            PL.MULTI_PRICE_UNIT AS PRICE_UNIT,
                            PL.PURCHASE_UOM_QTY AS QTY_TO_GET,
                            PL.PRICE_SUBTOTAL AS AMOUNT_OF_BUY,
                            PL.MULTI_QTY_RECEIVED AS RECEIVED_QTY,
                            SPT.WAREHOUSE_ID AS WAREHOUSE_ID,
                            P.PURCHASER_ID AS PURCHASER_ID,
                            PL.PURCHASE_RETURN_QTY AS RETURN_QTY,
                             CASE
                                WHEN P.STATE in ('purchase', 'done') AND PL.PURCHASE_RETURN_QTY !=0
                                THEN PL.PURCHASE_RETURN_QTY * PL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS RETURN_AMOUNT,
                            CASE
                                WHEN P.STATE in ('purchase', 'done') AND PL.MULTI_QTY_RECEIVED !=0
                                THEN PL.MULTI_QTY_RECEIVED * PL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS RECEIVED_AMOUNT,
                            PL.MULTI_QTY_INVOICED AS BILLED_QTY,
                            CASE
                                WHEN P.STATE in ('purchase', 'done') AND PL.MULTI_QTY_INVOICED !=0
                                THEN PL.MULTI_QTY_INVOICED * PL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS BILLED_AMOUNT,
                            CASE
                                WHEN P.STATE in ('purchase', 'done')
                                THEN (PL.PURCHASE_UOM_QTY - PL.MULTI_QTY_RECEIVED)
                                ELSE 0
                            END AS QTY_TO_RECEIVE,
                            CASE
                                WHEN P.STATE in ('purchase', 'done')
                                THEN (PL.PURCHASE_UOM_QTY - PL.MULTI_QTY_RECEIVED) * PL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS AMOUNT_TO_RECEIVE,
                            CASE
                                WHEN P.STATE in ('purchase', 'done')
                                THEN (PL.MULTI_QTY_RECEIVED - PL.MULTI_QTY_INVOICED)
                                ELSE 0
                            END AS QTY_TO_BILL,
                            CASE
                                WHEN P.STATE in ('purchase', 'done')
                                THEN (PL.MULTI_QTY_RECEIVED - PL.MULTI_QTY_INVOICED) * PL.MULTI_PRICE_UNIT
                                ELSE 0
                            END AS AMOUNT_TO_BILL,
                            PL.DISCOUNT_AMOUNT AS DISCOUNT_AMOUNT                     
                        
                    FROM    PURCHASE_ORDER_LINE PL
                            LEFT JOIN PURCHASE_ORDER P ON P.ID = PL.ORDER_ID
                            LEFT JOIN RES_PARTNER R ON R.ID = P.PARTNER_ID
                            LEFT JOIN STOCK_PICKING_TYPE SPT ON SPT.ID = P.PICKING_TYPE_ID
                    WHERE   PL.STATE != 'draft'
                    GROUP BY 	PL.ID,P.PARTNER_ID,P.ID,P.DATE_ORDER,P.COMPANY_ID,SPT.WAREHOUSE_ID,P.PURCHASER_ID"""
        # self.env.cr.execute(query, tuple(company))
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, query))
