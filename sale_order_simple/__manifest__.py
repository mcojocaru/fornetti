# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Sale Order Simple',
    'version': '14.0.1.0.0',
    'category': 'Sales',
    'description': """
""",
    'website': '',
    'depends': ['l10n_ro', 'sale_stock', 'mrp', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_order_wizard.xml',
        'wizard/start_wizard.xml',
        'wizard/purchase_order_wizard.xml',
        'views/product_list.xml',
        'views/profiles.xml',
        'views/stock_warehouse_views.xml',        
        'views/res_config_settings_views.xml',
        'views/templates.xml',
        'data/data.xml',
        'data/data_categories.xml',
        'data/data_unbild.xml',
        'data/data_email.xml',
        'views/main.xml',
        ],
    'qweb': [
        "static/src/vue/xml/vue_tmpl.xml",
    ],
    'installable': True,
    'auto_install': False,
}
