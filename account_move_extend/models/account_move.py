from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_reset = fields.Boolean(string="Is reset to draft", default=False)
    confirm_remark = fields.Text(string="Remark Before Confirm")

    def button_draft(self):
        values = super(AccountMove, self).button_draft()
        self.is_reset = True
        return values

    def write(self, vals):
        """Update model_name and model_model field values to reflect model_id
        changes."""
        for rec in self:
            if vals:
                if rec.state == "draft" and rec.move_type in ['out_invoice','in_invoice']:
                    if rec.is_reset:
                        if not vals.get('confirm_remark'):
                            if not rec.confirm_remark:
                                raise models.ValidationError('You have to add remark for reseted bill or invoice')

        return super().write(vals)

             
    



