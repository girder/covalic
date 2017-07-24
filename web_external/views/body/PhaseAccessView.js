import _ from 'underscore';
import events from 'girder/events';
import AccessWidget from 'girder/views/widgets/AccessWidget';

import router from '../../router';
import View from '../view';
import template from '../../templates/body/phaseAccessPage.pug';
import '../../stylesheets/body/challengeAccess.styl';

var PhaseAccessView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                router.navigate('phase/' + this.model.id +
                    '/instructions?wizard&curr=' + (this.wizard.current + 1) + '&total=' +
                    this.wizard.total, {trigger: true});
            }, this).saveAccessList();
        },

        'click .c-save-access-button': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                events.trigger('g:alert', {
                    text: 'Settings saved.',
                    type: 'success',
                    icon: 'ok',
                    timeout: 3000
                });
            }, this).saveAccessList();
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        if (this.wizard && !_.has(this.wizard, 'current')) {
            this.wizard.current = 0;
        }

        this.accessWidget = new AccessWidget({
            parentView: this,
            modelType: 'phase',
            modal: false,
            model: this.model,
            hideRecurseOption: true,
            hideSaveButton: true
        });

        this.render();
    },

    render: function () {
        this.$el.html(template({
            wizard: this.wizard,
            phase: this.model
        }));

        this.accessWidget.setElement(this.$('.c-access-list-container')).render();

        return this;
    }
});

export default PhaseAccessView;
