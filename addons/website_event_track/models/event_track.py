# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.addons.website.models.website import slug


class EventTrackTag(models.Model):
    _name = "event.track.tag"
    _description = 'Track Tag'
    _order = 'name'

    name = fields.Char(string='Tag', translate=True)
    track_ids = fields.Many2many('event.track', string='Tracks')


class EventTrackLocation(models.Model):
    _name = "event.track.location"
    _description = 'Track Location'

    name = fields.Char(string='Room')


class EventTrack(models.Model):
    _name = "event.track"
    _description = 'Event Track'
    _order = 'priority, date'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'website.seo.metadata', 'website.published.mixin']

    name = fields.Char(string='Title', required=True, translate=True)

    user_id = fields.Many2one('res.users', string='Responsible', track_visibility='onchange', default=lambda self: self.env.uid)
    speaker_ids = fields.Many2many('res.partner', string='Speakers')
    tag_ids = fields.Many2many('event.track.tag', string='Tags')
    state = fields.Selection([
        ('draft', 'Proposal'), ('confirmed', 'Confirmed'), ('announced', 'Announced'), ('published', 'Published')],
        string='Status', default='draft', required=True, copy=False, track_visibility='onchange')
    description = fields.Html(string='Track Description', translate=True)
    date = fields.Datetime(string='Track Date')
    duration = fields.Float(digits=(16, 2), default=1.5)
    location_id = fields.Many2one('event.track.location', string='Room')
    event_id = fields.Many2one('event.event', string='Event', required=True)
    color = fields.Integer('Color Index')
    priority = fields.Selection([
        ('0', 'Low'), ('1', 'Medium'),
        ('2', 'High'), ('3', 'Highest')],
        required=True, default='1')
    image = fields.Binary(compute='_compute_image', readonly=True, store=True)

    @api.one
    @api.depends('speaker_ids.image')
    def _compute_image(self):
        if self.speaker_ids:
            self.image = self.speaker_ids[0].image
        else:
            self.image = False

    @api.model
    def create(self, vals):
        res = super(EventTrack, self).create(vals)
        res.message_subscribe(res.speaker_ids.ids)
        return res

    @api.multi
    def write(self, vals):
        res = super(EventTrack, self).write(vals)
        if vals.get('speaker_ids'):
            for track in self:
                track.message_subscribe(track.speaker_ids.ids)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ Override read_group to always display all states. """
        if groupby and groupby[0] == "state":
            # Default result structure
            # states = self._get_state_list(cr, uid, context=context)
            states = [('draft', 'Proposal'), ('confirmed', 'Confirmed'), ('announced', 'Announced'), ('published', 'Published')]
            read_group_all_states = [{
                '__context': {'group_by': groupby[1:]},
                '__domain': domain + [('state', '=', state_value)],
                'state': state_value,
                'state_count': 0,
            } for state_value, state_name in states]
            # Get standard results
            read_group_res = super(EventTrack, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby)
            # Update standard results with default results
            result = []
            for state_value, state_name in states:
                res = filter(lambda x: x['state'] == state_value, read_group_res)
                if not res:
                    res = filter(lambda x: x['state'] == state_value, read_group_all_states)
                res[0]['state'] = [state_value, state_name]
                result.append(res[0])
            return result
        else:
            return super(EventTrack, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby)

    @api.multi
    @api.depends('name')
    def _website_url(self, field_name, arg):
        res = super(EventTrack, self)._website_url(field_name, arg)
        res.update({(track.id, '/event/%s/track/%s' % (slug(track.event_id), slug(track))) for track in self})
        return res

    @api.multi
    def open_track_speakers_list(self):
        self.ensure_one()
        return {
            'name': _('Speakers'),
            'domain': [('id', 'in', self.speaker_ids.ids)],
            'view_mode': 'kanban,form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
        }


class EventSponsorsType(models.Model):
    _name = "event.sponsor.type"
    _order = "sequence"

    name = fields.Char(string='Sponsor Type', required=True, translate=True)
    sequence = fields.Integer()


class EventSponsors(models.Model):
    _name = "event.sponsor"
    _order = "sequence"

    event_id = fields.Many2one('event.event', string='Event', required=True)
    sponsor_type_id = fields.Many2one('event.sponsor.type', string='Sponsoring Type', required=True)
    partner_id = fields.Many2one('res.partner', string='Sponsor/Customer', required=True)
    url = fields.Char(string='Sponsor Website')
    sequence = fields.Integer(store=True, related='sponsor_type_id.sequence')
    image_medium = fields.Binary(string='Logo', type='binary', related='partner_id.image_medium', store=True)
