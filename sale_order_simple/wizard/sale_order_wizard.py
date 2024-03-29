# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json

def _round(amount):
    #return tools.float__round(amount, precision_digits=2)
    return round(amount, 2)

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
    amount_prev_day = fields.Float(string='Amount Previous Day', default = 0.0, readonly=True)
    amount_today = fields.Float(string='Amount Current Day', default=0.0)
    current_cash_amount = fields.Float('Current Cash Amount', related='user_id.current_cash_amount')
    wiz_line = fields.One2many('sale_order_simple.wizard_line', 'wizard_id', string="Product List", default=None)
    currency_id = fields.Many2one(related='order_id.currency_id', string='Currency', readonly=True, default=None)

    expense_sheet_id = fields.Many2one('hr.expense.sheet', string='Expense Sheet')
    expense_ids = fields.One2many('hr.expense', related='expense_sheet_id.expense_line_ids', readonly=False)
    total_expenses = fields.Float('Total Expenses', compute="_compute_total_expenses")

    amount_sale_total = fields.Monetary(string="Amount Total", compute="_compute_amount_all", default=0)
    amount_untaxed = fields.Monetary(string="Amount Untaxed", compute="_compute_amount_all", default=0)
    amount_tax = fields.Monetary(string="Amount Tax", compute="_compute_amount_all", default=0)
    amount_total = fields.Monetary(string="Amount Total", compute="_compute_amount_all", default=0)

    @api.depends('expense_ids.unit_amount')
    def _compute_total_expenses(self):
        for exp_line in self.expense_ids:
            if exp_line.unit_amount > 0:
                exp_line._origin.unit_amount = exp_line.unit_amount
        self.expense_ids._compute_amount()
        self.expense_sheet_id._compute_amount()
        self.total_expenses = self.expense_sheet_id.total_amount

    @api.depends('wiz_line.price_subtotal', 'total_expenses', 'amount_today')
    def _compute_amount_all(self):
        self.order_id._amount_all()
        self.amount_total = self.current_cash_amount + self.order_id.amount_total + self.amount_prev_day \
                            - self.amount_today - self.expense_sheet_id.total_amount
        self.amount_sale_total = _round(sum([sl.price_total for sl in self.order_id.order_line.filtered(
            lambda l: l.product_id in self.profile_id.product_ids.mapped('product_id'))]))

    @api.model
    def create_wizard(self):
        res_id = self.create({})
        lines = self.create_wiz_lines(res_id)
        res_id.lines_json1 = res_id.lines_json2 = json.dumps(lines)

        exp_lines = self.create_wiz_expense_lines(res_id)

        form_view = self.env.ref('sale_order_simple.action_sale_order_wizard_form')
        return {
            'name': 'Vanzare Produse',
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

        def _wiz_line_data(wiz_line):
            return {
                'order_line_id': wiz_line.order_line_id.id,
                'product_id': wiz_line.product_id.id,
                'product_name': wiz_line.order_line_id.name,
                'qty_available': wiz_line.product_id.qty_available,
                'sold_qty': _round(wiz_line.sold_qty),
                'sold_qty_adjusted': _round(wiz_line.sold_qty_adjusted),
                'product_uom': wiz_line.product_uom.id,
                'product_uom_name': wiz_line.product_uom.name,
                'current_qty': wiz_line.current_qty,
                'price_unit': wiz_line.price_unit_initial,
                'is_section': wiz_line.is_section,
                'price_total': _round(wiz_line.price_total),
                'price_subtotal': _round(wiz_line.price_subtotal),
                'subtotal_order_lines': [(6, 0, wiz_line.subtotal_order_lines.ids)],
            }
        self.lines_json2 = json.dumps([_wiz_line_data(line) for line in self.wiz_line])

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
            order_id.pricelist_id = profile_id.warehouse_id.sale_pricelist_id
            order_id._onchange_pricelist_id()

            res['order_id'] = order_id.id
            res['partner_id'] = order_id.partner_id.id
            res['pricelist_id'] = order_id.pricelist_id.id
            res['company_id'] = order_id.company_id.id
            res['state'] = order_id.state
            res['amount_prev_day'] = self.env.user.amount_prev_day

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
        lines.update_price_total()

        section_lines = self.wiz_line.filtered(lambda wl: wl.is_section == True)
        section_lines.update_section_line(lines)

    def create_wiz_expense_lines(self, wiz_id):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if not employee_id:
            raise Exception(f"Nu exista configurat angajat pentru {self.env.user.name}")

        wiz_id.expense_sheet_id = self.env['hr.expense.sheet'].create({
            'name': f'Cheltuieli pentru {self.user_id.name}',
            'employee_id': employee_id.id,
        })
        for product_line in self.env.user.profile_id.expense_product_ids.sorted(lambda l: l.sequence):
            expense_line = self.env['hr.expense'].create({
                'name': product_line.product_id.name,
                'employee_id': employee_id.id,
                'product_id': product_line.product_id.id,
                'unit_amount': 0,
                'quantity': 1,
                'tax_ids': [(6, 0, [])],
                'sheet_id': wiz_id.expense_sheet_id.id,
                'payment_mode': 'company_account',
                'company_id': wiz_id.company_id.id,
            })
            expense_line._onchange_product_id_date_account_id()
            expense_line.unit_amount = 0

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
                    'qty_available': product_line.product_id.qty_available,
                    'sold_qty': 0,
                    'sold_qty_adjusted': 0,
                    'product_uom': so_line.product_uom.id,
                    'product_uom_name': so_line.product_uom.name,
                    'current_qty': product_line.product_id.qty_available,
                    'price_unit': so_line.price_unit,
                    'price_unit_initial': so_line.price_unit,
                    'is_section': False,
                }
                current_qty_section += product_line.product_id.qty_available
            else:
                wiz_line = {
                    'wizard_id': wiz_id.id,
                    'order_line_id': so_line.id,
                    'product_id': so_line.product_id.id,
                    'product_name': so_line.name,
                    'qty_available': 0,
                    'product_uom': so_line.product_uom.id,
                    'product_uom_name': so_line.product_uom.name,
                    'current_qty': current_qty_section,
                    'sold_qty': 0,
                    'sold_qty_adjusted': 0,
                    'price_unit': 0,
                    'price_unit_initial': 0,
                    'is_section': True,
                    'subtotal_order_lines': [(6, 0, subtotal_so_lines)]
                }
                current_qty_section = 0
                subtotal_so_lines = []
            self.env['sale_order_simple.wizard_line'].create(wiz_line)
            lines.append(wiz_line)
        return lines

    def confirm(self):
        # for line in self.wiz_line:
        #     qty = line.free_qty - line.current_qty
        #     if line.product_uom != self.env.ref('uom.product_uom_unit') and qty > 0:
        #         bom_id = self._create_bom(line)
        #         unbild = self.env['mrp.unbuild'].create({
        #             'product_id': line.product_id.id,
        #             'product_uom_id': line.product_uom.id,
        #             'location_id': self.env.ref('stock.stock_location_stock').id,
        #             'location_dest_id': self.env.ref('stock.stock_location_stock').id,
        #             'bom_id': bom_id.id,
        #             'product_qty': qty
        #         })
        #         unbild.sudo().action_validate()
        self.expense_ids.filtered(lambda exp: exp.unit_amount == 0).unlink()
        if self.expense_ids.exists():
            self.expense_sheet_id.action_submit_sheet()
            self.expense_sheet_id.approve_expense_sheets()
            self.expense_sheet_id.action_sheet_move_create()
        else:
            self.expense_sheet_id.unlink()

        sold_lines =  self.order_id.order_line.filtered(lambda l: l.product_uom_qty > 0)
        so_line = self.env['sale.order.line'].with_context(round=True).create(
            {
                'name': self.env.ref('sale_order_simple.product_amount_prev_date').name,
                'order_id': self.order_id.id,
                'product_id': self.env.ref('sale_order_simple.product_amount_prev_date').id,
                'product_uom_qty': 1,
                'price_unit': self.amount_prev_day
            })
        so_line.tax_id = [(6, 0, [])]

        so_line = self.env['sale.order.line'].with_context(round=True).create(
            {
                'name': self.env.ref('sale_order_simple.product_amount_baked_today').name,
                'order_id': self.order_id.id,
                'product_id': self.env.ref('sale_order_simple.product_amount_baked_today').id,
                'product_uom_qty': -1,
                'price_unit': self.amount_today
            })
        so_line.tax_id = [(6, 0, [])]

        self.order_id.with_context(active_id=self.id, active_model='sale.order').action_confirm()
        if sold_lines:
            self.order_id.picking_ids.action_assign()
        for pick in self.order_id.picking_ids:
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, pick.id)]})
            wiz.process()
        self.user_id.current_cash_amount = self.amount_total
        self.profile_id.company_id.amount_prev_day = self.amount_today

        invoice = self.order_id._create_invoices()
        if invoice:
            invoice[0].with_context(active_ids=[invoice[0].id],active_model='account.move', active_id=invoice[0].id).action_post()
            if invoice[0].is_inbound():
                domain = [('payment_type', '=', 'inbound')]
            else:
                domain = [('payment_type', '=', 'outbound')]

            pm_id = self.env['account.payment.method'].search(domain, limit=1)
            journal_id = self.env['account.journal'].search(
                [('company_id', '=', invoice[0].company_id.id), ('type', '=', 'cash')], limit=1)

            payment = self.env['account.payment'].with_context(active_ids=[invoice[0].id], active_model='account.move',
                                                               active_id=self.id).create(
                {'journal_id': journal_id.id, 'payment_method_id': pm_id.id, 'payment_type': 'inbound'})
            payment.action_post()

        has_fornetti_group = self.env.user.has_group('sale_order_simple.fornetti_group')
        if has_fornetti_group:
            self.env.user.profile_id.do_next_flow_state(action='output')

    def cancel(self):
        self.order_id.unlink()
        self.expense_sheet_id.unlink()

    def dummy(self):
        return {
            "type": "ir.actions.do_nothing",
        }

    # def _create_bom(self, line):
    #     bom = {
    #         'product_tmpl_id': line.product_id.product_tmpl_id.id,
    #         'product_uom_id': line.product_uom.id,
    #         'type': 'normal',
    #         'product_qty': 1
    #     }
    #     bom_id = self.env['mrp.bom'].create(bom)
    #     ratio = 1 - float(self.env['ir.config_parameter'].get_param('fornetti.product_loss_ratio'))
    #     bom_line1 = {
    #         'product_id': line.product_id.id,
    #         'product_qty': ratio,
    #         'product_uom_id': line.product_uom.id,
    #         'bom_id': bom_id.id
    #     }
    #     self.env['mrp.bom.line'].create(bom_line1)
    #     prod_loss = self.env.ref('sale_order_simple.product_fornetti_loss')
    #     bom_line2 = {
    #         'product_id': prod_loss.id,
    #         'product_qty': 1 - ratio,
    #         'product_uom_id': prod_loss.uom_id.id,
    #         'bom_id': bom_id.id
    #     }
    #     self.env['mrp.bom.line'].create(bom_line2)
    #
    #     return bom_id


