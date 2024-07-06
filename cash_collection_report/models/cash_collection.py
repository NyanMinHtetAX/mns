from odoo import models, fields, api, tools


class CashCollection(models.Model):
    _name = 'cash.collection'
    _description = 'Cash Collection'
    _auto = False

    assigned_date = fields.Date(string="Assigned Date")
    to_collect_date = fields.Date(string="To Collect Date")
    collect_no = fields.Char(string="Collect No")
    customer = fields.Many2one('res.partner', string="Customer")
    invoice_address = fields.Many2one('res.partner', string="Invoice Address")
    assigned_amount = fields.Float(string="Assigned Amount")
    collected_amount = fields.Float(string="Collected Amount")
    remained_amount = fields.Float(string="Remained Amount")
    collector = fields.Char(string="Collector")
    assign_person = fields.Char(string="Assign Person")
    payment_date = fields.Date(string="Payment Date")

    @api.model
    def _query(self):
        query = """
            SELECT 
                PC.ID,
                PC.DATE AS assigned_date,
                PC.TO_COLLECT_DATE AS to_collect_date,
                PC.NAME AS collect_no,
                RP.ID AS customer,
                RP_CASH.ID AS invoice_address,
                SUM(PCL.AMOUNT_TOTAL) AS assigned_amount,
                COALESCE(SUM(PCL.AMOUNT_PAID), 0.0) AS collected_amount,
                COALESCE(SUM(PCL.AMOUNT_TOTAL) - SUM(PCL.AMOUNT_PAID), 0.0) AS remained_amount,
                RP_USER.NAME AS collector,
                RP_USER2.NAME AS assign_person,
                PCPL.DATE AS PAYMENT_DATE
            FROM 
                PAYMENT_COLLECTION PC
                LEFT JOIN RES_PARTNER RP ON RP.ID = PC.PARTNER_ID
                LEFT JOIN RES_PARTNER RP_CASH ON RP_CASH.ID = PC.INVOICE_ADDRESS_ID
                LEFT JOIN PAYMENT_COLLECTION_LINE PCL ON PCL.COLLECTION_ID = PC.ID
                LEFT JOIN RES_USERS RU ON RU.ID = PC.SALE_MAN_ID
                LEFT JOIN RES_USERS RU2 ON RU2.ID = PC.CREATE_UID
                LEFT JOIN RES_PARTNER RP_USER ON RU.PARTNER_ID = RP_USER.ID
                LEFT JOIN RES_PARTNER RP_USER2 ON RP_USER2.ID = RU2.PARTNER_ID
                LEFT JOIN PAYMENT_COLLECTION_PAYMENT_LINE PCPL ON PCPL.PAYMENT_COLLECTION_ID = PC.ID
            GROUP BY
                PC.ID, PC.DATE, PC.TO_COLLECT_DATE, PC.NAME, RP.ID, RP_CASH.ID, RP_USER.NAME, RP_USER2.NAME, PCPL.DATE
        """
        return query

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("CREATE OR REPLACE VIEW %s AS (%s)" % (self._table, self._query()))
