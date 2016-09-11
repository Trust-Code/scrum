# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Project Scrum',
    'summary': 'Scrum Management module maintained by Trustcode',
    'version': '10.0.1.0.0',
    'category': 'Project Management',
    'author': 'Vertel AB, Trustcode',
    'website': 'http://www.trustcode.com.br',
    'depends': ['project', 'mail'],
    'data': [
        'views/burndown_view.xml',
        'views/project_scrum_view.xml',
        'wizard/project_scrum_test_task_view.xml',
        'security/ir.model.access.csv',
        'security/project_security.xml',
        'security/project_task.xml',
        'views/project_config_settings_view.xml',
        'views/project_project.xml',
    ],
    'demo': ['demo/project_scrum.xml'],
    'installable': True,
    'application': True,
}
