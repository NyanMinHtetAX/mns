from odoo import fields, models, api, tools


class StockPicking(models.Model):
    _name = 'stock.picking.report'
    _description = 'Delivery Report'
    _auto = False

    assign_date = fields.Date("Assigned Date")
    delivery_date = fields.Date("Delivery Date")
    picking_no = fields.Char("Picking No")
    sale_customer = fields.Char("Sale Customer")
    delivery_address = fields.Char("Delivery Address")
    product = fields.Char("Product")
    assign_qty = fields.Integer("Assigned Qty")
    uom_assign = fields.Char(string="UOM")
    delivery_qty = fields.Integer("Delivery Qty")
    uom_delivery = fields.Char(string="UOM")
    return_qty = fields.Char("Return Qty")
    uom_return = fields.Char(string="UOM")

    @api.model
    def _query(self):
        query = """
            SELECT 
                PL.ID,
                DMP.ASSIGNED_DATE AS ASSIGN_DATE,
                DMP.DELIVERY_DATE AS DELIVERY_DATE,
                SP.NAME AS PICKING_NO,
                RP.NAME AS SALE_CUSTOMER,
                RP_AD.NAME AS DELIVERY_ADDRESS,
                PT.NAME AS PRODUCT,
                CAST(SM.MULTI_UOM_QTY AS INTEGER)AS ASSIGN_QTY,
                UOM.NAME AS UOM_ASSIGN,
                CAST(PL.QUANTITY_DONE AS INTEGER) AS DELIVERY_QTY,
                UOM.NAME AS UOM_DELIVERY,
                CAST(PL.QUANTITY_RETURN AS char) AS RETURN_QTY,
                UOM.NAME AS UOM_RETURN
            FROM PICKING_LINE PL
                LEFT JOIN DELIVERY_MAN_PICKING DMP ON DMP.ID =  PL.DELIVERY_PICKING_ID
                LEFT JOIN STOCK_PICKING SP ON SP.ID = DMP.PICKING_ID
                LEFT JOIN STOCK_MOVE SM ON SM.PICKING_ID = SP.ID
                LEFT JOIN RES_PARTNER RP ON RP.ID = DMP.SALE_CUSTOMER_ID
                LEFT JOIN RES_PARTNER RP_AD ON RP_AD.ID = DMP.CUSTOMER_ID
                LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = PL.PRODUCT_ID
                LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
                LEFT JOIN UOM_UOM UOM ON UOM.ID = PL.UOM_ID
            WHERE SP.COMPANY_ID = %s
            GROUP BY PL.ID,SP.NAME,DMP.ASSIGNED_DATE,DMP.DELIVERY_DATE,RP.NAME,RP_AD.NAME,PRODUCT,SM.MULTI_UOM_QTY,UOM.NAME,PL.QUANTITY_DONE,PL.QUANTITY_RETURN
                """
        return query

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("CREATE OR REPLACE VIEW %s AS (%s)" % (self._table, self._query() % self.env.user.company_id.id))