class SaleOrderWizardLine(models.Model):
    _name = 'sale_order_simple.wizard_line'

    wizard_id = fields.Many2one('sale_order_simple.wizard', string="Wizard")
    order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    subtotal_order_lines = fields.Many2many(comodel_name='sale.order.line', string='Subtotal Order_lines')
    is_section = fields.Boolean('Is Section', default=False)
    currency_id = fields.Many2one(related='order_line_id.currency_id')
    product_id = fields.Many2one(related='order_line_id.product_id')
    product_name = fields.Char('Product Name')
    qty_available = fields.Float(related='product_id.qty_available')
    current_qty = fields.Float(string="Product Qty", default=0.0)
    sold_qty = fields.Float(string="Sold Qty", compute='update_sold_qty')
    sold_qty_adjusted = fields.Float(string="Sold Qty Adjusted", compute='update_sold_qty')
    product_uom = fields.Many2one(related="order_line_id.product_uom")
    product_uom_name = fields.Char(related="product_uom.name")
    price_unit = fields.Float(related='order_line_id.price_unit')
    price_unit_initial = fields.Float('Price Unit Initial')
    price_total = fields.Monetary(string="Price Total")
    price_subtotal = fields.Monetary(string="Price Total")
    price_tax = fields.Monetary(string="Price Total")

    @api.depends('current_qty')
    def update_sold_qty(self):
        ratio = 1 - float(self.env['ir.config_parameter'].sudo().get_param('fornetti.product_loss_ratio'))
        for line in self:
            if not (line.is_section or line.product_uom == self.env.ref('uom.product_uom_unit')):
                line.sold_qty_adjusted =  _round(ratio * (line.qty_available - line.current_qty))
            else:
                line.sold_qty_adjusted = _round(line.qty_available - line.current_qty)
            line.sold_qty = _round(line.qty_available - line.current_qty)

    def update_price_total(self):
        for line in self:
            if not line.is_section:
                ratio = 1 - float(self.env['ir.config_parameter'].sudo().get_param('fornetti.product_loss_ratio'))
                price_unit = self.env['account.tax']._fix_tax_included_price_company(
                    line.order_line_id._get_display_price(line.product_id), line.product_id.taxes_id,
                    line.order_line_id.tax_id, line.order_line_id.company_id)
                if line.product_uom != self.env.ref('uom.product_uom_unit'):
                    line.order_line_id.price_unit = ratio * price_unit
                line.order_line_id.product_uom_qty = line.qty_available - line.current_qty
                line.order_line_id._compute_amount()
                line.price_total = _round(line.order_line_id.price_total)
                line.price_subtotal = _round(line.order_line_id.price_subtotal)
                line.price_tax = _round(line.order_line_id.price_tax)

    def update_section_line(self, non_section_lines):
        for section_line in self:
            lines = non_section_lines.filtered(lambda wl: wl.order_line_id._origin in section_line.subtotal_order_lines._origin)
            section_line.current_qty = sum([l.current_qty for l in lines])
            section_line.sold_qty = sum([l.sold_qty for l in lines])
            section_line.sold_qty_adjusted = _round(sum([l.sold_qty_adjusted for l in lines]))
            section_line.price_subtotal = _round(sum([l.price_total for l in lines]))
            section_line.price_total = _round(sum([l.price_total for l in lines]))
            section_line.price_tax = _round(sum([l.price_tax for l in lines]))


# class SaleOrderWizardExpLine(models.Model):
#     _name = 'sale_order_simple.wizard_line_expense'
#
#     wizard_id = fields.Many2one('sale_order_simple.wizard', string="Wizard")
#     product_id = fields.Many2one('product.product', string='Prodduct')
#     order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
#     currency_id = fields.Many2one(related='order_line_id.currency_id')
#     amount = fields.Float(string="Amount", default=0.0)
#
#     price_total = fields.Monetary(string="Price Total")
#     price_subtotal = fields.Monetary(string="Price Total")
#     price_tax = fields.Monetary(string="Price Total")
#
#     @api.onchange('amount')
#     def update_price_total(self):
#         for line in self:
#             line.order_line_id.write({'price_unit': -line.amount})
#             line.order_line_id._compute_amount()
#             line.price_total = line.order_line_id.price_total
#             line.price_subtotal = line.order_line_id.price_subtotal
#             line.price_tax = line.order_line_id.price_tax