from odoo import models, fields, api, tools, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class ActiveCustomerListsReport(models.Model):
    _name = 'active.customer.list.sql.report'
    _description = "Active Customer Lists Report"
    _auto = False
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    date_order = fields.Datetime(string='SO Date', readonly=True)
    order_id = fields.Many2one('sale.order', string='SO No.', readonly=True)
    to_thirty_days = fields.Integer(string='0-30', readonly=True)
    to_sixty_days = fields.Integer(string='31-60', readonly=True)
    to_ninety_days = fields.Integer(string='61-90', readonly=True)
    to_one_twenty_days = fields.Integer(string='91-120', readonly=True)
    to_older_days = fields.Integer(string='Older', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sale Team', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesparson', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        my_query = """
                    WITH RankedOrders AS (
                        SELECT
                            SO.ID AS ID,
                            SO.PARTNER_ID AS PARTNER_ID,
                            SO.ID AS ORDER_ID,
                            SO.COMPANY_ID AS COMPANY_ID,
                            SO.DATE_ORDER AS DATE_ORDER,
                            SO.USER_ID AS USER_ID,
                            SO.TEAM_ID AS TEAM_ID,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) >= 0 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) <= 30 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) else 0 end) as TO_THIRTY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) >= 31 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) <= 60 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) else 0 end) as TO_SIXTY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) >= 61 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) <= 90 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) else 0 end) as TO_NINETY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) >= 91 AND 
                                (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) <= 120 
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) else 0 end) as TO_ONE_TWENTY_DAYS,
                            sum(case when (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) > 120  
                                then (cast(to_char(date_trunc('day',  now()) - date_trunc('day',so.date_order),'DD') AS INT)) else 0 end) as TO_OLDER_DAYS,                            
                            ROW_NUMBER() OVER (PARTITION BY SO.PARTNER_ID ORDER BY SO.DATE_ORDER DESC) AS RowNum
                        FROM
                            SALE_ORDER SO
                        WHERE
                            SO.STATE != 'draft' AND SO.DATE_ORDER IS NOT NULL
                        GROUP BY
                            SO.ID,
                            SO.PARTNER_ID,
                            SO.COMPANY_ID,
                            SO.DATE_ORDER,
                            SO.USER_ID,
                            SO.TEAM_ID
                    )
                    SELECT
                        ID,
                        PARTNER_ID,
                        ORDER_ID,
                        COMPANY_ID,
                        TO_THIRTY_DAYS,
                        TO_SIXTY_DAYS,
                        TO_NINETY_DAYS,
                        TO_ONE_TWENTY_DAYS,
                        TO_OLDER_DAYS,
                        USER_ID,
                        TEAM_ID,
                        DATE_ORDER
                    FROM
                        RankedOrders
                    WHERE
                        RowNum = 1
        """
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, my_query))
