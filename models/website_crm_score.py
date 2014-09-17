from openerp import fields, models, api
from openerp.tools.safe_eval import safe_eval
import datetime
import logging


_logger = logging.getLogger(__name__)
evaluation_context = {
    'datetime': datetime,
    'context_today': datetime.datetime.now,
}

class website_crm_score(models.Model):
    _name = 'website.crm.score'

    @api.one
    def _count_leads(self):
        if self.id:
            self._cr.execute("""
                 SELECT COUNT(1)
                 FROM crm_lead_score_rel
                 WHERE score_id = %s
                 """, (self.id,))
            self.leads_count = self._cr.fetchone()[0]
        else:
            self.leads_count = 0

    @api.one
    @api.constrains('domain')
    def _assert_valid_domain(self):
        try:
            domain = safe_eval(self.domain, evaluation_context)
            self.env['crm.lead'].search(domain)
        except Exception as e:
            _logger.warning('Exception: %s' % (e,))
            raise Warning('The domain is incorrectly formatted')

    name = fields.Char('Name', required=True)
    value = fields.Float('Value', required=True)
    domain = fields.Char('Domain', required=True)
    running = fields.Boolean('Active', default=True)
    leads_count = fields.Integer(compute='_count_leads')

    # the default [] is needed for the function to be usable by the cron
    @api.model
    def assign_scores_to_leads(self, ids=[]):
        domain = [('running', '=', True)]
        if ids:
            domain.append(('id', 'in', ids))
        scores = self.search_read(domain=domain, fields=['domain'])
        for score in scores:
            domain = safe_eval(score['domain'], evaluation_context)
            domain.extend(['|', ('stage_id.on_change', '=', False), ('stage_id.probability', 'not in', [0, 100])])
            domain.extend([('score_ids', 'not in', [score['id']])])
            leads = self.env['crm.lead'].search(domain)

            for sub_ids in self._cr.split_for_in_conditions(leads.ids):
                self._cr.execute("""INSERT INTO crm_lead_score_rel
                                    SELECT unnest(%s), %s as score_id""",
                                (list(sub_ids), score['id']))

            # Todo: force recompute of fields that depends on score_ids
            leads.modified(['score_ids'])
            leads.recompute()
