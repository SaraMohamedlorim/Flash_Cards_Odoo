{
    'name': 'Flashcards Learning System',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Comprehensive flashcard learning system with review and quiz modes',
    'description': """
        Advanced flashcard system with spaced repetition, quiz mode, 
        progress tracking, and comprehensive reporting.
        
        Features:
        - Create and manage flashcards with categories and tags
        - Review mode with answer reveal
        - Quiz mode with scoring
        - Progress tracking and statistics
        - Session management
        - Import/Export capabilities
        - Dashboard with analytics
    """,
    'author': 'sara mohammed',
    'website': 'https://www.sara.com',
    'depends': ['base', 'web', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'data/category_data.xml',
        'views/flashcard_views.xml',  
        'views/tags_views.xml',
        'views/category_views.xml',
        'views/session_views.xml',
        'views/dashboard_views.xml',
        'views/import_export_views.xml',
       
    ],
    'demo': [
        'demo/flashcard_demo.xml',
        'demo/tags_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'Flash_Cards/static/src/css/flashcard.css',
            'Flash_Cards/static/src/js/flashcard.js',
        ],
        'web.assets_qweb': [
            'Flash_Cards/static/src/xml/dashboard_widget.xml',
            'Flash_Cards/static/src/xml/flashcard_templates.xml',
            'Flash_Cards/static/src/xml/templates.xml',
            'Flash_Cards/static/src/xml/website_templates.xml',

        ],
        'website.assets_editor': [
            'Flash_Card/static/src/css/flashcard.css',
        ],
    },
    'images': ['static/description/flash-cards.png'],
    'icon': '/Flash_Cards/static/description/flash-cards.png',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}