# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Sale Order Simple',
    'version': '1.1',
    'category': 'Sales',
    'description': """
""",
    'website': '',
    'depends': ['l10n_ro', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_order_wizard.xml',
        'views/profiles.xml',
        'views/main.xml',
        'views/res_config_settings_views.xml',
        'views/templates.xml',
        'data/data.xml',
        ],
    'qweb': [
        "static/src/js/xml/react_tmpl.xml",
    ],
        'installable': True,
    'auto_install': False,
}
