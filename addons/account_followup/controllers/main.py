# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2014 OpenErp S.A. (<http://odoo.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import http, addons
from openerp.http import request
from openerp.tools.safe_eval import safe_eval


class FollowupReportController(addons.account.controllers.main.FinancialReportController):

    @http.route(['/account/followup_report/all/', '/account/followup_report/all/page/<int:page>'], type='http', auth='user')
    def followup_all(self, page=1, **kw):
        uid = request.session.uid
        context_obj = request.env['account.report.context.followup']
        report_obj = request.env['account.followup.report']
        context_all_obj = request.env['account.report.context.followup.all']
        reports = []
        context_all_id = context_all_obj.sudo(uid).search([('create_uid', '=', uid)], limit=1)
        partners_data = request.env['res.partner'].get_partners_in_need_of_action()
        partners = request.env['res.partner'].browse(partners_data.keys())
        action_contexts = []
        if not context_all_id:
            context_all_id = context_all_obj.sudo(uid).create({'valuemax': len(partners)})
        if 'partner_filter' in kw:
            context_all_id.write({'partner_filter': kw['partner_filter']})
        if 'partner_done' in kw and 'partner_filter' not in kw:
            if context_all_id.partner_filter == 'action':
                context_all_id.write({'valuenow': context_all_id.valuenow + 1})
                if kw['partner_done'] == 'all':
                    partners.update_next_action()
                    context_all_id.write({'valuenow': context_all_id.valuemax})
                    partners = partners - partners
                    if 'action_partner_list' in kw:
                        action_partner_list = safe_eval('[' + kw['action_partner_list'] + ']')
                        action_contexts = request.env['account.report.context.followup'].search([('partner_id', 'in', action_partner_list)])
        if context_all_id.valuemax != context_all_id.valuenow + len(partners):
            context_all_id.write({'valuemax': context_all_id.valuenow + len(partners)})
        if context_all_id.partner_filter == 'all':
            partners = request.env['res.partner'].get_partners_with_overdue()
        for partner in partners[((page - 1) * 15):(page * 15)]:
            context_id = context_obj.sudo(uid).search([('partner_id', '=', partner.id)], limit=1)
            context_id = context_obj.with_context(lang=partner.lang).create({'partner_id': partner.id, 'level': partners_data[partner.id][0]})
            # if not context_id:
            #     context_id = context_obj.with_context(lang=partner.lang).create({'partner_id': partner.id, 'level': partners_data[partner.id][0]})
            # else:
            #     context_id.write({'level': partners_data[partner.id][0]})
            lines = report_obj.with_context(lang=partner.lang).get_lines(context_id)
            reports.append({
                'context': context_id.with_context(lang=partner.lang),
                'lines': lines,
            })
        rcontext = {
            'reports': reports,
            'report': report_obj,
            'mode': 'display',
            'page': page,
            'context_all': context_all_id,
            'just_arrived': 'partner_done' not in kw,
            'action_contexts': action_contexts,
        }
        return request.render('account.report_followup_all', rcontext)
