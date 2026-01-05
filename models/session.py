from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError



class FlashcardSession(models.Model):
    _name = 'flashcard.session'
    _description = 'Flashcard Study Session'
    _order = 'create_date desc'

    name = fields.Char(string='Session Name', required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    session_type = fields.Selection([
        ('review', 'Review Mode'),
        ('quiz', 'Quiz Mode')
    ], string='Session Type', required=True)

    # إحصائيات الجلسة
    total_cards = fields.Integer(string='Total Cards')
    completed_cards = fields.Integer(string='Completed Cards')
    correct_answers = fields.Integer(string='Correct Answers')
    session_score = fields.Float(string='Session Score', compute='_compute_session_score')

    # التوقيت
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (minutes)', compute='_compute_duration')

    # البطاقات في الجلسة
    card_ids = fields.Many2many('flashcard.card', string='Cards in Session')
    current_card_index = fields.Integer(string='Current Card Index', default=0)

    # حالة الجلسة
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft')

    @api.depends('correct_answers', 'total_cards')
    def _compute_session_score(self):
        for session in self:
            if session.total_cards > 0:
                session.session_score = (session.correct_answers / session.total_cards) * 100
            else:
                session.session_score = 0.0

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for session in self:
            if session.start_time and session.end_time:
                start = fields.Datetime.from_string(session.start_time)
                end = fields.Datetime.from_string(session.end_time)
                session.duration = (end - start).total_seconds() / 60
            else:
                session.duration = 0.0
    

    def action_start_session(self):
        """بدء الجلسة"""
        self.write({
            'state': 'in_progress',
            'start_time': fields.Datetime.now()
        })
        return True

    def action_end_session(self):
        """إنهاء الجلسة"""
        self.write({
            'state': 'completed',
            'end_time': fields.Datetime.now()
        })
        return True

    def action_cancel_session(self):
        """إلغاء الجلسة"""
        self.write({
            'state': 'cancelled',
            'end_time': fields.Datetime.now()
        })
        return True

    @api.model
    def create_review_session(self):
        """إنشاء جلسة مراجعة جديدة"""
        cards = self.env['flashcard.card'].search([('active', '=', True)])
        if not cards:
            raise UserError("No active flashcards available for review.")
        
        session = self.create({
            'name': "Review Session - {}".format(fields.Datetime.now().strftime('%Y-%m-%d %H:%M')),
            'session_type': 'review',
            'card_ids': [(6, 0, cards.ids)],
            'total_cards': len(cards),
            'state': 'draft'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Review Session',
            'res_model': 'flashcard.session',
            'res_id': session.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def create_quiz_session(self, card_count=10):
        """إنشاء جلسة اختبار جديدة"""
        import random
        cards = self.env['flashcard.card'].search([('active', '=', True)])
        if not cards:
            raise UserError("No active flashcards available for quiz.")
        
        if len(cards) > card_count:
            quiz_cards = random.sample(cards.ids, card_count)
        else:
            quiz_cards = cards.ids
        
        session = self.create({
            'name': "Quiz Session - {}".format(fields.Datetime.now().strftime('%Y-%m-%d %H:%M')),
            'session_type': 'quiz',
            'card_ids': [(6, 0, quiz_cards)],
            'total_cards': len(quiz_cards),
            'state': 'draft'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quiz Session',
            'res_model': 'flashcard.session',
            'res_id': session.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    


   