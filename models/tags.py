from odoo import models, fields, api

class FlashcardTag(models.Model):
    _name = 'flashcard.tag'
    _description = 'Flashcard Tag'
    _order = 'name'
    
    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')
    card_count = fields.Integer(string='Card Count', compute='_compute_card_count')
    
    @api.depends('name')
    def _compute_card_count(self):
        for tag in self:
            tag.card_count = self.env['flashcard.card'].search_count([
                ('tag_ids', 'in', [tag.id]),
                ('active', '=', True)
            ])
    
    def action_view_tag_cards(self):
        """عرض بطاقات العلامة"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cards - {}'.format(self.name),
            'res_model': 'flashcard.card',
            'view_mode': 'tree,form',
            'domain': [('tag_ids', 'in', [self.id])],
            'context': {'default_tag_ids': [(6, 0, [self.id])]}
        }