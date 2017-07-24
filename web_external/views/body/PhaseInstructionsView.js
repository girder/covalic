import FolderModel from 'girder/models/FolderModel';
import MarkdownWidget from 'girder/views/widgets/MarkdownWidget';

import router from '../../router';
import View from '../view';
import template from '../../templates/body/phaseInstructions.pug';
import '../../stylesheets/body/challengeInstructions.styl';

var PhaseInstructionsView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this._saveAndGoTo('phase/' + this.model.id +
                '/input?wizard&curr=' + (this.wizard.current + 1) +
                '&total=' + this.wizard.total);
        },

        'click .c-save-instructions': function () {
            this._saveAndGoTo('phase/' + this.model.id);
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;

        this.phaseFolder = new FolderModel({
            _id: this.model.get('folderId')
        });

        this.instructionsEditor = new MarkdownWidget({
            parentView: this,
            prefix: 'phase-instructions',
            placeholder: 'Enter phase overview',
            enableUploads: true,
            maxUploadSize: 1024 * 1024 * 2,
            allowedExtensions: ['png', 'jpeg', 'jpg'],
            parent: this.phaseFolder
        });

        this.render();
    },

    render: function () {
        this.$el.html(template({
            wizard: this.wizard,
            phase: this.model,
            markdownLink: 'https://daringfireball.net/projects/markdown/syntax'
        }));

        this.instructionsEditor.setElement(
            this.$('.c-instructions-markdown-editor')).render()
            .val(this.model.get('instructions') || '');

        return this;
    },

    _saveAndGoTo: function (route) {
        this.model.once('g:saved', function () {
            router.navigate(route, {trigger: true});
        }, this).set({
            instructions: this.instructionsEditor.val()
        }).save();
    }
});

export default PhaseInstructionsView;
