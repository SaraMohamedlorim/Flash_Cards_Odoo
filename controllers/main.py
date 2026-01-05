from random import random
from odoo import http
from odoo.http import request
from odoo import models, fields, api
import json


class FlashcardController(http.Controller):

    @http.route('/flashcards/review', type='http', auth='user', website=True)
    def review_mode(self, category_id=None, **kwargs):
        domain = [('active', '=', True)]
        if category_id:
            domain.append(('category_id', '=', int(category_id)))

        cards = request.env['flashcard.card'].search(domain)
        if not cards:
            return request.render('flashcard_app.no_cards_template')

        # إنشاء جلسة مراجعة
        session = request.env['flashcard.session'].create({
            'name': f"Review Session - {fields.Datetime.now()}",
            'session_type': 'review',
            'card_ids': [(6, 0, cards.ids)],
            'total_cards': len(cards),
            'state': 'in_progress'
        })

        return request.render('flashcard_app.review_template', {
            'session': session,
            'current_card': cards[0] if cards else False,
            'card_index': 0,
            'total_cards': len(cards)
        })

    @http.route('/flashcards/quiz', type='http', auth='user', website=True)
    def quiz_mode(self, **kwargs):
        cards = request.env['flashcard.card'].search([('active', '=', True)])
        if not cards:
            return request.render('flashcard_app.no_cards_template')

        # اختيار بطاقات عشوائية للاختبار
        quiz_cards = random.sample(cards.ids, min(10, len(cards)))

        session = request.env['flashcard.session'].create({
            'name': f"Quiz Session - {fields.Datetime.now()}",
            'session_type': 'quiz',
            'card_ids': [(6, 0, quiz_cards)],
            'total_cards': len(quiz_cards),
            'state': 'in_progress'
        })

        return request.render('flashcard_app.quiz_template', {
            'session': session,
            'current_card': request.env['flashcard.card'].browse(quiz_cards[0]),
            'card_index': 0,
            'total_cards': len(quiz_cards)
        })

    @http.route('/flashcards/next-card', type='json', auth='user')
    def next_card(self, session_id, current_card_id, user_answer=None, is_correct=None):
        session = request.env['flashcard.session'].browse(int(session_id))
        current_card = request.env['flashcard.card'].browse(int(current_card_id))

        # تسجيل تقدم البطاقة الحالية
        if user_answer is not None:
            request.env['session.card.progress'].create({
                'session_id': session.id,
                'card_id': current_card.id,
                'user_answer': user_answer,
                'is_correct': is_correct
            })

            # تحديث إحصائيات البطاقة
            current_card.write({
                'review_count': current_card.review_count + 1,
                'correct_count': current_card.correct_count + (1 if is_correct else 0),
                'last_reviewed': fields.Datetime.now()
            })

        # الانتقال للبطاقة التالية
        session.current_card_index += 1

        if session.current_card_index >= session.total_cards:
            # إنهاء الجلسة
            session.write({
                'state': 'completed',
                'end_time': fields.Datetime.now(),
                'completed_cards': session.total_cards
            })
            return {'finished': True, 'session_id': session.id}

        next_card = session.card_ids[session.current_card_index]
        return {
            'finished': False,
            'card_id': next_card.id,
            'question': next_card.name,
            'card_index': session.current_card_index,
            'total_cards': session.total_cards
        }