import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        _logger.info(f'WSEM fsm action_confirm SR')
        for order in self:
            fsm_order = self.env['fsm.order'].search([('sale_id', '=', order.id)], limit=1)
            if fsm_order:
                _logger.info(f'WSEM fsm orden {fsm_order.id}')
                for line in order.order_line:
                    if line.product_id:
                        # Buscar equipos asociados a la variante del producto
                        product_tmpl_id = line.product_id.product_tmpl_id.id
                        equipments = self.env['fsm.equipment'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)])
                        for equipment in equipments:
                            _logger.info(f'WSEM fsm iterando equipo')
                            self._create_stock_request_for_equipment(fsm_order, equipment)
        return res

    def _create_stock_request_for_equipment(self, fsm_order, equipment):
        self.env['stock.request'].create({
            'fsm_order_id': fsm_order.id,
            'product_id': equipment.product_id.id,
            'product_uom_qty': 1,
            'state': 'draft',  # Assuming 'draft' is the initial state
        })
        for child in equipment.child_ids:
            _logger.info(f'WSEM fsm add child')
            self._create_stock_request_for_equipment(fsm_order, child)

