// JavaScript للتفاعلات الديناميكية
odoo.define('Flash_Cards.flashcard_js', function (require) {
    "use strict";

    var core = require('web.core');
    var utils = require('web.utils');

    var FlashcardWidget = core.Class.extend({
        init: function (parent) {
            this.parent = parent;
            this.setupEventListeners();
        },

        setupEventListeners: function () {
            // تفعيل أزرار المراجعة
            this.setupReviewButtons();
            
            // تفعيل الرسوم البيانية
            this.setupCharts();
            
            // تفعيل التحديث التلقائي
            this.setupAutoRefresh();
        },

        setupReviewButtons: function () {
            var self = this;
            
            // زر إظهار الإجابة
            $(document).on('click', '.btn-show-answer', function () {
                var $answer = $(this).closest('.review-card').find('.review-answer');
                $answer.addClass('show');
                $(this).hide();
                
                // إظهار أزرار التقييم
                $(this).closest('.review-card').find('.btn-correct, .btn-incorrect').show();
            });

            // أزرار التقييم
            $(document).on('click', '.btn-correct, .btn-incorrect', function () {
                var isCorrect = $(this).hasClass('btn-correct');
                var cardId = $(this).closest('.review-card').data('card-id');
                self.recordAnswer(cardId, isCorrect);
            });
            
            // زر التالي
            $(document).on('click', '.btn-next', function () {
                var cardId = $(this).closest('.review-card').data('card-id');
                self.nextCard(cardId);
            });
        },

        recordAnswer: function (cardId, isCorrect) {
            var self = this;
            var $currentCard = $('.review-card[data-card-id="' + cardId + '"]');
            $currentCard.addClass('flashcard-fade-in');
            
            // إرسال البيانات إلى الخادم
            return this._rpc({
                route: '/flashcards/record_answer',
                params: {
                    'card_id': cardId,
                    'is_correct': isCorrect,
                }
            }).then(function (data) {
                if (data.next_card) {
                    self.loadNextCard(data.next_card);
                } else {
                    self.showSessionResults(data.results);
                }
            }).catch(function (error) {
                console.error('Error recording answer:', error);
            });
        },

        nextCard: function (cardId) {
            var self = this;
            
            return this._rpc({
                route: '/flashcards/next_card',
                params: {
                    'current_card_id': cardId,
                }
            }).then(function (data) {
                if (data.next_card) {
                    self.loadNextCard(data.next_card);
                } else {
                    self.showSessionResults(data.results);
                }
            });
        },

        loadNextCard: function (cardData) {
            var self = this;
            
            this.loadTemplate('Flash_Card.review_card', {card: cardData})
                .then(function (html) {
                    $('.review-card-container').html(html);
                    self.updateProgressBar(cardData.current_index, cardData.total_cards);
                })
                .catch(function (error) {
                    console.error('Error loading next card:', error);
                });
        },

        loadTemplate: function (templateName, data) {
            return this._rpc({
                route: '/web/dataset/call_kw/flashcard.card/render_template',
                params: {
                    model: 'flashcard.card',
                    method: 'render_template',
                    args: [templateName, data],
                    kwargs: {}
                }
            });
        },

        updateProgressBar: function (currentIndex, totalCards) {
            var percentage = (currentIndex / totalCards) * 100;
            $('.progress-fill').css('width', percentage + '%');
            $('.progress-info span:first').text('Card ' + currentIndex + ' of ' + totalCards);
            $('.progress-info span:last').text(Math.round(percentage) + '%');
        },

        setupCharts: function () {
            // تهيئة الرسوم البيانية إذا كانت موجودة
            if (typeof Chart !== 'undefined') {
                this.setupProgressChart();
                this.setupCategoryChart();
            }
        },

        setupProgressChart: function () {
            var ctx = document.getElementById('progressChart');
            if (ctx) {
                var self = this;
                
                // جلب بيانات التقدم من الخادم
                this._rpc({
                    route: '/flashcards/get_progress_data',
                    params: {}
                }).then(function (data) {
                    var chart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: 'Daily Reviews',
                                data: data.values,
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                tension: 0.4,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1
                                    }
                                }
                            }
                        }
                    });
                });
            }
        },

        setupCategoryChart: function () {
            var ctx = document.getElementById('categoryChart');
            if (ctx) {
                var self = this;
                
                this._rpc({
                    route: '/flashcards/get_category_stats',
                    params: {}
                }).then(function (data) {
                    var chart = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                data: data.values,
                                backgroundColor: [
                                    '#667eea', '#764ba2', '#28a745', '#ffc107', 
                                    '#dc3545', '#6f42c1', '#e83e8c', '#fd7e14'
                                ]
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            }
                        }
                    });
                });
            }
        },

        setupAutoRefresh: function () {
            var self = this;
            
            // تحديث الإحصائيات كل 30 ثانية
            setInterval(function () {
                $('.flashcard-stat-card').addClass('flashcard-pulse');
                
                // تحديث البيانات من الخادم
                self._rpc({
                    route: '/flashcards/get_dashboard_stats',
                    params: {}
                }).then(function (data) {
                    self.updateDashboardStats(data);
                });
                
                setTimeout(function () {
                    $('.flashcard-stat-card').removeClass('flashcard-pulse');
                }, 2000);
            }, 30000);
        },

        updateDashboardStats: function (stats) {
            // تحديث بطاقات الإحصائيات
            $('.flashcard-stat-card:nth-child(1) .flashcard-stat-number').text(stats.total_cards);
            $('.flashcard-stat-card:nth-child(2) .flashcard-stat-number').text(stats.reviewed_today);
            $('.flashcard-stat-card:nth-child(3) .flashcard-stat-number').text(stats.due_cards);
            $('.flashcard-stat-card:nth-child(4) .flashcard-stat-number').text(stats.avg_success_rate.toFixed(1) + '%');
        },

        showSessionResults: function (results) {
            var self = this;
            
            this.loadTemplate('Flash_Card.session_results', {results: results})
                .then(function (html) {
                    $('.review-mode-container').html(html);
                    
                    // إضافة مستمعي الأحداث للأزرار الجديدة
                    $(document).on('click', '.btn-restart-session', function () {
                        self.startNewSession();
                    });
                    
                    $(document).on('click', '.btn-back-dashboard', function () {
                        window.location.href = '/web#action=flashcard_dashboard';
                    });
                });
        },

        startNewSession: function () {
            var self = this;
            
            this._rpc({
                route: '/flashcards/start_new_session',
                params: {
                    'session_type': 'review' // أو 'quiz'
                }
            }).then(function (data) {
                if (data.success) {
                    window.location.reload();
                }
            });
        },

        getScoreClass: function (score) {
            if (score >= 80) return 'session-score-high';
            if (score >= 60) return 'session-score-medium';
            return 'session-score-low';
        }
    });

    return {
        FlashcardWidget: FlashcardWidget,
        init: function () {
            return new FlashcardWidget(this);
        }
    };
});