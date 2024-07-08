import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            if not order.commitment_date:
                raise UserError('La fecha de entrega no está definida. Por favor, defina una fecha de entrega antes de confirmar el pedido.')
            if not order.fsm_location_id:
                raise UserError('La ubicación FSM no está definida. Por favor, defina una ubicación FSM antes de confirmar el pedido.')

        res = super(SaleOrder, self).action_confirm()
        _logger.info(f'WSEM fsm action_confirm')
        
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
                            self._create_stock_request_for_equipment(fsm_order, equipment, order.commitment_date, order.fsm_location_id.id)
        return res

    def _create_stock_request_for_equipment(self, fsm_order, equipment, expected_date, location_id):
        self.env['stock.request'].create({
            'fsm_order_id': fsm_order.id,
            'product_id': equipment.product_id.id,
            'product_uom_id': equipment.product_id.uom_id.id,
            'product_uom_qty': 1,
            'state': 'draft',  # Assuming 'draft' is the initial state
            'expected_date': expected_date,
            'location_id': location_id,
            'direction': 'outbound',
            'picking_policy': 'one'
        })
        for child in equipment.child_ids:
            _logger.info(f'WSEM fsm add child')
            self._create_stock_request_for_equipment(fsm_order, child, expected_date, location_id)
