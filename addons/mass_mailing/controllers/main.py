
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request


class MassMailController(http.Controller):

    @http.route('/mail/track/<int:mail_id>/blank.gif', type='http', auth='none')
    def track_mail_open(self, mail_id, **post):
        """ Email tracking. """
        mail_mail_stats = request.registry.get('mail.mail.statistics')
        mail_mail_stats.set_opened(request.cr, SUPERUSER_ID, mail_mail_ids=[mail_id])
        response = werkzeug.wrappers.Response()
        response.mimetype = 'image/gif'
        response.data = 'R0lGODlhAQABAIAAANvf7wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='.decode('base64')

        return response

    @http.route(['/mail/mailing/<int:mailing_id>/unsubscribe', '/mail/mailing/<int:mailing_id>/unsubscribe/<record_ids>'], type='http', methods=['GET', 'POST'], auth='none', website=True)
    def mailing(self, mailing_id, email=None, res_id=None, ans_id=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        Mail = request.registry['mail.mail']
        MassMailing = request.registry['mail.mass_mailing']
        mailing_ids = MassMailing.exists(cr, SUPERUSER_ID, [mailing_id], context=context)
        if not mailing_ids:
            return 'KO'
        mailing = MassMailing.browse(cr, SUPERUSER_ID, mailing_ids[0], context=context)
        if mailing.mailing_model == 'mail.mass_mailing.contact':
            if not ans_id:
                values = {}
                list_ids = [l.id for l in mailing.contact_list_ids]
                record_ids = request.registry[mailing.mailing_model].search(cr, SUPERUSER_ID, [('list_id', 'in', list_ids), ('id', '=', res_id), ('email', 'ilike', email)], context=context)
                temp = {'record_ids': record_ids[0], 'mailing_id': mailing_id}
                values.update(temp)
                return request.website.render('mass_mailing.unsubscription_reason', values)
            else:
                values = {'mailing_id': mailing_id}
                txt_msg = post['unsubscription_reason']
                if txt_msg == 'Other':
                    txt_msg = post['txt_unsubscription_reason']
                values.update(post)
                request.registry[mailing.mailing_model].write(cr, SUPERUSER_ID, int(post['record_ids']), {'opt_out': True, 'reason_to_unsubscribe': txt_msg}, context=context)
                mailing_email = request.registry[mailing.mailing_model].browse(cr, SUPERUSER_ID, int(post['record_ids']), context=context)
                mail_values = {
                    'email_from': 'admin@example.com',
                    'email_to': mailing_email.email,
                    'subject': 'Mass Mailing Unsubscription',
                    'body_html': '<div class="snippet_row" style="padding:0px;width:600px;margin:auto;background-color:#fff"><table style="margin: 0" cellpadding="0" cellspacing="0"><tbody><tr><td valign="center" style="text-align:center"><a href="http://www.example.com" style="text-decoration:none"><img src="/logo.png" style="padding:10px;height:auto;max-width:600px;width:200px" alt="Your Logo"></a></td></tr></tbody></table><table><tbody><tr><td style="color:#8B8284"><p style="font-size:30px;margin-bottom:20px">You have unsubscribed from the <a href="#">[mailing list].</a></p><p>If you unsubscribed by mistake, click <a t-att-href="/website_mass_mailing/subscribe/">here.</a></p><p>We will always be pleased to see you around on <a href="http://www.example.com">Odoo.</a></p></td><td><img src="/fa_to_img/%EF%80%AA/rgb(0,0,0)/200" alt="image"></td></tr></tbody></table><table cellspacing="0" cellpadding="0" style="margin: 20px auto"><tbody><tr style="text-align:center"><td><a href="https://www.facebook.com/Odoo"><img src="/website_mail/static/src/img/theme_imgs/social_facebook.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://twitter.com/Odoo"><img src="/website_mail/static/src/img/theme_imgs/social_twitter.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://plus.google.com/+Odooapps"><img src="/website_mail/static/src/img/theme_imgs/social_googleplus.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://www.linkedin.com/company/odoo"><img src="/website_mail/static/src/img/theme_imgs/social_linkedin.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="#"><img src="/website_mail/static/src/img/theme_imgs/social_rss.png" style="height:auto;max-width:600px" alt="social icon"></a></td></tr></tbody></table></div>',
                    'notification': True,
                    'mailing_id': mailing_id
                }
                mailing_ids = Mail.create(cr, SUPERUSER_ID, mail_values, context=context)
                mail_mail_obj = Mail.browse(cr, SUPERUSER_ID, mailing_ids, context=context)
                Mail.write(cr, SUPERUSER_ID, mailing_ids, {'body_html': mail_values['body_html']}, context=context)
                Mail.send(cr, SUPERUSER_ID, mailing_ids, context=context)
                return request.website.render('mass_mailing.unsubscribe_template', values)
        else:
            values = {'mailing_id': mailing_id, 'record_ids': res_id}
            email_fname = None
            model = request.registry[mailing.mailing_model]
            if 'email_from' in model._fields:
                email_fname = 'email_from'
            elif 'email' in model._fields:
                email_fname = 'email'
            if email_fname:
                record_ids = model.search(cr, SUPERUSER_ID, [('id', '=', res_id), (email_fname, 'ilike', email)], context=context)
            if 'opt_out' in model._fields:
                model.write(cr, SUPERUSER_ID, record_ids, {'opt_out': True}, context=context)
            mailing_email = request.registry[mailing.mailing_model].browse(cr, SUPERUSER_ID, int(record_ids[0]), context=context)
            mail_values = {
                'email_from': 'admin@example.com',
                'email_to': mailing_email.email,
                'subject': 'Mass Mailing Unsubscription',
                'body_html': '<div class="snippet_row" style="padding:0px;width:600px;margin:auto;background-color:#fff"><table style="margin: 0" cellpadding="0" cellspacing="0"><tbody><tr><td valign="center" style="text-align:center"><a href="http://www.example.com" style="text-decoration:none"><img src="/logo.png" style="padding:10px;height:auto;max-width:600px;width:200px" alt="Your Logo"></a></td></tr></tbody></table><table><tbody><tr><td style="color:#8B8284"><p style="font-size:30px;margin-bottom:20px">You have unsubscribed from the <a href="#">[mailing list].</a></p><p>If you unsubscribed by mistake, click <a t-att-href="/website_mass_mailing/subscribe/">here.</a></p><p>We will always be pleased to see you around on <a href="http://www.example.com">Odoo.</a></p></td><td><img src="/fa_to_img/%EF%80%AA/rgb(0,0,0)/200" alt="image"></td></tr></tbody></table><table cellspacing="0" cellpadding="0" style="margin: 20px auto"><tbody><tr style="text-align:center"><td><a href="https://www.facebook.com/Odoo"><img src="/website_mail/static/src/img/theme_imgs/social_facebook.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://twitter.com/Odoo"><img src="/website_mail/static/src/img/theme_imgs/social_twitter.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://plus.google.com/+Odooapps"><img src="/website_mail/static/src/img/theme_imgs/social_googleplus.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://www.linkedin.com/company/odoo"><img src="/website_mail/static/src/img/theme_imgs/social_linkedin.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="#"><img src="/website_mail/static/src/img/theme_imgs/social_rss.png" style="height:auto;max-width:600px" alt="social icon"></a></td></tr></tbody></table></div>',
                'notification': True,
                'mailing_id': mailing_id
            }
            mailing_ids = Mail.create(cr, SUPERUSER_ID, mail_values, context=context)
            mail_mail_obj = Mail.browse(cr, SUPERUSER_ID, mailing_ids, context=context)
            Mail.write(cr, SUPERUSER_ID, mailing_ids, {'body_html': mail_values['body_html']}, context=context)
            Mail.send(cr, SUPERUSER_ID, mailing_ids, context=context)
            return request.website.render('mass_mailing.unsubscribe_template', values)

    @http.route('/website_mass_mailing/<mailing_id>/subscribe/<record_ids>', type='http', auth='none', website=True)
    def subscribe_mail(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        Mail = request.registry['mail.mail']
        MassMailing = request.registry['mail.mass_mailing']
        mailing = MassMailing.browse(cr, SUPERUSER_ID, int(post['mailing_id']), context=context)
        model = request.registry[mailing.mailing_model]
        if 'reason_to_unsubscribe' in model._fields:
            model.write(cr, SUPERUSER_ID, int(post['record_ids']), {'opt_out': False, 'reason_to_unsubscribe': ' '}, context=context)
        else:
            model.write(cr, SUPERUSER_ID, int(post['record_ids']), {'opt_out': False}, context=context)
        mailing_email = model.browse(cr, SUPERUSER_ID, int(post['record_ids']), context=context)
        mail_values = {
            'email_from': 'admin@example.com',
            'email_to': mailing_email.email,
            'subject': 'Mass Mailing subscription',
            'body_html': '<div class="snippet_row" style="padding:0px;width:600px;margin:auto;background-color:#fff"><table style="margin: 0" cellpadding="0" cellspacing="0"><tbody><tr><td valign="center" style="text-align:center"><a href="http://www.example.com" style="text-decoration:none"><img src="/logo.png" style="padding:10px;height:auto;max-width:600px;width:200px" alt="Your Logo"></a></td></tr></tbody></table><table><tbody><tr><td style="color:#8B8284"><p style="font-size:30px;margin-bottom:20px">You have subscribed from the <a href="#">[mailing list].</a></p><p>We will always be pleased to see you around on <a href="http://www.odoo.com">Odoo.</a></p></td><td><img src="/fa_to_img/%EF%80%AA/rgb(0,0,0)/200" alt="image"></td></tr></tbody></table><table cellspacing="0" cellpadding="0" style="margin: 20px auto"><tbody><tr style="text-align:center"><td><a href="https://www.facebook.com/Odoo"><img src="/website_mail/static/src/img/theme_imgs/social_facebook.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://twitter.com/Odoo"><img src="/website_mail/static/src/img/theme_imgs/social_twitter.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://plus.google.com/+Odooapps"><img src="/website_mail/static/src/img/theme_imgs/social_googleplus.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="https://www.linkedin.com/company/odoo"><img src="/website_mail/static/src/img/theme_imgs/social_linkedin.png" style="height:auto;max-width:600px" alt="social icon"></a><a href="#"><img src="/website_mail/static/src/img/theme_imgs/social_rss.png" style="height:auto;max-width:600px" alt="social icon"></a></td></tr></tbody></table></div>',
            'notification': True,
            'mailing_id': int(post['mailing_id']),
        }
        mailing_ids = Mail.create(cr, SUPERUSER_ID, mail_values, context=context)
        mail_mail_obj = Mail.browse(cr, SUPERUSER_ID, mailing_ids, context=context)
        Mail.write(cr, SUPERUSER_ID, mailing_ids, {'body_html': mail_values['body_html']}, context=context)
        Mail.send(cr, SUPERUSER_ID, mailing_ids, context=context)
        return 'ok'

    @http.route(['/mail/mailing/unsubscribe'], type='json', auth='none', website=True)
    def unsubscribe(self, mailing_id, opt_in_ids, opt_out_ids, email):
        mailing = request.env['mail.mass_mailing'].sudo().browse(mailing_id)
        print mailing
        print email
        if mailing.exists():
            mailing.update_opt_out(mailing_id, email, opt_in_ids, False)
            mailing.update_opt_out(mailing_id, email, opt_out_ids, True) 

    @http.route('/website_mass_mailing/is_subscriber', type='json', auth="public", website=True)
    def is_subscriber(self, list_id, **post):
        cr, uid, context = request.cr, request.uid, request.context
        Contacts = request.registry['mail.mass_mailing.contact']
        Users = request.registry['res.users']

        is_subscriber = False
        email = None
        if uid != request.website.user_id.id:
            email = Users.browse(cr, SUPERUSER_ID, uid, context).email
        elif request.session.get('mass_mailing_email'):
            email = request.session['mass_mailing_email']

        if email:
            contact_ids = Contacts.search(cr, SUPERUSER_ID, [('list_id', '=', int(list_id)), ('email', '=', email), ('opt_out', '=', False)], context=context)
            is_subscriber = len(contact_ids) > 0

        return {'is_subscriber': is_subscriber, 'email': email}

    @http.route('/website_mass_mailing/subscribe', type='json', auth="public", website=True)
    def subscribe(self, list_id, email, **post):
        cr, uid, context = request.cr, request.uid, request.context
        Contacts = request.registry['mail.mass_mailing.contact']

        contact_ids = Contacts.search_read(cr, SUPERUSER_ID, [('list_id', '=', int(list_id)), ('email', '=', email)], ['opt_out'], context=context)
        if not contact_ids:
            Contacts.add_to_list(cr, SUPERUSER_ID, email, int(list_id), context=context)
        else:
            if contact_ids[0]['opt_out']:
                Contacts.write(cr, SUPERUSER_ID, [contact_ids[0]['id']], {'opt_out': False}, context=context)
        # add email to session
        request.session['mass_mailing_email'] = email
        return True

    @http.route('/r/<string:code>/m/<int:stat_id>', type='http', auth="none")
    def full_url_redirect(self, code, stat_id, **post):
        cr, uid, context = request.cr, request.uid, request.context
        request.registry['website.links.click'].add_click(cr, uid, code, request.httprequest.remote_addr, request.session['geoip'].get('country_code'), stat_id=stat_id, context=context)
        return werkzeug.utils.redirect(request.registry['website.links'].get_url_from_code(cr, uid, code, context=context), 301)
