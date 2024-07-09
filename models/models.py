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
        _logger.info('WSEM fsm action_confirm')
        
        for order in self:
            fsm_order = self.env['fsm.order'].search([('sale_id', '=', order.id)], limit=1)
            if fsm_order:
                _logger.info(f'WSEM fsm orden {fsm_order.id}')
                picking = self.env['stock.picking'].search([('origin', '=', order.name)], limit=1)
                if not picking:
                    raise UserError('No se encontró un albarán asociado al pedido de venta.')
                
                location_id = picking.location_id.id
                _logger.info(f'WSEM fsm location_id {location_id}')
                
                for line in order.order_line:
                    if line.product_id:
                        # Buscar un equipo asociado a la variante del producto
                        product_tmpl_id = line.product_id.product_tmpl_id.id
                        equipment = self.env['fsm.equipment'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)], limit=1)
                        if equipment:
                            _logger.info('WSEM fsm iterando equipo principal')
                            self._create_stock_request_for_equipment(fsm_order, equipment, order.commitment_date, location_id)
                            # Crear solicitudes para equipos hijos
                            for child in equipment.child_ids:
                                _logger.info('WSEM fsm add child')
                                self._create_stock_request_for_equipment(fsm_order, child, order.commitment_date, location_id)
        return res

    def _create_stock_request_for_equipment(self, fsm_order, equipment, expected_date, location_id):
        if equipment.product_id.type == 'product':
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



