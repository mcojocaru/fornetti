# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _


class SaleOrderWizard(models.Model):
    _name = 'sale_order_simple.wizard'

    user_id = fields.Many2one('res.users', string='User')
    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile')
    line_ids = fields.One2many('sale_order_simple.wizard_line', 'wizard_id', string='Products')

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderWizard, self).default_get(fields)
        res['user_id'] = self.env.user.id
        if self.env.user.profile_id:
            res['profile_id'] = self.env.user.profile_id.id
            lines = []
            for product in self.env.user.profile_id.product_ids:
                lines.append((0, 0, 
                              {'product_id': product.id,
                               'product_uom_id': product.uom_id 
                           }))
            res['line_ids'] = lines
        return res

    @api.multi
    def confirm(self):
        pass


class SaleOrderWizardLine(models.Model):
    _name = 'sale_order_simple.wizard_line'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_id = fields.Many2one(related='product_id.uom_id')
    product_qty = fields.Float(string='Quantity')
    wizard_id = fields.Many2one('sale_order_simple.wizard', string='Wizard')
