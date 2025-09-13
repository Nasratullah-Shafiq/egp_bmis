"""
Author: Safiullah Arian 65605444+safiullah-arian@users.noreply.github.com
Date: 2025-07-29 11:49:27
LastEditors: Safiullah Arian 65605444+safiullah-arian@users.noreply.github.com
LastEditTime: 2025-07-29 12:08:18
FilePath: customization/egp_bmis/models/board_members.py
Description: 这是默认设置,可以在设置》工具》File Description中进行配置
"""
from odoo import models, fields, api, _

class ConstBoardMember(models.Model):
    _name = "const.board.member"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Const Board Members"

    position_title = fields.Char(string='Position', related='employee_id.job_id.name', store=True)
    phone = fields.Char(string='Phone', related='employee_id.work_phone', store=True)
    email = fields.Char(string='Email', related='employee_id.work_email', store=True)
    role = fields.Selection([('pre_offer_opening', 'Pre Offer Opening'),
                             ('offer_opening', 'Offer Opening'),
                             ('evaluation', 'Evaluation'),
                             ('ٍٍexamination', 'Delivery and Dissection'),
                             ('purchase', 'Purchase'),
                             ('complaint', 'Complaint'),
                             ('inspection ', 'Inspection'),
                             ]
                            , string='Role', required=True, tracking=True)

    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True)
    const_control_id = fields.Many2one('construction.control', string="Board Member", tracking=True)


