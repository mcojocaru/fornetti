# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Profile(models.Model):
    _name = 'sale_order_simple.user_profile'
    
    name = fields.Char('Name', required=True)
    user_id = fields.Many2one('res.users', string="User")
    so_partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    po_partner_id = fields.Many2one('res.partner', string='Supplier', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    sale_product_list_id = fields.Many2one('sale_order_simple.sale_product_list', string='Sale Product List', required=True)
    purchase_product_list_id = fields.Many2one('sale_order_simple.sale_product_list', string='Purchase Product List', required=True)
    product_ids = fields.One2many(related='sale_product_list_id.product_ids', string="Products")

class SaleProductList(models.Model):
    _name = 'sale_order_simple.sale_product_list'

    name = fields.Char('Name', default='', required=True)
    type = fields.Selection(string="Type", selection=[('sale', 'Vanzare'), ('purchase', 'Intrare')], default='sale')
    product_ids = fields.One2many('sale_order_simple.product_list_item', 'sale_product_list_id', string="Profile", copy=True)


class ProfileProducts(models.Model):
    _name = 'sale_order_simple.product_list_item'

    sale_product_list_id = fields.Many2one('sale_order_simple.sale_product_list', string='Sale Product List',
                                           required=True)
    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")
    product_id = fields.Many2one('product.product', string='Product')


class ResUsers(models.Model):
    _inherit = 'res.users'

    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile', compute='_compute_profile')

    def _compute_profile(self):
        for user in self:
            user.profile_id = self.env['sale_order_simple.user_profile'].search([('user_id', '=', user.id)])
