# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _
import json


class SaleOrderWizard(models.Model):
    _name = 'sale_order_simple.wizard'

    user_id = fields.Many2one('res.users', string='User', default=None)
    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile', default=None)

    lines_json1 = fields.Char('Json1', default='')
    lines_json2 = fields.Char('Json2', default='')
    order_id = fields.Many2one('sale.order', string="Sale Order", default=None)
    partner_id = fields.Many2one(related='order_id.partner_id', default=None)
    pricelist_id = fields.Many2one(related="order_id.pricelist_id", default=None)
    company_id = fields.Many2one(related="order_id.company_id", default=None)
    state = fields.Selection(related="order_id.state", default=None)
    amount_prev_day = fields.Float(string='Amount Previous Day', default = 0.0)
    wiz_line = fields.One2many('sale_order_simple.wizard_line', 'wizard_id', string="Product List", default=None)
    currency_id = fields.Many2one(related='order_id.currency_id', string='Currency', readonly=True, default=None)

    amount_untaxed = fields.Monetary(string="Amount Untaxed", compute="_compute_amount_all", default=0)
    amount_tax = fields.Monetary(string="Amount Tax", compute="_compute_amount_all", default=0)
    amount_total = fields.Monetary(string="Amount Total", compute="_compute_amount_all", default=0)

    @api.model
    def create_wizard(self):
        res_id = self.create({})
        lines = self.create_wiz_lines(res_id)
        res_id.lines_json1 = res_id.lines_json2 = json.dumps(lines)

        form_view = self.env.ref('sale_order_simple.action_sale_order_wizard_form')
        return {
            'name': 'Vanzare Produse',
            'res_model': self._name,
            'res_id': res_id.id,
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    @api.onchange('lines_json1')
    def char1_inchange(self):
        print(self.lines_json1)
        self.update_wiz_lines_from_json(self.lines_json1)

        def _wiz_line_data(wiz_line):
            return {
                'order_line_id': wiz_line.order_line_id.id,
                'product_id': wiz_line.product_id.id,
                'product_name': wiz_line.product_id.name,
                'free_qty': wiz_line.product_id.free_qty,
                'sold_qty': wiz_line.sold_qty,
                'product_uom': wiz_line.product_uom.id,
                'product_uom_name': wiz_line.product_uom.name,
                'current_qty': wiz_line.current_qty,
                'price_unit': wiz_line.price_unit,
                'is_section': wiz_line.is_section,
                'price_total': wiz_line.price_total,
                'price_subtotal': wiz_line.price_subtotal,
                'subtotal_order_lines': [(6, 0, wiz_line.subtotal_order_lines.ids)],
            }
        self.lines_json2 = json.dumps([_wiz_line_data(line) for line in self.wiz_line])

    @api.depends('wiz_line.price_total')
    def _compute_amount_all(self):
         for obj in self:
            obj.amount_untaxed = sum([l.price_subtotal for l in obj.wiz_line.filtered(lambda wl: wl.is_section == False)])
            obj.amount_tax = sum([l.price_tax for l in obj.wiz_line.filtered(lambda wl: wl.is_section == False)])
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

        return res

    def update_wiz_lines_from_json(self, json_data):
        lines = json.loads(json_data)
        for line in lines:
            wiz_line = self.env['sale_order_simple.wizard_line'].search([('order_line_id', '=', line['order_line_id'])])
            if wiz_line:
                wiz_line.write(line)
        self.update_all()

    def update_all(self):
        lines = self.wiz_line.filtered(lambda wl: wl.is_section == False)
        lines.update_sold_qty()
        lines.update_price_total()

        section_lines = self.wiz_line.filtered(lambda wl: wl.is_section == True)
        section_lines.update_section_line(lines)

    def create_wiz_lines(self, wiz_id):
        lines = []
        subtotal_so_lines = []
        current_qty_section = 0
        for product_line in self.env.user.profile_id.product_ids.sorted(lambda l: l.sequence):
            subtotal_categ = self.env.ref('sale_order_simple.product_category_subtotal')
            so_line = self.env['sale.order.line'].with_context(round=True).create(
                {
                    'name': product_line.product_id.name,
                    'order_id': wiz_id.order_id.id,
                    'product_id': product_line.product_id.id,
                    'product_uom_qty': 0,
                    'display_type': 'line_section' if product_line.product_id.categ_id == subtotal_categ else False
                })
            subtotal_so_lines.append(so_line.id)
            so_line.product_id_change()
            if product_line.product_id.categ_id != subtotal_categ:
                wiz_line = {
                    'wizard_id': wiz_id.id,
                    'order_line_id': so_line.id,
                    'product_id': so_line.product_id.id,
                    'product_name': so_line.product_id.name,
                    'free_qty': product_line.product_id.free_qty,
                    'sold_qty': 0,
                    'product_uom': so_line.product_uom.id,
                    'product_uom_name': so_line.product_uom.name,
                    'current_qty': product_line.product_id.free_qty,
                    'price_unit': so_line.price_unit,
                    'is_section': False,
                }
                current_qty_section += product_line.product_id.free_qty
            else:
                wiz_line = {
                    'wizard_id': wiz_id.id,
                    'order_line_id': so_line.id,
                    'product_id': so_line.product_id.id,
                    'product_name': so_line.product_id.name,
                    'free_qty': 0,
                    'product_uom': so_line.product_uom.id,
                    'product_uom_name': so_line.product_uom.name,
                    'current_qty': current_qty_section,
                    'sold_qty': 0,
                    'price_unit': 0,
                    'is_section': True,
                    'subtotal_order_lines': [(6, 0, subtotal_so_lines)]
                }
                current_qty_section = 0
                subtotal_so_lines = []
            self.env['sale_order_simple.wizard_line'].create(wiz_line)
            lines.append(wiz_line)
        return lines

    def confirm(self):
        for wizl in self.wiz_line:
            wizl.order_line_id.product_uom_qty = wizl.free_qty - wizl.current_qty
        self.order_id.action_confirm()
        for pick in self.order_id.picking_ids:
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, pick.id)]})
            wiz.process()

    def cancel(self):
        self.order_id.unlink()

    def dummy(self):
        return {
            "type": "ir.actions.do_nothing",
        }

