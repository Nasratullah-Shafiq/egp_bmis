class ConstructionControlLinePart(models.Model):
    _name = 'construction.control.line.part'
    _description = 'Partial Delivery of Construction Line'

    line_id = fields.Many2one('construction.control.line', string='Construction Line', required=True, ondelete='cascade')
    qty = fields.Float(string='Quantity Delivered', required=True)
    delivery_date = fields.Date(string='Delivery Date', default=fields.Date.today)
    notes = fields.Text(string='Notes')
