# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, _lt, api, fields, models


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    sale_pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
	)