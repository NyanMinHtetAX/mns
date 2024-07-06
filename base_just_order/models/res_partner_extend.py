from odoo import api, fields, models, tools, _
from odoo import exceptions
import random
import werkzeug.urls
from odoo.addons.auth_signup.models.res_partner import SignupError, now


def random_token():
    # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for _ in range(20))

class Partner(models.Model):
    _inherit = "res.partner"

    is_from_mobile = fields.Boolean(string='Is Mobile Customer?', default=False)
    check_new_customer = fields.Boolean(string='Is New Customers', compute='_get_new_customer',store=True)

    delivery_type = fields.Selection([
        ('home', 'Home'),
        ('work', 'Work'),
        ('car_gate',"Car Gate"),
        ('other', 'Other'),
    ], required=True, default='home')

    def _get_new_customer(self):
        for rec in self:
            rec.check_new_customer = False
            if not rec.ref and rec.is_from_mobile:
                rec.check_new_customer = True

    def signup_prepare_just_order(self, signup_type="signup", expiration=False):
        """ generate a new token for the partners with the given validity, if necessary
            :param expiration: the expiration datetime of the token (string, optional)
        """
        for partner in self:
            if expiration or not partner.signup_valid:
                token = random_token()
                while self._signup_retrieve_partner(token):
                    token = random_token()
                partner.sudo().signup_token= token
                partner.sudo().signup_type= signup_type
                partner.sudo().signup_expiration= expiration
        return True



class User(models.Model):
    _inherit = "res.users"

    

    def password_reset(self):
        if self.env.context.get('install_mode', False):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        self.mapped('partner_id').signup_prepare_just_order(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('auth_signup.reset_password_email')
        assert template._name == 'mail.template'

        email_values = {
            'email_cc': False,
            'auto_delete': True,
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            email_values['email_to'] = user.email
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.send_mail(user.id, force_send=force_send, raise_exception=True, email_values=email_values)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)

