# -*- coding: utf-8 -*-
{
    'name': 'Blogs',
    'category': 'Website',
    'website': 'https://www.odoo.com/page/blog-engine',
    'summary': 'News, Blogs, Announces, Discussions',
    'version': '1.0',
    'description': """
OpenERP Blog
============

        """,
    'author': 'Odoo SA',
    'depends': ['knowledge', 'website_mail', 'website_partner'],
    'data': [
        'data/website_blog_data.xml',
        'views/website_blog_views.xml',
        'views/website_blog_templates.xml',
        'views/snippets.xml',
        'security/ir.model.access.csv',
        'security/website_blog.xml',
    ],
    'demo': [
        'data/website_blog_demo.xml'
    ],
    'test': [
        'tests/test_website_blog.yml'
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'installable': True,
    'application': True,
}
