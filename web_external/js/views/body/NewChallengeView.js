covalic.views.NewChallengeView = covalic.View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            var challenge = new covalic.models.ChallengeModel();
            challenge.set({
                name: this.$('#c-challenge-name').val(),
                description: this.$('#c-challenge-description').val(),
                organizers: this.$('#c-challenge-organizers').val(),
                startDate: this.dateTimeRangeWidget.fromDateString(),
                endDate: this.dateTimeRangeWidget.toDateString()
            });

            challenge.on('g:saved', function () {
                covalic.router.navigate('challenge/' + challenge.id +
                    '/access?wizard&curr=' + (this.wizard.current + 1) + '&total=' +
                    this.wizard.total, {trigger: true});
            }, this).off('g:error').on('g:error', function (err) {
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
                this.$('button.c-save-challenge').removeClass('disabled');
                this.$('#c-challenge-' + err.responseJSON.field).focus();
            }, this).save();

            this.$('button.c-save-challenge').addClass('disabled');
            this.$('.g-validation-failed-message').text('');
        }
    },

    initialize: function (settings) {
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
        this.$el.html(covalic.templates.newChallengePage({
            wizard: this.wizard
        }));

        this.dateTimeRangeWidget.setElement(this.$('#c-challenge-timeframe'));
        this.dateTimeRangeWidget.render();

        this.$('#c-challenge-name').focus();

        return this;
    }
});

covalic.router.route('challenge/new', 'newChallenge', function () {
    girder.events.trigger('g:navigateTo', covalic.views.NewChallengeView, {
        wizard: {
            total: 4
        }
    });
});
