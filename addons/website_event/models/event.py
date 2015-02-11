# -*- coding: utf-8 -*-

import re

from openerp import api, fields, models, _
from openerp.addons.website.models.website import slug


class Event(models.Model):
    _name = 'event.event'
    _inherit = ['event.event', 'website.seo.metadata', 'website.published.mixin']

    def _default_hashtag(self):
        return re.sub("[- \\.\\(\\)\\@\\#\\&]+", "", self.env.user.company_id.name).lower()

    twitter_hashtag = fields.Char(string='Twitter Hashtag', default=_default_hashtag)
    website_published = fields.Boolean(track_visibility='onchange')
    # TDE TODO FIXME: when website_mail/mail_thread.py inheritance work -> this field won't be necessary
    website_message_ids = fields.One2many(
        'mail.message', 'res_id',
        domain=lambda self: [
            '&', ('model', '=', self._name), ('type', '=', 'comment')
        ],
        string='Website Messages',
        help="Website communication history",
    )
    show_menu = fields.Boolean(string='Dedicated Menu', compute='_get_show_menu', inverse='_set_show_menu')
    menu_id = fields.Many2one('website.menu', string='Event Menu')

    @api.one
    def _get_new_menu_pages(self):
        todo = [
            (_('Introduction'), 'website_event.template_intro'),
            (_('Location'), 'website_event.template_location')
        ]
        result = []
        for name, path in todo:
            complete_name = name + ' ' + self.name
            newpath = self.env['website'].new_page(complete_name, path, ispage=False)
            url = "/event/" + slug(self) + "/page/" + newpath
            result.append((name, url))
        result.append((_('Register'), '/event/%s/register' % slug(self)))
        return result

    @api.one
    def _set_show_menu(self):
        if self.menu_id and not self.show_menu:
            self.menu_id.unlink()
        elif self.show_menu and not self.menu_id:
            root_menu = self.env['website.menu'].create({'name': self.name})
            to_create_menus = self._get_new_menu_pages()[0]
            seq = 0
            for name, url in to_create_menus:
                self.env['website.menu'].create({
                    'name': name,
                    'url': url,
                    'parent_id': root_menu.id,
                    'sequence': seq,
                })
                seq += 1
            self.menu_id = root_menu

    @api.one
    def _get_show_menu(self):
        self.show_menu = bool(self.menu_id)

    @api.multi
    @api.depends('name')
    def _website_url(self, name, arg):
        res = super(Event, self)._website_url(name, arg)
        res.update({(e.id, '/event/%s' % slug(e)) for e in self})
        return res

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'website_published' in init_values and self.website_published:
            return 'website_event.mt_event_published'
        elif 'website_published' in init_values and not self.website_published:
            return 'website_event.mt_event_unpublished'
        return super(Event, self)._track_subtype(init_values)
