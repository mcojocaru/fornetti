# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _
import json

def _round(amount):
    #return tools.float__round(amount, precision_digits=2)
    return round(amount, 2)

def _wiz_line_data(wiz_line):
    return {
        'order_line_id': wiz_line.order_line_id.id,
        'product_id': wiz_line.product_id.id,
        'product_name': wiz_line.order_line_id.name,
        'product_uom': wiz_line.product_uom.id,
        'product_uom_name': wiz_line.product_uom.name,
        'uom_po_qty_name': wiz_line.uom_po_qty_name,
        'uom_po_qty_flag': wiz_line.uom_po_qty_flag,
        'current_qty': _round(wiz_line.current_qty),
        'price_unit': wiz_line.price_unit,
        'is_section': wiz_line.is_section,
        'price_total': _round(wiz_line.price_total),
        'price_subtotal': _round(wiz_line.price_subtotal),
        'subtotal_order_lines': [(6, 0, wiz_line.subtotal_order_lines.ids)],
        'disabled': wiz_line.disabled,
    }

class PurchaseOrderWizard(models.Model):
    _name = 'sale_order_simple.purchase_wizard'

    supplier_invoice_number = fields.Char('Numar Factura Furnizor', required=True)
    user_id = fields.Many2one('res.users', string='User', default=None)
    profile_id = fields.Many2one('sale_order_simple.user_profile', string='Profile', default=None)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    partner_ids = fields.Many2many('res.partner', compute="_compute_seller_ids")

    lines_json1 = fields.Char('Json1', default='')
    lines_json2 = fields.Char('Json2', default='')
    order_id = fields.Many2one('purchase.order', string="Purchase Order", default=None)

    company_id = fields.Many2one(related="order_id.company_id", default=None)
    state = fields.Selection(related="order_id.state", default=None)
    wiz_line = fields.One2many('sale_order_simple.purchase_wizard_line', 'wizard_id', string="Product List", default=None)
    currency_id = fields.Many2one(related='order_id.currency_id', string='Currency', readonly=True, default=None)

    amount_untaxed = fields.Monetary(string="Amount Untaxed", compute="_compute_amount_all", default=0)
    amount_tax = fields.Monetary(string="Amount Tax", compute="_compute_amount_all", default=0)
    amount_total = fields.Monetary(string="Amount Total", compute="_compute_amount_all", default=0)

    qty_total_bags = fields.Float(compute='_compute_purchase_qty_bigger')
    qty_total_bax = fields.Float(compute='_compute_purchase_qty_bigger')
    qty_total_box = fields.Float(compute='_compute_purchase_qty_bigger')

    def _compute_seller_ids(self):
        self.partner_ids = self.profile_id.product_ids.mapped('product_id.seller_ids.name')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        partner_id = self.partner_id
        self.order_id.order_line.unlink()
        self.order_id.partner_id = partner_id
        self.order_id.onchange_partner_id()

        self._origin.wiz_line.unlink()
        self._origin.partner_id = partner_id
        lines = self.create_wiz_lines(self._origin)
        self.lines_json2 = json.dumps(lines)

    @api.model
    def create_wizard(self):
        res_id = self.create({'partner_id':self.env.user.profile_id.po_partner_id.id, 'supplier_invoice_number': "" })
        lines = self.create_wiz_lines(res_id)
        res_id.lines_json1 = res_id.lines_json2 = json.dumps(lines)

        form_view = self.env.ref('sale_order_simple.action_purchase_order_wizard_form')
        return {
            'name': 'Formular Intrare',
            'res_model': self._name,
            'res_id': res_id.id,
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'context': {'active_model': self._name, 'active_ids': res_id.ids, 'active_id': res_id.id},
            'target': 'new'
        }

    @api.onchange('lines_json1')
    def lines_json1_onchange(self):
        self.update_wiz_lines_from_json(self.lines_json1)
        self.lines_json2 = json.dumps([_wiz_line_data(line) for line in self.wiz_line])

    @api.depends('wiz_line.price_subtotal')
    def _compute_purchase_qty_bigger(self):
        for obj in self:
            obj.qty_total_bags = sum([l.uom_po_qty for l in obj.wiz_line.filtered(
                lambda wl: wl.is_section != True and wl.uom_po_id and wl.uom_po_id.name.startswith('Punga'))])
            obj.qty_total_bax = sum([l.uom_po_qty for l in obj.wiz_line.filtered(
                lambda wl: wl.is_section != True and wl.uom_po_id and wl.uom_po_id.name.startswith('Bax'))])
            obj.qty_total_box = sum([l.uom_po_qty for l in obj.wiz_line.filtered(
                lambda wl: wl.is_section != True and wl.uom_po_id and wl.uom_po_id.name.startswith('Cutie'))])


    @api.depends('wiz_line.price_subtotal', 'wiz_line.price_tax')
    def _compute_amount_all(self):
        for obj in self:
            obj.amount_untaxed = sum([l.price_subtotal for l in obj.wiz_line.filtered(lambda wl: wl.is_section == False)])
            obj.amount_tax = sum([l.price_tax for l in obj.wiz_line.filtered(lambda wl: wl.is_section == False)])
            obj.amount_total = obj.amount_untaxed + obj.amount_tax

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrderWizard, self).default_get(fields)
        res['user_id'] = self.env.user.id
        profile_id = self.env.user.profile_id
        if profile_id:
            res['profile_id'] = self.env.user.profile_id.id
            res['partner_id'] = profile_id.po_partner_id.id

            order_id = self.env['purchase.order'].create(
                {'partner_id': profile_id.po_partner_id.id,
            })
            order_id.onchange_partner_id()

            res['order_id'] = order_id.id
            res['company_id'] = order_id.company_id.id
            res['state'] = order_id.state
            res['partner_ids'] = [(6, 0, self.profile_id.product_ids.mapped('product_id.seller_ids.name').ids)]

        return res

    def update_wiz_lines_from_json(self, json_data):
        lines = json.loads(json_data)
        for line in lines:
            wiz_line = self.env['sale_order_simple.purchase_wizard_line'].search([('order_line_id', '=', line['order_line_id'])])
            if wiz_line:
                wiz_line.write(line)
        self.update_all()

    def update_all(self):
        lines = self.wiz_line.filtered(lambda wl: wl.is_section == False)
        lines.update_price_total()

        section_lines = self.wiz_line.filtered(lambda wl: wl.is_section == True)
        section_lines.update_section_line(lines)

    def create_wiz_lines(self, wiz_id):
        lines = []
        subtotal_po_lines = []
        for product_line in self.env.user.profile_id.product_ids.sorted(lambda l: l.sequence):
            subtotal_categ = self.env.ref('sale_order_simple.product_category_subtotal')
            po_line = self.env['purchase.order.line'].with_context(round=True).create(
                {
                    'name': product_line.product_id.name,
                    'order_id': wiz_id.order_id.id,
                    'product_id': product_line.product_id.id,
                    'product_qty': 0,
                    'product_uom': product_line.product_id.uom_id.id,
                    'display_type': 'line_section' if product_line.product_id.categ_id == subtotal_categ else False,
                    'price_unit': 0,
                    'date_planned': fields.Date.today(),
                })
            subtotal_po_lines.append(po_line.id)
            po_line.onchange_product_id()
            po_line._onchange_quantity()
            if product_line.product_id.categ_id != subtotal_categ:
                wiz_line = {
                    'wizard_id': wiz_id.id,
                    'order_line_id': po_line.id,
                    'product_id': po_line.product_id.id,
                    'product_name': po_line.product_id.name,
                    'product_uom': po_line.product_uom.id,
                    'product_uom_name': po_line.product_uom.name,
                    'uom_po_id': product_line.uom_po_id and product_line.uom_po_id.id or po_line.product_uom.id,
                    'current_qty': 0,
                    'price_unit': po_line.price_unit,
                    'is_section': False,
                    'disabled': wiz_id.partner_id not in po_line.product_id.seller_ids.mapped('name')
                }
            else:
                wiz_line = {
                    'wizard_id': wiz_id.id,
                    'order_line_id': po_line.id,
                    'product_id': po_line.product_id.id,
                    'product_name': po_line.name,
                    'product_uom': po_line.product_uom.id,
                    'product_uom_name': po_line.product_uom.name,
                    'uom_po_id': product_line.uom_po_id and product_line.uom_po.id or po_line.product_uom.id,
                    'current_qty': 0,
                    'price_unit': 0,
                    'is_section': True,
                    'subtotal_order_lines': [(6, 0, subtotal_po_lines)],
                    'disabled': True,
                }
                subtotal_po_lines = []
            self.env['sale_order_simple.purchase_wizard_line'].create(wiz_line)
            lines.append(wiz_line)
        return lines

    def confirm(self):
        self.order_id.partner_ref = self.supplier_invoice_number
        self.order_id.order_line.filtered(lambda l: l.product_qty == 0).unlink()
        self.order_id.button_confirm()
        picking_id = self.order_id.picking_ids
        for ml in picking_id.move_line_ids:
            ml.qty_done = ml.product_qty

        picking_id.with_context(
            skip_immediate=True,
            skip_backorder=True,
            picking_ids_not_to_backorder=picking_id.ids).button_validate()

        invoice = self.order_id.action_create_invoice()['res_id']
        if invoice:
            invoice = self.env['account.move'].browse(invoice)
            invoice.invoice_date = invoice.date        
            invoice.ref = self.supplier_invoice_number
            invoice.action_post()

        has_fornetti_group = self.env.user.has_group('sale_order_simple.fornetti_group')            
        if has_fornetti_group:
            self.env.user.profile_id.do_next_flow_state(action='input')

    def cancel(self):
        self.order_id.button_cancel()
        self.order_id.unlink()


