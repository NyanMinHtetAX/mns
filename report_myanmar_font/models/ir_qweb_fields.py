# -*- coding: utf-8 -*-
from markupsafe import Markup, escape
from odoo import api, fields, models, _, _lt

######################################################################################
# Below Code make auto-translate to zawgyi while pdf is generating for t-field
# But not for t-esc, i am still working on that
######################################################################################
class HTMLConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field.html'

    @api.model
    def value_to_html(self, value, options):
        return super(HTMLConverter, self).value_to_html(self.convert_font(value), options)
class ManyToManyConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field.many2many'

    @api.model
    def value_to_html(self, value, options):
        return self.convert_font(super(ManyToManyConverter, self).value_to_html(value, options))

class ManyToOneConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field.many2one'

    @api.model
    def value_to_html(self, value, options):
        return self.convert_font(super(ManyToOneConverter, self).value_to_html(value, options))


class SelectionConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field.selection'

    @api.model
    def value_to_html(self, value, options):
        return super(SelectionConverter, self).value_to_html(self.convert_font(value), options)

class TextConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field.text'

    @api.model
    def value_to_html(self, value, options):
        return super(TextConverter, self).value_to_html(self.convert_font(value), options)

class FieldConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field'

    @api.model
    def value_to_html(self, value, options):
        return super(FieldConverter, self).value_to_html(self.convert_font(value), options)

class Contact(models.AbstractModel):
    _inherit = 'ir.qweb.field.contact'

    @api.model
    def value_to_html(self, value, options):
        if not value:
            return ''

        opf = options.get('fields') or ["name", "address", "phone", "mobile", "email"]
        sep = options.get('separator')
        template_options = options.get('template_options', {})
        if sep:
            opsep = escape(sep)
        elif template_options.get('no_tag_br'):
            # escaped joiners will auto-escape joined params
            opsep = escape(', ')
        else:
            opsep = Markup('<br/>')

        value = value.sudo().with_context(show_address=True)
        name_get = value.name_get()[0][1]

        name_get = self.convert_font(name_get)

        # Avoid having something like:
        # name_get = 'Foo\n  \n' -> This is a res.partner with a name and no address
        # That would return markup('<br/>') as address. But there is no address set.
        if any(elem.strip() for elem in name_get.split("\n")[1:]):
            address = opsep.join(name_get.split("\n")[1:]).strip()
        else:
            address = ''
        val = {
            'name': name_get.split("\n")[0],
            'address': address,
            'phone': value.phone,
            'mobile': value.mobile,
            'city': value.city,
            'country_id': value.country_id.display_name,
            'website': value.website,
            'email': value.email,
            'vat': value.vat,
            'vat_label': value.country_id.vat_label or _('VAT'),
            'fields': opf,
            'object': value,
            'options': options
        }
        return self.env['ir.qweb']._render('base.contact', val, **template_options)

