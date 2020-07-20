# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Profile(models.Model):
    _name = 'sale_order_simple.user_profile'
    
    name = fields.Char('Name', required=True)
    user_id = fields.Many2one('res.users', string="User")
    so_partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    product_ids = fields.One2many('sale_order_simple.profile_products', 'profile_id', string='Products', required=True)


class ProfileProducts(models.Model):
    _name = 'sale_order_simple.profile_products'

    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")
    product_id = fields.Many2one('product.product', string='Product')
    profile_id = fields.Many2one('sale_order_simple.user_profile', string="Profile")


class ResUsers(models.Model):
    _inherit = 'res.users'

    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile', compute='_compute_profile')

    def _compute_profile(self):
        for user in self:
            user.profile_id = self.env['sale_order_simple.user_profile'].search([('user_id', '=', user.id)])
