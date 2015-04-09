# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.addons.website.models.website import slug


class Event(models.Model):
    _inherit = "event.event"

    track_ids = fields.One2many('event.track', 'event_id', string='Tracks')
    sponsor_ids = fields.One2many('event.sponsor', 'event_id', string='Sponsors')
    blog_id = fields.Many2one('blog.blog', string='Event Blog')
    show_track_proposal = fields.Boolean(string='Talks Proposals')
    show_tracks = fields.Boolean(string='Multiple Tracks')
    show_blog = fields.Boolean(string='News')
    count_tracks = fields.Integer(string='Tracks', compute='_count_tracks')
    allowed_track_tag_ids = fields.Many2many('event.track.tag', relation='event_allowed_track_tags_rel', string='Available Track Tags')
    tracks_tag_ids = fields.Many2many('event.track.tag', relation='event_track_tags_rel', string='Track Tags', compute='_get_tracks_tag_ids', store=True)
    count_sponsor = fields.Integer(string='# Sponsors', compute='_count_sponsor')

    @api.one
    def _count_tracks(self):
        self.count_tracks = len(self.track_ids)

    @api.one
    def _count_sponsor(self):
        self.count_sponsor = len(self.sponsor_ids)

    @api.one
    @api.depends('track_ids.tag_ids')
    def _get_tracks_tag_ids(self):
        self.tracks_tag_ids = self.track_ids.mapped('tag_ids').ids

    @api.one
    def _get_new_menu_pages(self):
        result = super(Event, self)._get_new_menu_pages()[0]  # TDE CHECK api.one -> returns a list with one item ?
        if self.show_tracks:
            result.append((_('Talks'), '/event/%s/track' % slug(self)))
            result.append((_('Agenda'), '/event/%s/agenda' % slug(self)))
        if self.blog_id:
            result.append((_('News'), '/blogpost'+slug(self.blog_ig)))
        if self.show_track_proposal:
            result.append((_('Talk Proposals'), '/event/%s/track_proposal' % slug(self)))
        return result

