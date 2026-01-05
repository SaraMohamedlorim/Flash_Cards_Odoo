import json
from odoo import models, fields, api
from odoo.exceptions import UserError
import csv
import base64
import io
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class FlashcardImportExport(models.Model):
    _name = 'flashcard.import.export'
    _description = 'Flashcards Import/Export'

    import_file = fields.Binary(string='Import File', required=True)
    filename = fields.Char(string='Filename')

    instructions = fields.Text(
        string="Instructions",
        default="CSV file should have these columns:\n- Question (required)\n- Answer (required)\n- Category (optional)\n- Level (optional: easy, medium, hard)\n- Tags (optional, comma-separated)"
    )


    
    def action_import(self):
        if not self.import_file:
            raise UserError("Please upload a CSV file first.")
        
        data = base64.b64decode(self.import_file)
        csv_data = io.StringIO(data.decode('utf-8'))
        reader = csv.DictReader(csv_data)

        for row in reader:
            question = row.get('Question')
            answer = row.get('Answer')
            if not question or not answer:
                continue
            self.env['flashcard.card'].create({
                'question': question,
                'answer': answer,
                'category_id': False,
                'level': row.get('Level', 'easy'),
                'tags': row.get('Tags', ''),
            })

        return {'type': 'ir.actions.act_window_close'}

    def export_cards_csv(self, card_ids=None):
        """تصدير البطاقات إلى CSV"""
        try:
            if card_ids:
                cards = self.env['flashcard.card'].browse(card_ids)
            else:
                cards = self.env['flashcard.card'].search([])
            
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            
            # كتابة العنوان
            writer.writerow([
                'Question', 'Answer', 'Category', 'Level', 
                'Tags', 'Review Count', 'Correct Count', 'Success Rate'
            ])
            
            # كتابة البيانات
            for card in cards:
                tags = ', '.join(card.tag_ids.mapped('name'))
                writer.writerow([
                    card.name or '',
                    card.answer or '',
                    card.category_id.name if card.category_id else '',
                    card.level or '',
                    tags,
                    card.review_count,
                    card.correct_count,
                    card.success_rate
                ])
            
            csv_data = output.getvalue()
            output.close()
            
            # إنشاء سجل تصدير
            export_record = self.env['flashcard.export.history'].create({
                'filename':'flashcards_export_{0}.csv'.format(fields.Datetime.now().strftime("%Y%m%d_%H%M%S")),
                'export_date': fields.Datetime.now(),
                'card_count': len(cards),
                'user_id': self.env.user.id
            })
            
            return {
                'csv_data': csv_data,
                'filename': export_record.filename,
                'export_id': export_record.id
            }
            
        except Exception as e:
            _logger.exception("Export error: {}".format(str(e)))
            raise UserError("Export failed: {}".format(str(e)))
    
    def import_cards_csv(self, file_data, filename):
        """استيراد البطاقات من CSV"""
        try:
            if len(file_data) > 5 * 1024 * 1024:  # 5 MB
             raise UserError("The file is too large (maximum 5 MB).")
            # فك تشفير الملف
            file_content = base64.b64decode(file_data).decode('utf-8')
            file_like = io.StringIO(file_content)
            
            reader = csv.DictReader(file_like)
            imported_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, 2):  # الصف 2 هو بداية البيانات
                try:
                    # البحث عن الفئة أو إنشاؤها
                    category_name = row.get('Category', '').strip()
                    category_id = False
                    if category_name:
                        category = self.env['flashcard.category'].search([
                            ('name', '=ilike', category_name)
                        ], limit=1)
                        if not category:
                            category = self.env['flashcard.category'].create({
                                'name': category_name
                            })
                        category_id = category.id
                    
                    # معالجة العلامات
                    tag_names = [tag.strip() for tag in row.get('Tags', '').split(',') if tag.strip()]
                    tag_ids = []
                    for tag_name in tag_names:
                        tag = self.env['flashcard.tag'].search([
                            ('name', '=ilike', tag_name)
                        ], limit=1)
                        if not tag:
                            tag = self.env['flashcard.tag'].create({
                                'name': tag_name
                            })
                        tag_ids.append(tag.id)
                    
                    # إنشاء البطاقة
                    card_vals = {
                        'name': row.get('Question', '').strip(),
                        'answer': row.get('Answer', '').strip(),
                        'level': row.get('Level', 'medium').strip().lower(),
                        'category_id': category_id,
                        'tag_ids': [(6, 0, tag_ids)],
                    }
                    
                    if card_vals['name'] and card_vals['answer']:
                        self.env['flashcard.card'].create(card_vals)
                        imported_count += 1
                    else:
                        error_count += 1
                        errors.append("Row {}: Missing question or answer".format(row_num))
                        
                except Exception as e:
                    error_count += 1
                    errors.append("Row {}: {}".format(row_num, str(e)))
                    _logger.error("Import error row {}: {}".format(row_num, str(e)))
            
            file_like.close()
            
            # إنشاء سجل استيراد
            import_record = self.env['flashcard.import.history'].create({
                'filename': filename,
                'import_date': fields.Datetime.now(),
                'imported_count': imported_count,
                'error_count': error_count,
                'error_details': '\n'.join(errors),
                'user_id': self.env.user.id
            })
            
            return {
                'imported_count': imported_count,
                'error_count': error_count,
                'errors': errors,
                'import_id': import_record.id
            }
            
        except Exception as e:
            _logger.exception("Import error: {}".format(str(e)))
            raise UserError("Import failed: {}".format(str(e)))
    
    def export_backup(self):
        """إنشاء نسخة احتياطية كاملة"""
        backup_data = {
            'categories': [],
            'tags': [],
            'cards': [],
            'export_date': fields.Datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # تصدير الفئات
        categories = self.env['flashcard.category'].search([])
        for category in categories:
            backup_data['categories'].append({
                'name': category.name,
                'description': category.description,
                'color': category.color
            })
        
        # تصدير العلامات
        tags = self.env['flashcard.tag'].search([])
        for tag in tags:
            backup_data['tags'].append({
                'name': tag.name,
                'color': tag.color
            })
        
        # تصدير البطاقات
        cards = self.env['flashcard.card'].search([])
        for card in cards:
            backup_data['cards'].append({
                'question': card.name,
                'answer': card.answer,
                'category': card.category_id.name if card.category_id else '',
                'level': card.level,
                'tags': [tag.name for tag in card.tag_ids],
                'review_count': card.review_count,
                'correct_count': card.correct_count,
                'success_rate': card.success_rate,
                'last_reviewed': card.last_reviewed.isoformat() if card.last_reviewed else '',
                'created_date': card.created_date.isoformat() if card.created_date else ''
            })
        
        data_str = json.dumps(backup_data, indent=4, ensure_ascii=False)
        data_b64 = base64.b64encode(data_str.encode('utf-8'))

        return {
            'file_data': data_b64,
            'filename': 'flashcards_backup_{0}.json'.format(fields.Datetime.now().strftime("%Y%m%d_%H%M%S")),
            'backup_data': backup_data
        }

class FlashcardImportHistory(models.Model):
    _name = 'flashcard.import.history'
    _description = 'Flashcards Import History'
    _order = 'import_date desc' 
    
    filename = fields.Char(string='Filename', required=True, tracking=True)
    import_date = fields.Datetime(string='Import Date', default=fields.Datetime.now)
    imported_count = fields.Integer(string='Imported Cards', tracking=True)
    error_count = fields.Integer(string='Errors', tracking=True)
    error_details = fields.Text(string='Error Details')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

class FlashcardExportHistory(models.Model):
    _name = 'flashcard.export.history'
    _description = 'Flashcards Export History'
    _order = 'export_date desc'
    
    filename = fields.Char(string='Filename', required=True , tracking=True)
    export_date = fields.Datetime(string='Export Date', default=fields.Datetime.now)
    card_count = fields.Integer(string='Exported Cards', tracking=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)