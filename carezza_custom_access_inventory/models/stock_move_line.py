# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from collections import OrderedDict, defaultdict

class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'
    
    pallet_number = fields.Integer(string='Pallet / Box / Roll', compute='compute_lot_id', store=True, inverse='_inverse_lot_id')
    hides = fields.Integer(compute='compute_lot_id', store=True, inverse='_inverse_lot_id')
    demand_qty = fields.Float(string='Demand Qty', help='Vendor Qty')
   
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'picking_id' in vals:
            picking = self.env['stock.picking'].browse([vals['picking_id']])
            product = self.env['product.product'].browse([vals['product_id']])
            if picking:
                if picking.picking_type_id.is_generate_lot and product.tracking == 'lot':
                    lot_name = self.env['ir.sequence'].next_by_code('lot.generation') or 'New'
                    dict = {'name': lot_name,
                            'product_id': vals['product_id'],
                            'po_id' : picking.purchase_id.id,
                            'company_id' : self.env.user.company_id.id,
#                             'pallet_number': res.
#                             'hides':
#                             'demand_qty':  
                         }
                    lot = self.env['stock.production.lot'].create(dict)
                    res.lot_id = lot.id
        return res    
    
    def write(self,vals):
        for record in self:
            res = super().write(vals)
            if 'demand_qty' in vals:
                ship_date = record.picking_id.ship_date
                record.lot_id.ship_date = ship_date
            return res
                
    @api.depends('lot_id')
    def compute_lot_id(self):
        for record in self:
            record.pallet_number = record.lot_id.pallet_number
            record.hides = record.lot_id.hides 
            
    def _inverse_lot_id(self):
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

        
        
    
    
    
