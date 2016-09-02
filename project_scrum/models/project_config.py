# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    cancel_open_tasks_scrum = fields.Boolean(
        _(u'Cancell open taks when the sprint is closed?'))


class ProjectConfigSettings(models.TransientModel):
    _inherit = 'project.config.settings'

    cancel_open_tasks_scrum = fields.Boolean(
        _(u'Cancell open taks when the sprint is closed?'), help=_("""
        When closing a sprint the open tasks are cancelled and a copy
        of the task is made for the next sprint.
        """))

    def get_default_cancel_open_tasks_scrum(self, fields):
        user = self.env.user
        return {'cancel_open_tasks_scrum':
                user.company_id.cancel_open_tasks_scrum}

    @api.multi
    def set_cancel_open_tasks_scrum(self):
        self.env.user.company_id.cancel_open_tasks_scrum = \
            self.cancel_open_tasks_scrum
