# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class SaleOrderWizard(models.Model):
    _name = 'sale_order_simple.wizard'

    user_id = fields.Many2one('res.users', string='User')
    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile')

    order_id = fields.Many2one('sale.order', string="Sale Order")
    partner_id = fields.Many2one(related='order_id.partner_id')
    pricelist_id = fields.Many2one(related="order_id.pricelist_id")
    company_id = fields.Many2one(related="order_id.company_id")
    state = fields.Selection(related="order_id.state")
    wiz_line = fields.One2many('sale_order_simple.wizard_line', 'wizard_id', string="Product List")
    currency_id = fields.Many2one(related='order_id.currency_id', string='Currency', readonly=True)

    amount_untaxed = fields.Monetary(string="Amount Untaxed", compute="_compute_amount_all")
    amount_tax = fields.Monetary(string="Amount Tax", compute="_compute_amount_all")
    amount_total = fields.Monetary(string="Amount Total", compute="_compute_amount_all")

    @api.depends('wiz_line.price_total')
    def _compute_amount_all(self):
         for obj in self:
            obj.amount_untaxed = sum([l.price_subtotal for l in obj.wiz_line])
            obj.amount_tax = sum([l.price_tax for l in obj.wiz_line])
            obj.amount_total = obj.amount_untaxed + obj.amount_tax

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderWizard, self).default_get(fields)
        res['user_id'] = self.env.user.id
        profile_id = self.env.user.profile_id
        if profile_id:
            res['profile_id'] = self.env.user.profile_id.id
            order_id = self.env['sale.order'].create(
                {'partner_id': profile_id.so_partner_id.id,
                 'warehouse_id': profile_id.warehouse_id.id
            })
            order_id.onchange_partner_id()

            res['order_id'] = order_id.id
            res['partner_id'] = order_id.partner_id.id
            res['pricelist_id'] = order_id.pricelist_id.id
            res['company_id'] = order_id.company_id.id
            res['state'] = order_id.state
            
            lines = []
            for product_line in self.env.user.profile_id.product_ids:
                so_line = self.env['sale.order.line'].with_context(round=True).create(
                    {
                        'name': product_line.product_id.name,
                        'order_id': order_id.id,
                        'product_id': product_line.product_id.id,
                        'product_uom_qty': 0
                    })
                so_line.product_id_change()
                wiz_line = {
                    'order_line_id': so_line.id,
                    'product_id': so_line.product_id.id,
                    'product_uom': so_line.product_uom.id,
                    'product_uom_qty': 0,
                    'price_unit': so_line.price_unit
                }
                lines.append((0, 0, wiz_line))
            res['wiz_line'] = lines

        return res

    @api.multi
    def confirm(self):
        for wizl in self.wiz_line:
            wizl.order_line_id.product_uom_qty = wizl.product_uom_qty
        self.order_id.action_confirm()
        for pick in self.order_id.picking_ids:
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, pick.id)]})
            wiz.process()

    @api.multi
    def cancel(self):
        self.order_id.unlink()


class SaleOrderWizardLine(models.Model):
    _name = 'sale_order_simple.wizard_line'

    wizard_id = fields.Many2one('sale_order_simple.wizard', string="Wizard")
    order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    currency_id = fields.Many2one(related='order_line_id.currency_id')
    product_id = fields.Many2one(related='order_line_id.product_id')
    product_uom_qty = fields.Float(string="Product Qty", default=0.0)
    product_uom = fields.Many2one(related="order_line_id.product_uom")
    price_unit = fields.Float(related='order_line_id.price_unit')
    price_total = fields.Monetary(string="Price Total", compute="_compute_price_total")
    price_subtotal = fields.Monetary(string="Price Total", compute="_compute_price_total")
    price_tax = fields.Monetary(string="Price Total", compute="_compute_price_total")

    @api.depends('product_uom_qty')
    def _compute_price_total(self):
        for line in self:
            line.order_line_id.product_uom_qty = line.product_uom_qty
            line.order_line_id._compute_amount()
            line.price_total = line.order_line_id.price_total
            line.price_subtotal = line.order_line_id.price_subtotal
            line.price_tax = line.order_line_id.price_tax
        
