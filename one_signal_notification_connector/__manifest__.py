{
    'name': 'One Signal Notification Connector',
    'version': '1.0',
    'category': 'Push Notification',
    'summary': """OneSignal connector helpful in sending push notification service for website(Desktop/Browser) & 
                mobile(Android & iOS) applications. These messages get delivered in real-time and appear in the 
                notification slider.""",
    'author': "Asiamatrix",
    'images': [
        'static/description/screen_shots.gif',
    ],
    'license': 'AGPL-3',
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/one_signal_notification_view.xml',
        'views/res_users_view.xml',
        'views/one_signal_notification_messages.xml',
        'views/one_signal_users.xml',
        'views/menu.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install':False,
}
