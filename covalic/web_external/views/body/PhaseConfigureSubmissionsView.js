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
    },

    _save: function (onSuccess) {
        var fields = {
            matchSubmissions: this.$('#c-phase-match-submissions').is(':checked'),
            enableOrganization: this.$('#c-phase-enable-organization').is(':checked'),
            enableOrganizationUrl: this.$('#c-phase-enable-organization-url').is(':checked'),
            enableDocumentationUrl: this.$('#c-phase-enable-documentation-url').is(':checked'),
            requireOrganization: this.$('#c-phase-require-organization').is(':checked'),
            requireOrganizationUrl: this.$('#c-phase-require-organization-url').is(':checked'),
            requireDocumentationUrl: this.$('#c-phase-require-documentation-url').is(':checked')
        };

        this.model.set(fields);
        this.model.once('g:saved', onSuccess);
        this.model.off('g:error').on('g:error', (err) => {
            this.$('.g-validation-failed-message').text(err.responseJSON.message);
            this.$(`#c-phase-${err.responseJSON.field}`).focus();
        }).save();

        this.$('.g-validation-failed-message').text('');
    }
});

export default PhaseConfigureSubmissionsView;
