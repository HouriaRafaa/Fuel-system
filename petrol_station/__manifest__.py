# -*- coding: utf-8 -*-
{
    'name': "Petrol Station Management System",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'mail', 'product', 'account', 'sale_management', 'stock', 'sale_automatic_workflow'],

    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/new_data.xml',
        'views/pump.xml',
        'views/petrol_station.xml',
        'views/pump_type.xml',
        'views/res_users_inherit.xml',
        'views/daily_sales.xml',
        'views/nozzle_petrol.xml',
        'report/station_report.xml',
        'report/daily_sales_report.xml',
        # 'views/sales_register.xml',

    ],

}
