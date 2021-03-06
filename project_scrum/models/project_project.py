# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FMT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FMT


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    closed = fields.Boolean(u'Estado Concluído?')
    cancelled = fields.Boolean(u'Estado Cancelado?')


class ProjectTask(models.Model):
    _inherit = "project.task"
    _order = "sequence"

    user_id = fields.Many2one('res.users', 'Assigned to', select=True,
                              track_visibility='onchange', default="")
    actor_ids = fields.Many2many(
        comodel_name='project.scrum.actors', string='Actor')
    sprint_id = fields.Many2one(
        comodel_name='project.scrum.sprint', string='Sprint')
    us_id = fields.Many2one(
        comodel_name='project.scrum.us', string='User Stories')
    use_scrum = fields.Boolean(related='project_id.use_scrum')
    closed = fields.Boolean(related='stage_id.closed')
    cancelled = fields.Boolean(related='stage_id.cancelled')
    description = fields.Html('Description')
    points = fields.Integer('Points')

    def _daterange(self, start_date, end_date):
        available_dates = []
        for n in range(int((end_date - start_date).days)):
            single_date = start_date + timedelta(days=n, hours=12)
            if single_date.weekday() != 5 and single_date.weekday() != 6:
                available_dates.append(single_date)
        return available_dates

    def _update_projected_burndown(self, vals):
        sprint = self.sprint_id
        if "sprint_id" in vals:
            sprint = self.env['project.scrum.sprint'].browse(vals["sprint_id"])
        if sprint and sprint.date_start and sprint.date_stop:
            bnd = self.env['project.burndown'].search(
                [('sprint_id', '=', sprint.id)])
            for item in bnd:
                item.unlink()
            points = sprint.total_points
            if "points" in vals and self.id:
                points += (vals["points"] - self.points)

            start_date = datetime.strptime(sprint.date_start, DATE_FMT)
            end_date = \
                datetime.strptime(sprint.date_stop, DATE_FMT) + timedelta(1)

            available_dates = self._daterange(start_date, end_date)
            closed_tasks = sprint.task_ids.filtered(
                lambda x: x.stage_id.closed)
            if "stage_id" in vals and self.id:
                stage = self.env['project.task.type'].browse(vals['stage_id'])
                if stage.closed:
                    closed_tasks |= sprint.task_ids.filtered(
                        lambda x: x.id == self.id)
                elif self.stage_id.closed:
                    closed_tasks = closed_tasks.filtered(
                        lambda x: x.id != self.id)

            points_day = points / float(len(available_dates) - 1 or 1)
            points_left = points
            points_real = points
            for single_date in available_dates:
                burndown = {'type': 'projected', 'day': single_date,
                            'points': points_left, 'sprint_id': sprint.id}
                self.env['project.burndown'].create(burndown)
                points_left -= points_day
                if points_left < 0.1:
                    points_left = 0

                today_str = datetime.now().strftime(DATETIME_FMT)
                tasks_today = closed_tasks.filtered(
                    lambda x: datetime.strptime((x.date_end or today_str),
                                                DATETIME_FMT) >= single_date +
                    timedelta(hours=-12) and datetime.strptime(
                        (x.date_end or today_str),
                        DATETIME_FMT) < single_date + timedelta(hours=12))

                points_today = sum(task.points for task in tasks_today)
                points_real -= points_today
                burndown = {'type': 'real', 'day': single_date,
                            'points': points_real, 'sprint_id': sprint.id}
                self.env['project.burndown'].create(burndown)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({
            'sprint_id': None,
        })
        return super(ProjectTask, self).copy(default)

    @api.model
    def create(self, values):
        result = super(ProjectTask, self).create(values)
        self._update_projected_burndown(values)
        return result

    @api.multi
    def write(self, vals):
        if self.env['project.task.type'].browse(vals.get('stage_id')).closed:
            vals['date_end'] = fields.datetime.now()
        if "points" in vals:
            self._update_projected_burndown(vals)
        if "stage_id" in vals:
            self._update_projected_burndown(vals)

        return super(ProjectTask, self).write(vals)

    @api.model
    def _read_group_sprint_id(self, present_ids, domain, **kwargs):
        project = self.env['project.project'].browse(
            self._resolve_project_id_from_context())

        if project.use_scrum:
            sprints = self.env['project.scrum.sprint'].search(
                [('project_id', '=', project.id)], order='sequence').name_get()
            return sprints, None
        else:
            return [], None

    @api.model
    def _read_group_us_id(self, present_ids, domain, **kwargs):
        project = self.env['project.project'].browse(
            self._resolve_project_id_from_context())

        if project.use_scrum:
            user_stories = self.env['project.scrum.us'].search(
                [('project_id', '=', project.id)], order='sequence').name_get()
            return user_stories, None
        else:
            return [], None

    _group_by_full = {
        'sprint_id': _read_group_sprint_id,
        'us_id': _read_group_us_id,
    }

    @api.model
    def filter_current_sprint(self):
        sprint = self.env['project.scrum.sprint']
        user = self.env.user
        view_type = 'kanban,form,tree'
        team_id = user.scrum_team_id.id
        sprint_ids = sprint.search([('state', '=', 'open'),
                                    ('scrum_team_id', '=', team_id)])
        if sprint_ids:
            self._cr.execute('select distinct project_id from project_task\
                       where sprint_id = %s' % sprint_ids[0])
            project_ids = self._cr.fetchall()
            context = {'search_default_project_id': project_ids}
            value = {
                'domain': [('state_sprint', '=', 'open')],
                'context': context,
                'name': _('Current Sprint'),
                'view_type': 'form',
                'view_mode': view_type,
                'res_model': 'project.task',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }
        else:
            value = {
                'domain': [('id', '=', 0)],
                'name': _('Current Sprint'),
                'view_type': 'form',
                'view_mode': view_type,
                'res_model': 'project.task',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'help': 'No sprint running.',
            }
        return value
