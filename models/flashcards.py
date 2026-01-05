from requests import request
from odoo import models, fields, api
from datetime import datetime
import random


class FlashcardCard(models.Model):
    _name = 'flashcard.card' 
    _description = 'Flashcard'
    _order = 'id desc'

    name = fields.Char(string='Question', required=True)
    answer = fields.Text(string='Answer', required=True)
    category_id = fields.Many2one('flashcard.category', string='Category')
    level = fields.Selection([
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], string='Difficulty Level', default='medium')


    recent_sessions = fields.Many2many(
    'session.card.progress',
    string='Recent Sessions',
    compute='_compute_recent_sessions',
    readonly=True
    )

    @api.depends()
    def _compute_recent_sessions(self):
        SessionProgress = self.env['session.card.progress']
        # استرجاع آخر 10 جلسات تمت مراجعتها
        recent = SessionProgress.search([], order='reviewed_at desc', limit=10)
        for record in self:
            record.recent_sessions = recent


    # @api.depends()
    # def _compute_recent_sessions(self):
    #     SessionProgress = self.env['session.card.progress']
    #     user_sessions = SessionProgress.search([
    #         ('create_uid', '=', self.env.uid)
    #     ], order='reviewed_at desc', limit=10)
    #     for record in self:
    #         record.recent_sessions = user_sessions



    # الإحصائيات والمتابعة
    review_count = fields.Integer(string='Review Count', default=0)
    correct_count = fields.Integer(string='Correct Answers', default=0)
    last_reviewed = fields.Datetime(string='Last Reviewed')
    next_review_date = fields.Date(string='Next Review')

    # معلومات إضافية
    active = fields.Boolean(default=True)
    created_date = fields.Datetime(default=fields.Datetime.now)
    created_by = fields.Many2one('res.users', default=lambda self: self.env.user)

    # علامات
    tag_ids = fields.Many2many('flashcard.tag', string='Tags')

    # معدل النجاح
    success_rate = fields.Float(string='Success Rate', compute='_compute_success_rate')


    card_count = fields.Integer(string="Total Cards", compute="_compute_stats", store=False)
    reviewed_today = fields.Integer(string="Reviewed Today", compute="_compute_stats", store=False)
    due_cards = fields.Integer(string="Due for Review", compute="_compute_stats", store=False)
    avg_success_rate = fields.Float(string="Average Success Rate", compute="_compute_stats", store=False)


    def action_start_review(self):
    
        # نبدأ جلسة مراجعة للبطاقات المختارة
        session = self.env['flashcard.session'].create({
            'name': 'Review Session - %s' % fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
            'start_time': fields.Datetime.now(),
            'session_type': 'review',
            'card_ids': [(6, 0, self.ids)],
        })
        # فتح واجهة الجلسة مباشرة
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'flashcard.session',
            'view_mode': 'form',
            'res_id': session.id,
            'target': 'current',
        }


    @api.depends()
    def _compute_stats(self):
        total_cards = self.search_count([])
        today = fields.Date.today()

        reviewed_today_count = self.search_count([('review_date', '=', today)])
        due_cards_count = self.search_count([('next_review_date', '<=', today)])
        # مثال بسيط لحساب النسبة
        success_rate = 0
        if total_cards:
            success_rate = (self.search_count([('status', '=', 'reviewed')]) / total_cards) * 100

        for rec in self:
            rec.card_count = total_cards
            rec.reviewed_today = reviewed_today_count
            rec.due_cards = due_cards_count
            rec.avg_success_rate = success_rate

    @api.depends('review_count', 'correct_count')
    def _compute_success_rate(self):
        for card in self:
            if card.review_count > 0:
                card.success_rate = (card.correct_count / card.review_count) * 100
            else:
                card.success_rate = 0.0


    def render_template(self, template_name, data):
        """تقديم قالب QWeb"""
        return request.env['ir.qweb']._render(template_name, data)
    
    def get_review_card_html(self, card):
        """الحصول على HTML لبطاقة المراجعة"""
        return self.render_template('Flash_Card.review_card', {
            'card': {
                'id': card.id,
                'name': card.name,
                'answer': card.answer,
            }
        })

    @api.model
    def render_template(self, template_name, data): 
        """تقديم قالب QWeb بالبيانات"""
        return self.env['ir.qweb']._render(template_name, data)