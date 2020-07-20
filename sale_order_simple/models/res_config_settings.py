# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_loss_ratio = fields.Float(string='Loss Ratio', default=0.14, config_parameter='fornetti.product_loss_ratio')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
#        self.env['ir.config_parameter'].set_param('sale.automatic_invoice', False)