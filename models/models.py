import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        _logger.info(f'WSEM fsm action_confirm')
        for order in self:
            fsm_order = self.env['fsm.order'].search([('sale_id', '=', order.id)], limit=1)
            if fsm_order:
                _logger.info(f'WSEM fsm orden {fsm_order.id}')
                for line in order.order_line:
                    if line.product_id:
                        # Buscar equipos asociados a la variante del producto
                        equipments = self.env['fsm.equipment'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)])
                        for equipment in equipments:
                            _logger.info(f'WSEM fsm iterando equipo')
                            self._add_equipment_to_fsm_order(fsm_order, equipment)
        return res

    def _add_equipment_to_fsm_order(self, fsm_order, equipment):
        fsm_order.equipment_ids |= equipment
        for child in equipment.child_ids:
            _logger.info(f'WSEM fsm add child')
            self._add_equipment_to_fsm_order(fsm_order, child)
