from odoo import models, fields, api, tools, _


class ActiveSupplierListsReport(models.Model):
    _name = 'active.supplier.list.sql.report'
    _description = "Active Supplier Lists Report"
    _auto = False
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    date_approve = fields.Datetime(string='PO Date', readonly=True)
    order_id = fields.Many2one('purchase.order', string='PO No.', readonly=True)
    to_thirty_days = fields.Integer(string='0-30', readonly=True)
    to_sixty_days = fields.Integer(string='31-60', readonly=True)
    to_ninety_days = fields.Integer(string='61-90', readonly=True)
    to_one_twenty_days = fields.Integer(string='91-120', readonly=True)
    to_older_days = fields.Integer(string='Older', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    purchaser_id = fields.Many2one('res.users', 'Purchaser', readonly=True)
    user_id = fields.Many2one('res.users', 'Purchase Representative', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        my_query = """
                    WITH RankedOrders AS (
                        SELECT
                            PO.ID AS ID,
                            PO.PARTNER_ID AS PARTNER_ID,
                            PO.ID AS ORDER_ID,
                            PO.COMPANY_ID AS COMPANY_ID,
                            PO.PURCHASER_ID AS PURCHASER_ID,
                            PO.USER_ID AS USER_ID,
                            PO.DATE_APPROVE AS DATE_APPROVE,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) >= 0 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) <= 30 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) else 0 end) as TO_THIRTY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) >= 31 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) <= 60 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) else 0 end) as TO_SIXTY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) >= 61 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) <= 90 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) else 0 end) as TO_NINETY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) >= 91 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) <= 120 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) else 0 end) as TO_ONE_TWENTY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) > 120  
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',po.date_approve),'DD') AS INT)) else 0 end) as TO_OLDER_DAYS, 
                            ROW_NUMBER() OVER (PARTITION BY PO.PARTNER_ID ORDER BY PO.DATE_APPROVE DESC) AS RowNum
                        FROM
                            PURCHASE_ORDER PO
                        WHERE
                            PO.STATE != 'draft' AND PO.DATE_APPROVE IS NOT NULL
                        GROUP BY
                            PO.ID,
                            PO.PARTNER_ID,
                            PO.COMPANY_ID,
                            PO.PURCHASER_ID,
                            PO.USER_ID,
                            PO.DATE_APPROVE
                    )
                    SELECT
                        ID,
                        PARTNER_ID,
                        ORDER_ID,
                        COMPANY_ID,
                        PURCHASER_ID,
                        USER_ID,
                        TO_THIRTY_DAYS,
                        TO_SIXTY_DAYS,
                        TO_NINETY_DAYS,
                        TO_ONE_TWENTY_DAYS,
                        TO_OLDER_DAYS,
                        DATE_APPROVE
                    FROM
                        RankedOrders
                    WHERE
                        RowNum = 1
        """
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, my_query))
