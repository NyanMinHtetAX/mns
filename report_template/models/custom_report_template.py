# -*- coding: utf-8 -*-

from odoo import fields, models


class CustomReportTemplate(models.Model):
    _name = 'custom.report.template'
    _description = 'Report Dynamic Report'
    _inherit = ['format.address.mixin', 'image.mixin']
    _rec_name = "name"

    name = fields.Char('Name')
    report_name = fields.Selection([('customize', 'Customization'),
                                    ('internal', 'Internal')], string='Report Name', default='customize')
    company_name = fields.Char('Company Name')
    parent_name = fields.Char('Parent Name')
    service_phone = fields.Char('Phone No Label Name')
    other_phone = fields.Char('Other Phone')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    website = fields.Char('Website')
    email = fields.Char('Email')
    bank_info_ids = fields.One2many('custom.report.template.line', 'bank_info_id', 'Add Bank Info')
    footer = fields.Text('Footer')
    note = fields.Text('Term & Conditions')

    # For Customize Header Footer
    title1 = fields.Char('Title One')
    title2 = fields.Char('Title Two')
    address = fields.Char('Address')
    company_phone = fields.Char('Phone Numbers')
    social_viber = fields.Char('Viber, Facebook & Wechat')
    social_mail = fields.Char('Gmail & Website')
    thank = fields.Text('Thank Note')
    complain = fields.Char('Complain')
    remark_note = fields.Text('Note')
    # For Customize Header Footer


class CustomReportTemplateLine(models.Model):
    _name = 'custom.report.template.line'
    _description = 'Bank Information'

    number = fields.Char('Account Number')
    name = fields.Char('Bank Name')
    bank_info_id = fields.Many2one('custom.report.template')