class SaleOrderWizardLine(models.Model):
    _name = 'sale_order_simple.wizard_line'

    wizard_id = fields.Many2one('sale_order_simple.wizard', string="Wizard")
    order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    subtotal_order_lines = fields.Many2many(comodel_name='sale.order.line', string='Subtotal Order_lines')
    is_section = fields.Boolean('Is Section', default=False)
    currency_id = fields.Many2one(related='order_line_id.currency_id')
    product_id = fields.Many2one(related='order_line_id.product_id')
    product_name = fields.Char(related='product_id.name')
    free_qty = fields.Float(related='product_id.free_qty')
    current_qty = fields.Float(string="Product Qty", default=0.0)
    sold_qty = fields.Float(string="Sold Qty")
    product_uom = fields.Many2one(related="order_line_id.product_uom")
    product_uom_name = fields.Char(related="product_uom.name")
    price_unit = fields.Float(related='order_line_id.price_unit')
    price_total = fields.Monetary(string="Price Total")
    price_subtotal = fields.Monetary(string="Price Total")
    price_tax = fields.Monetary(string="Price Total")
    update_button = fields.Boolean('Update Button')

    def update_sold_qty(self):
        for line in self:
            if not line.is_section:
                ratio = 1 - float(self.env['ir.config_parameter'].get_param('fornetti.product_loss_ratio'))
                line.sold_qty = ratio * (line.free_qty - line.current_qty)

    def update_price_total(self):
        for line in self:
            if not line.is_section:
                line.order_line_id.product_uom_qty = line.free_qty - line.current_qty
                line.order_line_id._compute_amount()
                line.price_total = line.order_line_id.price_total
                line.price_subtotal = line.order_line_id.price_subtotal
                line.price_tax = line.order_line_id.price_tax

    def update_section_line(self, non_section_lines):
        for section_line in self:
            lines = non_section_lines.filtered(lambda wl: wl.order_line_id._origin in section_line.subtotal_order_lines._origin)
            section_line.current_qty = sum([l.current_qty for l in lines])
            section_line.sold_qty = sum([l.sold_qty for l in lines])
            section_line.price_subtotal = sum([l.price_total for l in lines])
            section_line.price_total = sum([l.price_total for l in lines])
            section_line.price_tax = sum([l.price_tax for l in lines])
