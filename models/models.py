import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        _logger.info(f'WSEM fsm creando linea')
        res = super(SaleOrderLine, self).create(vals)
        if res.product_id:
            # Buscar equipos asociados a cualquier variante del template del producto
            product_tmpl_id = res.product_id.product_tmpl_id.id
            equipments = self.env['fsm.equipment'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)])
            for equipment in equipments:
                _logger.info(f'WSEM fsm iterando equipo')
                self._add_equipment_to_fsm_order(res.order_id, equipment)
        return res

    def _add_equipment_to_fsm_order(self, sale_order, equipment):
        fsm_order = self.env['fsm.order'].search([('sale_id', '=', sale_order.id)], limit=1)
        if fsm_order:
            _logger.info(f'WSEM fsm add equip')
            fsm_order.equipment_ids |= equipment
            for child in equipment.child_ids:
                _logger.info(f'WSEM fsm add child')
                self._add_equipment_to_fsm_order(sale_order, child)
