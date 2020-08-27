# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Sale Order Simple',
    'version': '1.1',
    'category': 'Sales',
    'description': """
""",
    'website': '',
    'depends': ['l10n_ro', 'sale_stock', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_order_wizard.xml',
        'wizard/start_wizard.xml',
        'wizard/purchase_order_wizard.xml',
        'views/product_list.xml',
        'views/profiles.xml',
        'views/res_config_settings_views.xml',
        'views/templates.xml',
        'data/data.xml',
        'data/data_categories.xml',
        'data/data_unbild.xml',
        'views/main.xml',
        ],
    'qweb': [
        "static/src/js/xml/react_tmpl.xml",
    ],
    'installable': True,
    'auto_install': False,
}
