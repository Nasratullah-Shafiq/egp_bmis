from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

class ConstructionControlLinePart(models.Model):
    _name = 'construction.control.line.part'
    _description = 'Partial Delivery of Construction Line'

    line_id = fields.Many2one('construction.control.line', string='Construction Line', required=True, ondelete='cascade')
    qty = fields.Float(string='Quantity Delivered', required=True)
    delivery_date = fields.Date(string='Delivery Date', default=fields.Date.today)
    notes = fields.Text(string='Notes')
    location = fields.Char(string='Location', required=True)
    unit_of_measure = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        tracking=True,
        help="Unit of measurement for this item."
    )
