from odoo import models, fields,api,_


class StockBackdateReport(models.Model):

    _name = 'stock.backdate.report'
    _description = 'Stock Backdate Report'
    _auto = False
    _rec_name = 'product_id'

    default_code = fields.Char('Internal Reference')
    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'Location')
    on_hand_qty = fields.Float('On Hand')
    uom_id = fields.Many2one('uom.uom', 'UoM')
    multi_uom_onhand_qty = fields.Char('Multi UOM On Hand Qty', compute='convert_to_multi_uom')
    value = fields.Float('Value')

    @api.depends('on_hand_qty')
    def convert_to_multi_uom(self):
        for rec in self:
            total_consumed_qty = 0
            multi_uom_qty = ''
            rec.multi_uom_onhand_qty = False
            product = rec.product_id
            qty = rec.on_hand_qty
            if product.multi_uom_ok and product.multi_uom_line_ids:
                lines = product.multi_uom_line_ids
                lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
                remaining_qty = qty
                for line in lines:
                    if total_consumed_qty == qty:
                        break
                    converted_qty = remaining_qty / line.ratio
                    if abs(converted_qty) >= 1:
                        multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                        consumed_qty = int(converted_qty) * line.ratio
                        remaining_qty -= consumed_qty
                        total_consumed_qty += consumed_qty
            else:
                multi_uom_qty = f'{qty} {product.uom_id.name}'
            rec.multi_uom_onhand_qty = multi_uom_qty

    @property
    def _table_query(self):
        company = self.env.company
        date = self.env.context.get('inventory_date', fields.Datetime.now())
        query = f"""
        SELECT      ROW_NUMBER() OVER(ORDER BY PRODUCT_ID, LOCATION_ID) AS ID, 
                    PRODUCT_ID, 
                    DEFAULT_CODE, 
                    LOCATION_ID, 
                    SUM(ON_HAND_QTY) AS ON_HAND_QTY,
                    UOM_ID,
                    ABS(SUM(VALUE)) AS VALUE
        FROM 
        (
        SELECT      SML.PRODUCT_ID,
                    PT.DEFAULT_CODE,
                    SML.LOCATION_ID,
                    SUM(
                        -SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                    ) AS ON_HAND_QTY,
                    PT.UOM_ID AS UOM_ID,
                    CASE
                        WHEN SL.USAGE = 'internal'
                        THEN (-SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)) * COALESCE(IP.VALUE_FLOAT, 0)
                        ELSE
                        SUM(
                            (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                        )
                    END AS VALUE
                    
        FROM        STOCK_MOVE_LINE SML
                    LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
                    LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
                    LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                    LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
                    LEFT JOIN IR_PROPERTY IP ON (IP.RES_ID=('product.product,' || PP.ID) AND IP.NAME='standard_price' AND IP.COMPANY_ID={company.id})
        WHERE       SML.DATE <= '{date}' AND SL.USAGE='internal' AND SML.STATE = 'done'
        GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_ID, PT.UOM_ID,SL.USAGE,LINE_UOM.FACTOR,PRODUCT_UOM.FACTOR,IP.VALUE_FLOAT
        
        UNION ALL
        
        SELECT      SML.PRODUCT_ID,
                    PT.DEFAULT_CODE,
                    SML.LOCATION_DEST_ID AS LOCATION_ID,
                    SUM(
                        SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                    ) AS ON_HAND_QTY,
                    PT.UOM_ID AS UOM_ID,
                    CASE
                        WHEN DL.USAGE = 'internal' 
                        THEN (SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)) * COALESCE(IP.VALUE_FLOAT, 0)
                        ELSE
                        SUM(
                            (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                        )
                    END AS VALUE
        FROM        STOCK_MOVE_LINE SML
                    LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
                    LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                    LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
                    LEFT JOIN IR_PROPERTY IP ON (IP.RES_ID=('product.product,' || PP.ID) AND IP.NAME='standard_price' AND IP.COMPANY_ID={company.id})
        WHERE       SML.DATE <= '{date}' AND DL.USAGE='internal' AND SML.STATE = 'done'
        GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_DEST_ID,DL.USAGE, PT.UOM_ID,LINE_UOM.FACTOR,PRODUCT_UOM.FACTOR, IP.VALUE_FLOAT
        ) AS STOCK_BACKDATE_REPORT  
        
        GROUP BY    PRODUCT_ID, DEFAULT_CODE, LOCATION_ID, UOM_ID      
        """
        return query
