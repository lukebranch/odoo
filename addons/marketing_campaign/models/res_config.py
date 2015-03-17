# -*- coding: utf-8 -*-

from openerp import _, api, fields, models


class MarketingCampaignConfig(models.TransientModel):
    _name = 'marketing.config.settings'
    _inherit = 'marketing.config.settings'

    module_marketing_campaign_crm_demo = fields.Boolean(
        string='Demo data for marketing campaigns',
        help='Installs demo data like leads, campaigns and segments for Marketing Campaigns.\n'
             '-This installs the module marketing_campaign_crm_demo.')
