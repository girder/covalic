import _ from 'underscore';
import events from 'girder/events';
import { getCurrentUser } from 'girder/auth';
import FolderModel from 'girder/models/FolderModel';
import UploadWidget from 'girder/views/widgets/UploadWidget';
import SubmissionModel from '../../models/SubmissionModel';
import View from '../view';
import router from '../../router';
import template from '../../templates/body/submitPage.pug';
import mismatchTemplate from '../../templates/widgets/mismatchedInputs.pug';
import '../../stylesheets/body/submitPage.styl';

var SubmitView = View.extend({
    events: {
        'input .c-submission-title-input': function () {
            this.title = this.$('.c-submission-title-input').val().trim();
            this.$('.c-submission-title-error').empty();
            this.uploadWidget.setUploadEnabled(!!this.title && this.filesCorrect);
        }
    },

    initialize: function (settings) {
        this.phase = settings.phase;
        this.phase.fetchGroundtruthItems();
        this.filesCorrect = false;
        this.render();
    },

    render: function () {
        this.$el.html(template({
            phase: this.phase,
            maxTitleLength: 80
        }));

        this.uploadWidget = new UploadWidget({
            el: this.$('.c-submit-upload-widget'),
            modal: false,
            noParent: true,
            title: null,
            overrideStart: true,
            parentView: this
        }).render();

        this.$('input.c-submission-title-input').focus();

        this.listenTo(this.uploadWidget, 'g:filesChanged', this.filesSelected);
        this.listenTo(this.uploadWidget, 'g:uploadStarted', this.uploadStarted);
        this.listenTo(this.uploadWidget, 'g:uploadFinished', this.uploadFinished);
    },

    /**
     * Called when the user selects or drops files to be uploaded.
     */
    filesSelected: function (files) {
        var transformName = function (f) {
            var dotPos = _.indexOf(f.name, '.');
            if (dotPos === -1) {
                return f.name;
            } else {
                return f.name.substr(0, dotPos);
            }
        };

        var matchInfo = this._matchInput(
            _.map(files, transformName),
            _.map(this.phase.get('groundtruthItems'), transformName)
        );

        var matchSubmissions = this.phase.get('matchSubmissions');
        if (_.isUndefined(matchSubmissions)) {
            matchSubmissions = true;
        }

        matchInfo.ok = !matchSubmissions ||
                       (_.isEmpty(matchInfo.unmatchedGroundtruths) &&
                        _.isEmpty(matchInfo.unmatchedInputs));

        var titleOk = this.$('input.c-submission-title-input').val().trim().length > 0;

        if (!titleOk) {
            this.$('input.c-submission-title').focus();
            this.$('.c-submission-title-error').text(
                'Please enter a title for your submission.');
        }

        this.uploadWidget.setUploadEnabled(matchInfo.ok && titleOk);

        this.$('.c-submission-mismatch-container').html(mismatchTemplate({
            matchInfo
        }));

        this.filesCorrect = matchInfo.ok;
    },

    _matchInput: function (inputs, groundtruths) {
        return {
            unmatchedGroundtruths: _.difference(groundtruths, inputs),
            unmatchedInputs: _.difference(inputs, groundtruths),
            matched: _.intersection(inputs, groundtruths)
        };
    },

    /**
     * When "start upload" is clicked, we want to make a folder in the user's
     * personal space for the submission contents, so we do that and then proceed
     * uploading into it.
     */
    uploadStarted: function () {
        this.folder = new FolderModel({
            name: `submission_${this.phase.id}_${Date.now()}`,
            parentType: 'user',
            parentId: getCurrentUser().id,
            description: 'Challenge submission'
        });

        this.folder.on('g:saved', function () {
            this.uploadWidget.parentType = 'folder';
            this.uploadWidget.parent = this.folder;
            this.uploadWidget.uploadNextFile();
        }, this).on('g:error', function () {
            events.trigger('g:alert', {
                icon: 'cancel',
                text: 'Could not create submission folder.',
                type: 'error',
                timeout: 4000
            });
        }, this).save();
    },

    uploadFinished: function () {
        var submission = new SubmissionModel();
        submission.on('c:submissionPosted', function () {
            router.navigate(`submission/${submission.id}`, {trigger: true});
        }, this).postSubmission({
            phaseId: this.phase.id,
            folderId: this.folder.id,
            title: this.title
        });
    }
});

export default SubmitView;
