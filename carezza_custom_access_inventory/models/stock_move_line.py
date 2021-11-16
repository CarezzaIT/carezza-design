# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from collections import OrderedDict, defaultdict

class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'
    
    pallet_number = fields.Integer(compute='compute_lot_id', store=True, inverse='_inverse_upper')
    hides = fields.Integer(compute='compute_lot_id', store=True, inverse='_inverse_upper')
    demand_qty = fields.Float(string='Demand Qty', help='Vendor Qty')
    
    @api.depends('lot_id')
    def compute_lot_id(self):
        for record in self:
            record.pallet_number = record.lot_id.pallet_number
            record.hides = record.lot_id.hides 
            
    def _inverse_upper(self):
        for record in self:
            record.lot_id.pallet_number = record.pallet_number
            record.lot_id.hides = record.hides 
        
    def _create_and_assign_production_lot(self):
        """ Creates and assign new production lots for move lines."""
        lot_vals = []
        # It is possible to have multiple time the same lot to create & assign,
        # so we handle the case with 2 dictionaries.
        key_to_index = {}  # key to index of the lot
        key_to_mls = defaultdict(lambda: self.env['stock.move.line'])  # key to all mls
        for ml in self:
            key = (ml.company_id.id, ml.product_id.id, ml.lot_name)
            key_to_mls[key] |= ml
            if ml.tracking != 'lot' or key not in key_to_index:
                key_to_index[key] = len(lot_vals)
                lot_vals.append({
                    'company_id': ml.company_id.id,
                    'name': ml.lot_name,
                    'product_id': ml.product_id.id,
                    'supplier_id': ml.move_id.purchase_line_id.order_id.partner_id.id,
                    'po_id': ml.move_id.purchase_line_id.order_id.id
                })

        lots = self.env['stock.production.lot'].create(lot_vals)
        for key, mls in key_to_mls.items():
            mls._assign_production_lot(lots[key_to_index[key]].with_prefetch(lots._ids))  # With prefetch to reconstruct the ones broke by accessing by index

        
        
    
    
    
