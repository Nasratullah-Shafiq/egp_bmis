{
    "name": "Building & Monitoring Integration System",
    "version": "17.0.1.0.0",
    "summary": "Building & Monitoring Integration System",
    'sequence': -100,
    'category': 'EGP',
    "description": "",
    'depends': ['base', 'mail', 'hr', 'product', 'egp_requirements', 'egp_inventory'],
    'data': [
        'security/security.xml',
        # 'data/egp_bmis_default_data.xml',
        'security/ir.model.access.csv',
        'data/egp_bmis_default_data.xml',
        'views/menu.xml',
        'views/construction_control_views.xml',

    ],
    "author": "Nasratullah Shafiq",
    "website": "https://mcit.gov.af/",
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": 'OPL-1',
}
