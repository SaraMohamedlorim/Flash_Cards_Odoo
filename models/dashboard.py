from odoo import models, fields, api
from datetime import datetime, timedelta

class FlashcardDashboard(models.Model):
    _name = 'flashcard.dashboard'
    _description = 'Flashcards Dashboard'
    _auto = False  # لا يوجد جدول فعلي في قاعدة البيانات

    # الحقول المحسوبة للوحة التحكم
    total_cards = fields.Integer(string='Total Cards', compute='_compute_dashboard_data')
    active_cards = fields.Integer(string='Active Cards', compute='_compute_dashboard_data')
    reviewed_today = fields.Integer(string='Reviewed Today', compute='_compute_dashboard_data')
    due_cards = fields.Integer(string='Due Cards', compute='_compute_dashboard_data')
    avg_success_rate = fields.Float(string='Average Success Rate', compute='_compute_dashboard_data')
    
    weekly_reviews = fields.Integer(string='Weekly Reviews', compute='_compute_dashboard_data')
    monthly_reviews = fields.Integer(string='Monthly Reviews', compute='_compute_dashboard_data')
    total_sessions = fields.Integer(string='Total Sessions', compute='_compute_dashboard_data')
    
    easy_cards = fields.Integer(string='Easy Cards', compute='_compute_dashboard_data')
    medium_cards = fields.Integer(string='Medium Cards', compute='_compute_dashboard_data')
    hard_cards = fields.Integer(string='Hard Cards', compute='_compute_dashboard_data')

    recent_sessions = fields.Many2many(
        'session.card.progress',
        string='Recent Sessions',
        compute='_compute_recent_sessions',
        readonly=True
    )


    @api.depends()
    def _compute_recent_sessions(self):
        SessionProgress = self.env['session.card.progress']
        recent = SessionProgress.search([], order='reviewed_at desc', limit=10)
        for record in self:
            record.recent_sessions = recent



    

    # ------------------------------
    #  دالة لحساب جميع البيانات
    # ------------------------------
    @api.depends()
    def _compute_dashboard_data(self):
        for rec in self:
            cards = rec.env['flashcard.card'].search([])
            sessions = rec.env['flashcard.session'].search([])
            
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # الحسابات
            reviewed_today = len([
                c for c in cards 
                if c.last_reviewed and c.last_reviewed.date() == today
            ])
            
            due_cards = len([
                c for c in cards 
                if not c.last_reviewed or (today - c.last_reviewed.date()).days > 7
            ])
            
            weekly_sessions = len([
                s for s in sessions 
                if s.create_date and s.create_date.date() >= week_ago
            ])
            
            monthly_sessions = len([
                s for s in sessions 
                if s.create_date and s.create_date.date() >= month_ago
            ])
            
            easy_cards = len([c for c in cards if c.level == 'easy'])
            medium_cards = len([c for c in cards if c.level == 'medium'])
            hard_cards = len([c for c in cards if c.level == 'hard'])
            
            avg_success = sum(c.success_rate for c in cards) / len(cards) if cards else 0
            
            # تعيين القيم
            rec.total_cards = len(cards)
            rec.active_cards = len([c for c in cards if c.active])
            rec.reviewed_today = reviewed_today
            rec.due_cards = due_cards
            rec.avg_success_rate = avg_success
            rec.weekly_reviews = weekly_sessions
            rec.monthly_reviews = monthly_sessions
            rec.total_sessions = len(sessions)
            rec.easy_cards = easy_cards
            rec.medium_cards = medium_cards
            rec.hard_cards = hard_cards


    @api.model
    def default_get(self, fields_list):
        """يملأ القيم الافتراضية للوحة التحكم"""
        defaults = super(FlashcardDashboard, self).default_get(fields_list)
        # نحسب القيم يدويًا ونرجعها كقاموس
        cards = self.env['flashcard.card'].search([])
        sessions = self.env['flashcard.session'].search([])
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        defaults.update({
            'total_cards': len(cards),
            'active_cards': len([c for c in cards if c.active]),
            'reviewed_today': len([c for c in cards if c.last_reviewed and c.last_reviewed.date() == today]),
            'due_cards': len([c for c in cards if not c.last_reviewed or (today - c.last_reviewed.date()).days > 7]),
            'avg_success_rate': sum(c.success_rate for c in cards) / len(cards) if cards else 0,
            'weekly_reviews': len([s for s in sessions if s.create_date and s.create_date.date() >= week_ago]),
            'monthly_reviews': len([s for s in sessions if s.create_date and s.create_date.date() >= month_ago]),
            'total_sessions': len(sessions),
            'easy_cards': len([c for c in cards if c.level == 'easy']),
            'medium_cards': len([c for c in cards if c.level == 'medium']),
            'hard_cards': len([c for c in cards if c.level == 'hard']),
        })
        return defaults
    # ------------------------------
    #  دوال إضافية للرسوم أو الإحصائيات التفصيلية
    # ------------------------------
    def get_category_stats(self):
        """إحصائيات الفئات"""
        categories = self.env['flashcard.category'].search([])
        stats = []
        
        for category in categories:
            category_cards = self.env['flashcard.card'].search([
                ('category_id', '=', category.id)
            ])
            
            stats.append({
                'name': category.name,
                'card_count': len(category_cards),
                'avg_success': sum(c.success_rate for c in category_cards) / len(category_cards) if category_cards else 0,
                'color': category.color or 0
            })
        
        return stats
    
    def get_weekly_progress(self):
        """تقدم الأسبوع"""
        today = datetime.now().date()
        week_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        
        progress_data = []
        for date_str in week_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            next_day = date_obj + timedelta(days=1)
            
            reviews = self.env['flashcard.card'].search_count([
                ('last_reviewed', '>=', datetime.combine(date_obj, datetime.min.time())),
                ('last_reviewed', '<', datetime.combine(next_day, datetime.min.time()))
            ])
            
            progress_data.append({
                'date': date_str,
                'reviews': reviews
            })
        
        return progress_data



    
