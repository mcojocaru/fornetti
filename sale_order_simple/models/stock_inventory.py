# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, SUPERUSER_ID
from lxml import etree

class Inventory(models.Model):
    _inherit = "stock.inventory"

    diff_lines = fields.Many2many('stock.inventory.line', compute="_compute_diff_lines")

    def _compute_diff_lines(self):
        for obj in self:
            obj.diff_lines = obj.line_ids.filtered(lambda l: l.difference_qty != 0)

    def action_validate(self):
        res = super(Inventory, self).action_validate()
        has_fornetti_group = self.env.user.has_group('sale_order_simple.fornetti_group')
        if self.diff_lines and has_fornetti_group:
                self.send_email()

        if has_fornetti_group:
            self.env.user.profile_id.flow_state = 'unlocked'
        return res

    def send_email(self):
        self.ensure_one()
        template = self.env.ref('sale_order_simple.email_template_edi_inventory_notification')
        template.sudo().send_mail(self.id)

class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(InventoryLine, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                         toolbar=toolbar, submenu=submenu)
        if view_type == 'tree' and self.env.uid != SUPERUSER_ID:
            has_fornetti_group = self.env.user.has_group('sale_order_simple.fornetti_group')
            if has_fornetti_group:
                root = etree.fromstring(res['arch'])
                root.set('create', 'false')
                res['arch'] = etree.tostring(root)

        return res
