import json
from odoo import api, models, fields, _
from lxml import etree


class Users(models.Model):

    _inherit = 'res.users'


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Users, self).fields_view_get(view_id=view_id,
                                                 view_type=view_type,
                                                 toolbar=toolbar,
                                                 submenu=submenu)
        if view_type != 'form':
            return res
        doc = etree.XML(res['arch'])
        page = doc.find(".//page[@name='access_rights']")
        notebook = page.getparent()
        group = doc.find(".//page[@name='access_rights']//group[@string='Other']")
        hide_group = self.env.ref('base_fieldsale.group_hide_mobile_field_sale')
        root_group = group.getparent()
        xml_to_add = """
        <page>
            <group col="2"
                   attrs="{'invisible': [('sel_groups_1_9_10', '!=', 1)]}"
                   modifiers='{"invisible": [["sel_groups_1_9_10", "!=", 1]]}'>
                <group>
                    <newline/>
                        HELLO
                    <newline/>
                </group>
            </group>
        </page>
        """
        notebook.insert(notebook.index(page) + 1, etree.XML(xml_to_add))
        # for field in model_fields:
        #     field = doc.xpath(f"//field[@name='{field}']")
        #     if not field:
        #         continue
        #     modifiers = json.loads(field[0].get('modifiers'))
        #     if is_hr_supervisor:
        #         modifiers.update({'readonly': [('state', 'in', ['validate', 'refuse'])]})
        #         field[0].set('modifiers', json.dumps(modifiers))
        #
        #     else:
        #         modifiers.update({'readonly': [('state', '!=', 'draft')]})
        #         field[0].set('modifiers', json.dumps(modifiers))

        res['arch'] = etree.tostring(doc)

        return res