class PurchaseOrderWizardLine(models.Model):
    _name = 'sale_order_simple.purchase_wizard_line'

    wizard_id = fields.Many2one('sale_order_simple.purchase_wizard', string="Wizard")
    order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")
    subtotal_order_lines = fields.Many2many(comodel_name='purchase.order.line', string='Subtotal Order_lines')
    is_section = fields.Boolean('Is Section', default=False)
    currency_id = fields.Many2one(related='order_line_id.currency_id')
    product_id = fields.Many2one(related='order_line_id.product_id')
    product_name = fields.Char('Product Name')
    current_qty = fields.Float(string="Product Qty", default=0.0)
    product_uom = fields.Many2one(related="order_line_id.product_uom")
    product_uom_name = fields.Char(related="product_uom.name")
    uom_po_id = fields.Many2one('uom.uom', string="Comanda")
    uom_po_qty = fields.Float('Cantitate Comanda', compute='_compute_uom_po_qty')
    uom_po_qty_flag = fields.Float('Difereneta Comanda', compute='_compute_uom_po_qty')
    uom_po_qty_name = fields.Char(compute='_compute_uom_po_qty')
    price_unit = fields.Float(related='order_line_id.price_unit')
    price_total = fields.Monetary(string="Price Total")
    price_subtotal = fields.Monetary(string="Price Total")
    price_tax = fields.Monetary(string="Price Total")
    disabled = fields.Boolean(default=False)

    def update_disabled(self):
        for line in self:
            line.disabled = line.wizard_id.partner_id not in line.product_id.seller_ids.mapped('name')

    def update_price_total(self):
        for line in self:
            if not line.is_section:
                line.order_line_id.product_qty = line.current_qty
                line.order_line_id._compute_amount()
                line.price_total = line.currency_id.round(line.order_line_id.price_total)
                line.price_subtotal = line.currency_id.round(line.order_line_id.price_subtotal)
                line.price_tax = line.currency_id.round(line.order_line_id.price_tax)

    @api.depends('current_qty')
    def _compute_uom_po_qty(self):
        for line in self:
            line.uom_po_qty_flag = False
            if not line.is_section:
                if line.product_id and line.uom_po_id and line.product_uom != line.uom_po_id:
                    line.uom_po_qty = _round(line.product_uom._compute_quantity(line.current_qty, line.uom_po_id, round=False))
                    line.uom_po_qty_flag = int(line.uom_po_qty) != line.uom_po_qty
                else:
                    line.uom_po_qty = _round(line.current_qty)
                line.uom_po_qty_name = f'{line.uom_po_qty} {line.uom_po_id and line.uom_po_id.name or line.product_uom.name}'
            else:
                line.uom_po_qty_name = ''

    def update_section_line(self, non_section_lines):
        for section_line in self:
            lines = non_section_lines.filtered(lambda wl: wl.order_line_id._origin in section_line.subtotal_order_lines._origin)
            section_line.current_qty = sum([l.current_qty for l in lines])
            section_line.price_subtotal = sum([l.price_total for l in lines])
            section_line.price_total = sum([l.price_total for l in lines])
            section_line.price_tax = sum([l.price_tax for l in lines])
