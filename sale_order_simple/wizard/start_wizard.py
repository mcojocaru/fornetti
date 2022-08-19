# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StartWizard(models.Model):
    _name = 'sale_order_simple.start_wizard'

    name = fields.Char(default='')
    user_id = fields.Many2one('res.users', string='User', default=None)
    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile', default=None)
    flow_type = fields.Selection(related='profile_id.flow_type')

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
            res['flow_type'] = self.env.user.profile_id.flow_type
        return res

    def start_inventory(self):
        if self.profile_id.inventory_blocked_today:
            raise UserError("Nu mai puteti efectua alte ajustari de inventar !!")

        inventory = self.env["stock.inventory"].create(
            {
                'name': 'Inventory', 
                'company_id': self.profile_id.company_id.id,
                'exhausted': True
            })
        inventory.location_ids = [(6, 0, self.profile_id.warehouse_id.lot_stock_id.ids)]
        products = self.env.user.profile_id.product_ids.sorted(lambda l: l.sequence).mapped('product_id')
        products = products.filtered(lambda p: p.type == 'product')
        inventory.product_ids = [(6, 0, products.ids)]
        action = inventory.action_start()
        action['context'] = {'active_id': inventory.id, 'active_model': 'stock.inventory'}
        return action

    def start_sale(self):
        if self.profile_id.sale_blocked_today:
            raise UserError("Nu mai puteti efectua alte vanzari !!")        

        action = self.env['sale_order_simple.wizard'].create_wizard()
        return action


    def start_purchase(self):
        if self.profile_id.purchase_blocked_today:
            raise UserError("Nu mai puteti efectua alte intrari!!")        

        return self.env['sale_order_simple.purchase_wizard'].create_wizard()