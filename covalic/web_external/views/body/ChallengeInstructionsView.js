import FolderModel from 'girder/models/FolderModel';
import MarkdownWidget from 'girder/views/widgets/MarkdownWidget';

import router from '../../router';
import View from '../view';
import template from '../../templates/body/challengeInstructions.pug';
import '../../stylesheets/body/challengeInstructions.styl';

var ChallengeInstructionsView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this._saveAndGoTo('challenge/' + this.model.id +
                '/thumbnail?wizard&curr=' + (this.wizard.current + 1) +
                '&total=' + this.wizard.total);
        },

        'click .c-save-instructions': function () {
            this._saveAndGoTo('challenge/' + this.model.id);
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;

        this.model.once('c:assetsFolderFetched', function (resp) {
            this.assetsFolder = new FolderModel(resp);

            this.instructionsEditor = new MarkdownWidget({
                parentView: this,
                prefix: 'challenge-instructions',
                placeholder: 'Enter challenge overview',
                enableUploads: true,
                maxUploadSize: 1024 * 1024 * 2,
                allowedExtensions: ['png', 'jpeg', 'jpg'],
                parent: this.assetsFolder
            });

            this.render();
        }, this).fetchAssetsFolder();
    },

    render: function () {
        this.$el.html(template({
            challenge: this.model,
            wizard: this.wizard,
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

export default ChallengeInstructionsView;
