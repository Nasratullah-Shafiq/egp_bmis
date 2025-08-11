from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict



class ConstructionControl(models.Model):
    """
    Main model for tracking construction quality control
    and contract information sourced from the procurement system.
    """
    _name = 'construction.control'
    _description = 'Construction Quality Control'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "contract_number"

    # Link to procurement offer (contractor offer)

    contract_id = fields.Many2one(
        'proc.contract',
        string='Procurement Contract',
        tracking=True
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=False
    )

    # partner_id = fields.Many2one('res.partner', string='Contractor', tracking=True)
    contract_number = fields.Char(
        string="Contract Number",
        readonly=True
    )

    contract_date = fields.Date(
        string="Contract Signing Date",
        readonly=True
    )


    start_date = fields.Date(
        string="Contract Start Date",
        store=True,
        readonly=True
    )

    contract_end_date = fields.Date(
        string="Contract End Date",
        store=True,
        tracking=True
    )



    line_ids = fields.One2many(
        'construction.control.line',
        'construction_control_id',
        string='Construction Items',
        help='List of items being tracked for construction quality.'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True)

    description = fields.Text(
        string="Description",
        help="Detailed description of the construction project."
    )

    board_member_ids = fields.One2many(
        'const.board.member',
        'const_control_id',
        string='Board Members',
        tracking=True, ondelete='cascade',
    )

    Project_manager = fields.Many2one('hr.employee', string='Project Manager', tracking=True)


    # for the construction control status btn to see the contract of egp_procurement
    def action_view_procurement_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Procurement Contract',
            'res_model': 'proc.contract',
            'res_id': self.contract_id.id,
            'view_mode': 'form',
            'target': 'current'
        }


    def action_in_progress(self):
        self.state = 'in_progress'


    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        self.state = 'draft'

    @api.onchange('contract_id')
    def _onchange_contract_id_fill(self):
        if self.contract_id:
            self.contract_number = self.contract_id.contract_number
            self.contract_date = self.contract_id.contract_date
            self.start_date = self.contract_id.start_date
            self.contract_end_date = self.contract_id.contract_end_date
            self.Project_manager = self.contract_id.project_manager

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_("You cannot delete the record that has been done."))
            else:
                return super(ConstructionControl, self).unlink()
        return None


    # connection to inventory with bmis

    construction_quality_ids = fields.One2many(
        'quality.control', 'contract_id', string="Quality Control Records")


    def action_open_construct_quality_controls(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Construct Quality Control Records'),
            'res_model': 'quality.control',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.construction_quality_ids.ids)],
            'target': 'current',
        }

    # In `proc.contract` model inventory connection
    # quality_ids = fields.One2many(
    #     'quality.control', 'contract_id', string="Quality Control Records")

    def action_send_to_quality_control(self):
        for contract in self:
            if not contract.warehouse_id:
                raise ValidationError("Missing Warehouse on contract.")
            if not contract.contract_id or not contract.contract_id.proc_offer_id:
                raise ValidationError("Missing Vendor in the contract offer.")

            # 🚫 Block if any existing QC is still not done
            active_qc = contract.construction_quality_ids.filtered(lambda q: q.state != 'done')
            if active_qc:
                raise UserError(
                    "You already have a QC in Draft or In Progress. Please finish it before creating a new one.")

            # ✅ Build approved qty map only from passed (approved) lines
            approved_qty_map = defaultdict(float)

            for qc in contract.construction_quality_ids:
                for line in qc.line_ids:
                    if not line.product_id:
                        continue
                    key = (line.product_id.id, line.name or '', line.price_unit)
                    if line.passed:
                        approved_qty_map[key] += line.approved_qty or 0.0

            # ✅ Now build QC lines for remaining qty
            qc_lines = []

            for line in contract.line_ids:
                if not line.product_id or line.first_estimation_qty <= 0:
                    continue

                key = (line.product_id.id, line.description or '', line.price or 0.0)
                already_approved = approved_qty_map.get(key, 0.0)
                remaining_qty = line.first_estimation_qty - already_approved

                if remaining_qty > 0:
                    qc_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': remaining_qty,
                        'price_unit': line.price or 0.0,
                        'name': line.description or line.product_id.name,
                    }))

            if not qc_lines:
                raise UserError("All products in this contract are fully approved. Nothing left for QC.")

            # ✅ Create QC
            qc_vals = {
                'const_contract_id': contract.id,
                'warehouse_id': contract.warehouse_id.id,
                'partner_id': contract.contract_id.proc_offer_id.id,
                'origin': contract.contract_number or f"Contract-{contract.id}",
                'line_ids': qc_lines,
            }

            qc = self.env['quality.control'].sudo().create(qc_vals)
            contract.message_post(body=_("📦 QC created for pending/rejected products. Ref: %s" % qc.name))

        return True

    def action_open_quality_controls(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quality Control Records'),
            'res_model': 'quality.control',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.construction_quality_ids.ids)],
            'target': 'current',
        }

