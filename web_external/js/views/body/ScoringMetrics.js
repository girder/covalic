covalic.views.ScoringMetricsView = covalic.View.extend({

    events: {
        'click .c-add-metric': function () {
            if (!this.addMetricWidget) {
                this.addMetricWidget = new covalic.views.AddMetricWidget({
                    el: $('#g-dialog-container'),
                    phase: this.model,
                    parentView: this
                }).on('g:saved', function (metric) {
                    if (!this.model.has('metrics') || !this.model.get('metrics')) {
                        this.model.set('metrics', {});
                    }
                    this.model.get('metrics')[metric.id] = {
                        title: '',
                        weight: 0,
                        description: ''
                    };
                    this.render();
                }, this);
            }
            this.addMetricWidget.render();
        },

        'click .c-save-metrics': function () {
            this.$('.g-validation-failed-message').empty();
            var metrics = {};
            _.each(this.$('.c-metric-container'), function (el) {
                el = $(el);
                var idInput = el.find('.c-metric-id');
                var metricId = idInput.val().trim();
                if (!metricId) {
                    this.$('.g-validation-failed-message').text(
                        'Metric identifier field must not be empty.');
                    idInput.focus();
                    return;
                }
                if (_.has(metrics, metricId)) {
                    this.$('.g-validation-failed-message').text(
                        'Duplicate metric identifier: ' + metricId + '.');
                    idInput.focus();
                    return;
                }

                metrics[metricId] = {
                    title: el.find('.c-metric-title').val().trim(),
                    description: el.find('.c-metric-description').val().trim(),
                    weight: window.Number(el.find('.c-metric-weight').val() || 0)
                }

                this.model.set('metrics', metrics).once('g:saved', function () {
                    girder.events.trigger('c:metricsSaved', {
                        type: 'success',
                        icon: 'ok',
                        text: 'Metrics saved.'
                    });
                }, this).saveMetrics();
            }, this);
        },

        'click .c-metric-remove-button': function (e) {
            $(e.currentTarget).parents('.c-metric-container').fadeOut(400, function () {
                $(this).remove();
            });
        }
    },

    initialize: function (settings) {
        girder.events.on('c:joinPhase', this.render, this);
        girder.cancelRestRequests('fetch');

        this.model = settings.phase;

        if (this.challenge) {
            this.render();
        } else {
            this.challenge = new covalic.models.ChallengeModel();
            this.challenge.set({
                _id: this.model.get('challengeId')
            }).on('g:fetched', function () {
                this.render();
            }, this).fetch();
        }
    },

    render: function () {
        this.$el.html(covalic.templates.scoringMetrics({
            phase: this.model,
            challenge: this.challenge,
            _: _
        }));

        this.$('button[title],.c-metric-remove-button').tooltip({
            placement: 'left'
        });

        return this;
    }
});

covalic.router.route('phase/:id/metrics', 'phaseMetrics', function(id, params) {
    // Fetch the phase by id, then render the view.
    var phase = new covalic.models.PhaseModel();
    phase.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.ScoringMetricsView, {
            phase: phase
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
