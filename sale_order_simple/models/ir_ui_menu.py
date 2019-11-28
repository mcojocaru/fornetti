from openerp import models, api, tools


class Menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache_context('self._uid', 'debug', keys=('lang',))
    def load_menus(self, debug):
        menu_root = super(Menu, self).load_menus(1, debug)
        data_obj = self.env['ir.model.data']
        f_menu_parent = data_obj.xmlid_to_res_id('sale_order_simple.fornetti_root')
        f_menu_admin = data_obj.xmlid_to_res_id(cr, uid, 'sale_order_simple.menu_fornetti_admin')
        f_user_group_id = self.env.ref('sale_order_simple.fornetti_group')
        if f_user_group_id:
            if uid != 1 and f_user_group and uid in f_user_group.users.ids:
                children =  filter(lambda menu: menu['id'] in [f_menu_parent], menu_root['children'])
                menu_root['children'] = children
                if children:
                    children1 = filter(lambda menu: menu['id'] != f_menu_admin, children[0]['children'])
                    children[0]['children'] = children1
                    ids = [children[0]['id']] + [ch['id'] for ch in children[0]['children']]
                    menu_root['all_menu_ids'] = ids
        return menu_root