class ConstructionControlLine(models.Model):
    """
    Line model for construction control entries such as material tracking,
    estimation difference, and validation.
    """
    _name = 'construction.control.line'
    _description = 'Construction Quality Control Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    construction_control_id = fields.Many2one(
        'construction.control',
        string='Construction Control Reference',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        required=True,
        help="Product used or inspected in the construction project."
    )

    description = fields.Text(
        string="Description",
        help="Detailed description of the construction item."
    )

    max_qty = fields.Float(
        string="Maximum Allowed Quantity",
        tracking=True,
        help="Upper limit of quantity allowed as per contract or estimation."
    )

    unit_measure = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        tracking=True,
        help="Unit of measurement for this item."
    )

    price = fields.Float(
        string='Unit Price',
        help='Unit price of the item.'
    )



    sub_total = fields.Float(
        string='Subtotal',
        compute="_compute_sub_total",
        store=True,
        help='Auto calculated: quantity × price.'
    )

    details = fields.Text(
        string='Technical Details',
        help='Any specific technical or operational details.'
    )

    first_estimation_qty = fields.Float(
        string='Initial Estimation',
        help='First quantity estimation from the engineer/contractor.'
    )

    second_estimation_qty = fields.Float(
        string='Second Estimation',
        help='Revised quantity estimation.'
    )

    # ✅ The only field you care about for comparing
    estimation_difference = fields.Float(
        string="Estimation Difference",
        compute="_compute_difference_and_complete",
        store=True,
        help="First Estimation - Second Estimation"
    )

    # ✅ Auto-mark complete if the estimations are equal (diff = 0)
    completed = fields.Boolean(
        string="Completed",
        help="Marked True when both estimations are equal."
    )

    @api.depends('first_estimation_qty', 'price')
    def _compute_sub_total(self):
        """
        Computes subtotal = quantity × price.
        """
        for rec in self:
            rec.sub_total = rec.first_estimation_qty * rec.price if rec.first_estimation_qty and rec.price else 0.0

    @api.depends('first_estimation_qty', 'second_estimation_qty')
    def _compute_difference_and_complete(self):
        """
        Calculates numeric difference between estimations.
        Sets completed=True if difference is zero.
        """
        for rec in self:
            if rec.first_estimation_qty is not None and rec.second_estimation_qty is not None:
                # Pure numeric diff
                rec.estimation_difference = rec.first_estimation_qty - rec.second_estimation_qty

                # Completed = true if difference is zero
                rec.completed = (rec.estimation_difference == 0.0)
            else:
                rec.estimation_difference = 0.0
                rec.completed = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Auto-fill unit of measure from selected product.
        """
        for rec in self:
            if rec.product_id:
                rec.unit_measure = rec.product_id.uom_id





# contract connection

class ProcContract(models.Model):
    _name = "proc.contract"
    _description = "Procurement Contract"
