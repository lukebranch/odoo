# -*- coding: utf-8 -*-

{
    'name': 'Advanced Events',
    'category': 'Website',
    'summary': 'Sponsors, Tracks, Agenda, Event News',
    'website': 'https://www.odoo.com/page/events',
    'version': '1.0',
    'description': """
Online Advanced Events
======================

Adds support for:
- sponsors
- dedicated menu per event
- news per event
- tracks
- agenda
- call for proposals
        """,
    'author': 'Odoo S.A.',
    'depends': ['website_event', 'website_blog'],
    'data': [
        'data/event_data.xml',
        'views/event_track_templates.xml',
        'views/event_track_views.xml',
        'security/ir.model.access.csv',
        'security/event_track_security.xml',
    ],
    'demo': [
        'data/event_demo.xml',
        'data/website_event_track_demo.xml'
    ],
    'installable': True,
}
