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

        this.$('button[title]').tooltip({
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
