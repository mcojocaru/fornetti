# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'

    amount_prev_day = fields.Float(string='Amount Previous Day', default=0.0, tracking=True)


class Profile(models.Model):
    _inherit = ['mail.thread']
    _name = "sale_order_simple.user_profile"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    user_id = fields.Many2one('res.users', string="User")
    amount_prev_day = fields.Float(related='company_id.amount_prev_day', readonly=False)
    current_cash_amount = fields.Float(related="user_id.current_cash_amount", readonly=False, tracking=True)

    flow_type = fields.Selection(
                selection=[
                    ('inventory', 'Doar Inventar'), 
                    ('inventory_input_output', 'Inventar - Intrare - Vanzare'), 
                    ('input', 'Doar Intrare')
                ], 
                string="Flow Type", 
                default='inventory_input_output')
    flow_state = fields.Selection(strong='Current Flow State',
                selection=[
                    ('none', ''),
                    ('inventory', 'Inventar'), 
                    ('input', 'Intrare'), 
                    ('output', 'Vanzare')
                ], 
                default='none')

    so_partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    po_partner_id = fields.Many2one('res.partner', string='Supplier', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=False)
    sale_product_list_id = fields.Many2one('sale_order_simple.sale_product_list', string='Sale Product List', required=True)
    product_ids = fields.One2many(related='sale_product_list_id.product_ids', string="Products")
    expense_product_ids = fields.One2many(related='sale_product_list_id.expense_product_ids', string="Expeses")

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)])

    def do_next_flow_state(self):
        if self.flow_type == 'inventory':
            self.flow_state = 'inventory'

        elif self.flow_type == 'input':
            self.flow_state = 'input'

        elif self.flow_type == 'inventory_input_output':
            if self.flow_state in ('none', 'inventory'):
                self.flow_state = 'input'

            elif self.flow_state == 'input':
                self.flow_state = 'output'

            elif self.flow_state == 'output':
                self.flow_state = 'inventory'


class SaleProductList(models.Model):
    _name = 'sale_order_simple.sale_product_list'

    name = fields.Char('Name', default='', required=True)
    type = fields.Selection(string="Type", selection=[('sale', 'Vanzare'), ('purchase', 'Intrare')], default='sale')
    product_ids = fields.One2many('sale_order_simple.product_list_item', 'sale_product_list_id', string="Products", copy=True)
    expense_product_ids = fields.One2many('sale_order_simple.product_list_item', 'sale_product_list_exp_id', string="Expenses",
                                  copy=True)


class ProfileProducts(models.Model):
    _name = 'sale_order_simple.product_list_item'

    sale_product_list_id = fields.Many2one('sale_order_simple.sale_product_list', string='Sale Product List')
    sale_product_list_exp_id = fields.Many2one('sale_order_simple.sale_product_list', string='Sale Product List2')

    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")
    product_id = fields.Many2one('product.product', string='Product')
    uom_po_id = fields.Many2one('uom.uom', string="UM Comanda")


class ResUsers(models.Model):
    _inherit = 'res.users'

    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile', compute='_compute_profile')
    current_cash_amount = fields.Float(string='Cash', default = 0.0, tracking=True)
    amount_prev_day = fields.Float(related='profile_id.amount_prev_day')

    def _compute_profile(self):
        for user in self:
            user.profile_id = self.env['sale_order_simple.user_profile'].search([('user_id', '=', user.id)])
