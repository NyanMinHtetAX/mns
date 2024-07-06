from odoo import models,fields,api,_


class AboutUs(models.Model):
    _name = 'about.us'
    _description = 'About Us'

    shop_name = fields.Char(string='Shop Name')
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone')
    description = fields.Text(string='Description')

