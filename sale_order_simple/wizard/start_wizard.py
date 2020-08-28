# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StartWizard(models.Model):
    _name = 'sale_order_simple.start_wizard'

    user_id = fields.Many2one('res.users', string='User', default=None)
    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile', default=None)
    flow_state = fields.Selection(related='profile_id.flow_state')

    @api.model
    def create_wizard(self):
        res_id = self.create({})

        form_view = self.env.ref('sale_order_simple.action_start_wizard_form')
        return {
            'name': 'Vanzare Produse',
            'res_model': self._name,
            'res_id': res_id.id,
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
        }

    @api.model
    def default_get(self, fields):
        res = super(StartWizard, self).default_get(fields)
        res['user_id'] = self.env.user.id
        profile_id = self.env.user.profile_id
        if profile_id:
            res['profile_id'] = self.env.user.profile_id.id
        return res

    def start_inventory(self):
        inventory = self.env["stock.inventory"].create({'name': 'Inventory'})
        inventory.location_ids = [(6, 0, self.env.ref('stock.stock_location_stock').ids)]
        products = self.env.user.profile_id.product_ids.sorted(lambda l: l.sequence).mapped('product_id')
        inventory.product_ids = [(6, 0, products.ids)]
        action = inventory.action_start()
        action['context'] = {'active_id': inventory.id, 'active_model': 'stock.inventory'}
        return action

    def start_sale(self):
        return self.env['sale_order_simple.wizard'].create_wizard()

    def start_purchase(self):
        return self.env['sale_order_simple.purchase_wizard'].create_wizard()