import events from 'girder/events';
import router from '../../router';
import View from '../view';
import template from '../../templates/body/phaseConfigureSubmissionsPage.pug';

var PhaseConfigureSubmissionsView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this._save(() => {
                router.navigate(`phase/${this.model.id}`, {trigger: true});
            });
        },

        'click .c-save-options': function () {
            this._save(() => {
                events.trigger('g:alert', {
                    text: 'Settings saved.',
                    type: 'success',
                    icon: 'ok',
                    timeout: 3000
                });
            });
        }
    },

    _save: function (onSuccess) {
        var fields = {
            matchSubmissions: this.$('#c-phase-match-submissions').is(':checked')
        };

        this.model.set(fields);
        this.model.once('g:saved', onSuccess);
        this.model.off('g:error').on('g:error', (err) => {
            this.$('.g-validation-failed-message').text(err.responseJSON.message);
            this.$(`#c-phase-${err.responseJSON.field}`).focus();
        }).save();

        this.$('.g-validation-failed-message').text('');
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;

        this.render();
    },

    render: function () {
        this.$el.html(template({
            wizard: this.wizard,
            phase: this.model
        }));

        return this;
    }
});

export default PhaseConfigureSubmissionsView;
