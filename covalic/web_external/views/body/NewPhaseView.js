import _ from 'underscore';
import DateTimeRangeWidget from 'girder/views/widgets/DateTimeRangeWidget';

import router from '../../router';
import View from '../view';
import PhaseModel from '../../models/PhaseModel';
import template from '../../templates/body/newPhasePage.pug';
import '../../stylesheets/widgets/wizards.styl';
import '../../stylesheets/body/newChallengePage.styl';

var NewPhaseView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            var phase = new PhaseModel({
                challengeId: this.challenge.id,
                name: this.$('#c-phase-name').val(),
                description: this.$('#c-phase-description').val(),
                active: this.$('#c-phase-active').is(':checked'),
                hideScores: this.$('#c-phase-hide-scores').is(':checked'),
                startDate: this.dateTimeRangeWidget.fromDateString(),
                endDate: this.dateTimeRangeWidget.toDateString(),
                type: this.$('#c-phase-training').is(':checked') ? 'training' : ''
            });

            phase.on('g:saved', function () {
                router.navigate('phase/' + phase.id +
                    '/access?wizard&curr=' + (this.wizard.current + 1) + '&total=' +
                    this.wizard.total, {trigger: true});
            }, this).off('g:error').on('g:error', function (err) {
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
                this.$('#c-phase-' + err.responseJSON.field).focus();
            }, this).save();

            this.$('.g-validation-failed-message').text('');
        }
    },

    initialize: function (settings) {
        this.challenge = settings.challenge;
        this.wizard = settings.wizard || false;
        if (this.wizard && !_.has(this.wizard, 'current')) {
            this.wizard.current = 0;
        }

        this.dateTimeRangeWidget = new DateTimeRangeWidget({
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(template({
            wizard: this.wizard
        }));

        this.dateTimeRangeWidget.setElement(this.$('#c-phase-timeframe')).render();

        this.$('#c-phase-name').focus();

        return this;
    }
});

export default NewPhaseView;
