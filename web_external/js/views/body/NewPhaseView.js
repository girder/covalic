covalic.views.NewPhaseView = covalic.View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            var phase = new covalic.models.PhaseModel();
            phase.set({
                challengeId: this.challenge.id,
                name: this.$('#c-phase-name').val(),
                description: this.$('#c-challenge-description').val(),
                active: this.$('#c-phase-active').is(':checked'),
                startDate: this.dateTimeRangeWidget.fromDateString(),
                endDate: this.dateTimeRangeWidget.toDateString()
            });

            phase.on('g:saved', function () {
                covalic.router.navigate('phase/' + phase.id +
                    '/access?wizard&curr=' + (this.wizard.current + 1) + '&total=' +
                    this.wizard.total, {trigger: true});
            }, this).off('g:error').on('g:error', function (err) {
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
                this.$('button.c-save-challenge').removeClass('disabled');
                this.$('#c-phase-' + err.responseJSON.field).focus();
            }, this).save();

            this.$('button.c-save-challenge').addClass('disabled');
            this.$('.g-validation-failed-message').text('');
        }
    },

    initialize: function (settings) {
        this.challenge = settings.challenge;
        this.wizard = settings.wizard || false;
        if (this.wizard && !_.has(this.wizard, 'current')) {
            this.wizard.current = 0;
        }

        this.dateTimeRangeWidget = new girder.views.DateTimeRangeWidget({
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.newPhasePage({
            wizard: this.wizard
        }));

        this.dateTimeRangeWidget.setElement(this.$('#c-phase-timeframe'));
        this.dateTimeRangeWidget.render();

        this.$('#c-phase-name').focus();

        return this;
    }
});

covalic.router.route('challenge/:id/phase/new', 'newPhase', function (id) {
    var challenge = new covalic.models.ChallengeModel({
        _id: id
    });
    girder.events.trigger('g:navigateTo', covalic.views.NewPhaseView, {
        challenge: challenge,
        wizard: {
            total: 5
        }
    });
});
