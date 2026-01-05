from odoo import models, fields, api

class SessionCardProgress(models.Model):
    _name = 'session.card.progress'
    _description = 'Card Progress in Session'
    _rec_name = 'card_id'

    session_id = fields.Many2one('flashcard.session', string='Session', required=True , index=True)
    card_id = fields.Many2one('flashcard.card', string='Card', required=True , index=True)
    user_id = fields.Many2one(
        'res.users',
        string='Reviewed By',
        default=lambda self: self.env.user
    )
    user_answer = fields.Char(string='User Answer')
    is_correct = fields.Boolean(string='Is Correct')
    response_time = fields.Float(string='Response Time (sec)')
    reviewed_at = fields.Datetime(string='Reviewed At', default=fields.Datetime.now)


    @api.model
    def create(self, vals):
        card = self.env['flashcard.card'].browse(vals.get('card_id'))
        if card and 'user_answer' in vals:
            vals['is_correct'] = (vals['user_answer'].strip().lower() == card.answer.strip().lower())
        return super(SessionCardProgress, self).create(vals)

