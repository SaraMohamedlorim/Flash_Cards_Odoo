from odoo import models, fields, api

class FlashcardCategory(models.Model):
    _name = 'flashcard.category'
    _description = 'Flashcard Category'
    _order = 'name'
    
    name = fields.Char(string='Category Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    card_count = fields.Integer(string='Card Count', compute='_compute_card_count')
    color = fields.Integer(string='Color Index')
    
    # إحصائيات الفئة
    total_reviews = fields.Integer(string='Total Reviews', compute='_compute_category_stats')
    avg_success_rate = fields.Float(string='Average Success Rate', compute='_compute_category_stats')
    
    @api.depends('name')
    def _compute_card_count(self):
        for category in self:
            category.card_count = self.env['flashcard.card'].search_count([
                ('category_id', '=', category.id),
                ('active', '=', True)
            ])
    
    def _compute_category_stats(self):
        for category in self:
            cards = self.env['flashcard.card'].search([
                ('category_id', '=', category.id),
                ('active', '=', True)
            ])
            
            category.total_reviews = sum(card.review_count for card in cards)
            
            if cards:
                category.avg_success_rate = sum(card.success_rate for card in cards) / len(cards)
            else:
                category.avg_success_rate = 0.0
    
    def action_view_category_cards(self):
        """عرض بطاقات الفئة"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cards - {}'.format(self.name),
            'res_model': 'flashcard.card',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id}
        }