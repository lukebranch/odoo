# -*- coding: utf-8 -*-

from openerp import tools
from openerp import _, api, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp


class CampaignAnalysis(models.Model):
    _name = "campaign.analysis"
    _description = "Campaign Analysis"
    _auto = False
    _rec_name = 'date'

    def _total_cost(self, field_name, arg):
        """
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of case and section Data’s IDs
            @param context: A standard dictionary for contextual values
        """
        result = {}
        for ca_obj in self:
            wi_ids = self.env['marketing.campaign.workitem'].search(
                [('segment_id.campaign_id', '=', ca_obj.campaign_id.id)])
            total_cost = ca_obj.activity_id.variable_cost + \
                ((ca_obj.campaign_id.fixed_cost or 1.00) / len(wi_ids))
            result[ca_obj.id] = total_cost
        return result
    res_id = fields.Integer(string='Resource', readonly=True)
    year = fields.Char(string='Execution Year', size=4, readonly=True)
    month = fields.Selection([('01', 'January'), ('02', 'February'),
                              ('03', 'March'), ('04', 'April'), ('05',
                                                                 'May'), ('06', 'June'),
                              ('07', 'July'), ('08',
                                               'August'), ('09', 'September'),
                              ('10', 'October'), ('11', 'November'), ('12', 'December')],
                             'Execution Month', readonly=True)
    day = fields.Char(string='Execution Day', size=10, readonly=True)
    date = fields.Date(string='Execution Date', readonly=True, select=True)
    campaign_id = fields.Many2one(
        comodel_name='marketing.campaign', string='Campaign', readonly=True)
    activity_id = fields.Many2one(comodel_name='marketing.campaign.activity', string='Activity',
                                  readonly=True)
    segment_id = fields.Many2one(comodel_name='marketing.campaign.segment', string='Segment',
                                 readonly=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', readonly=True)
    country_id = fields.Many2one(
        related='partner_id.country_id', relation='res.country', string='Country')
    total_cost = fields.Float(
        compute='_total_cost', string='Cost', digits_compute=dp.get_precision('Account'))
    revenue = fields.Float(
        string='Revenue', readonly=True, digits_compute=dp.get_precision('Account'))
    count = fields.Integer(string='# of Actions', readonly=True)
    state = fields.Selection([('todo', 'To Do'),
                              ('exception',
                               'Exception'), ('done', 'Done'),
                              ('cancelled', 'Cancelled')], 'Status', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'campaign_analysis')
        cr.execute("""
            create or replace view campaign_analysis as (
            select
                min(wi.id) as id,
                min(wi.res_id) as res_id,
                to_char(wi.date::date, 'YYYY') as year,
                to_char(wi.date::date, 'MM') as month,
                to_char(wi.date::date, 'YYYY-MM-DD') as day,
                wi.date::date as date,
                s.campaign_id as campaign_id,
                wi.activity_id as activity_id,
                wi.segment_id as segment_id,
                wi.partner_id as partner_id ,
                wi.state as state,
                sum(act.revenue) as revenue,
                count(*) as count
            from
                marketing_campaign_workitem wi
                left join res_partner p on (p.id=wi.partner_id)
                left join marketing_campaign_segment s on (s.id=wi.segment_id)
                left join marketing_campaign_activity act on (act.id= wi.activity_id)
            group by
                s.campaign_id,wi.activity_id,wi.segment_id,wi.partner_id,wi.state,
                wi.date::date
            )
        """)
