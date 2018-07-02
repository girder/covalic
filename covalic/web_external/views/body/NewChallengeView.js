import _ from 'underscore';
import DateTimeRangeWidget from 'girder/views/widgets/DateTimeRangeWidget';

import router from '../../router';
import View from '../view';
import ChallengeModel from '../../models/ChallengeModel';
import template from '../../templates/body/newChallengePage.pug';
import '../../stylesheets/widgets/wizards.styl';
import '../../stylesheets/body/newChallengePage.styl';

var NewChallengeView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            var challenge = new ChallengeModel({
                name: this.$('#c-challenge-name').val(),
                description: this.$('#c-challenge-description').val(),
                organizers: this.$('#c-challenge-organizers').val(),
                startDate: this.dateTimeRangeWidget.fromDateString(),
                endDate: this.dateTimeRangeWidget.toDateString()
            });

            challenge.on('g:saved', function () {
                router.navigate(
                    `challenge/${challenge.id}/access?wizard&curr=${this.wizard.current + 1}&total=${this.wizard.total}`,
                    {trigger: true});
            }, this).off('g:error').on('g:error', function (err) {
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
                this.$('#c-challenge-' + err.responseJSON.field).focus();
            }, this).save();

            this.$('.g-validation-failed-message').text('');
        }
    },

    initialize: function (settings) {
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

        this.dateTimeRangeWidget.setElement(this.$('#c-challenge-timeframe')).render();

        this.$('#c-challenge-name').focus();

        return this;
    }
});

export default NewChallengeView;
