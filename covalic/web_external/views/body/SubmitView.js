import 'bootstrap-3-typeahead';
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

/**
 * View that allows users to post a submission to a phase.
 *
 * The submission form always includes a title field. The form includes other
 * submission fields depending on whether the fields are enabled for the phase.
 */
var SubmitView = View.extend({
    events: {
        'input .c-submission-title-input': function (event) {
            this.title = $(event.currentTarget).val().trim();
            this.validateInputs();
        },
        'input .c-submission-organization-input': function (event) {
            this.organization = $(event.currentTarget).val().trim();
            this.validateInputs();
        },
        'input .c-submission-organization-url-input': function (event) {
            this.organizationUrl = $(event.currentTarget).val().trim();
            this.validateInputs();
        },
        'input .c-submission-documentation-url-input': function (event) {
            this.documentationUrl = $(event.currentTarget).val().trim();
            this.validateInputs();
        },
        'input .c-submission-approach-input': '_updateApproach'
    },

    initialize: function (settings) {
        this.phase = settings.phase;
        this.phase.fetchGroundtruthItems();

        this.hasFiles = false;
        this.filesCorrect = false;
        this.title = null;
        this.organization = null;
        this.organizationUrl = null;
        this.documentationUrl = null;
        this.approaches = [];
        this.approach = null;

        this.submission = new SubmissionModel();
        this.submission.fetchApproaches(getCurrentUser(), this.phase).done((approaches) => {
            this.approaches = approaches;
            this.render();
        });
    },

    render: function () {
        this.$el.html(template({
            approach: this.approach,
            phase: this.phase,
            submission: this.submission,
            approaches: this.approaches,
            maxTextLength: 80,
            maxUrlLength: 1024
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
        this.$('.c-submission-approach-input').typeahead({
            source: this.approaches,
            afterSelect: () => this._updateApproach()
        });
        return this;
    },

    destroy: function () {
        this.$('.c-submission-approach-input').typeahead('destroy');
        return View.prototype.destroy.call(this);
    },

    /**
     * Validate all text inputs. Enable upload button if inputs valid and
     * uploaded files are valid.
     */
    validateInputs: function () {
        this.$('.c-submission-validation-error').empty();

        var valid = true;
        var errorText = null;

        if (_.isEmpty(this.title)) {
            this.$('input.c-submission-title').focus();
            errorText = 'Please enter a title for your submission.';
            valid = false;
        } else if (this.phase.enableOrganization() && this.phase.requireOrganization() && _.isEmpty(this.organization)) {
            this.$('input.c-submission-organization').focus();
            errorText = 'Please enter an organization or team name.';
            valid = false;
        } else if (this.phase.enableOrganizationUrl() && this.phase.requireOrganizationUrl() && _.isEmpty(this.organizationUrl)) {
            this.$('input.c-submission-organization-url').focus();
            errorText = 'Please enter a URL for the organization or team.';
            valid = false;
        } else if (this.phase.enableDocumentationUrl() && this.phase.requireDocumentationUrl() && _.isEmpty(this.documentationUrl)) {
            this.$('input.c-submission-documentation-url').focus();
            errorText = 'Please enter a URL for documentation about your submission.';
            valid = false;
        }

        if (!valid && this.hasFiles) {
            this.$('.c-submission-validation-error').text(errorText);
        }

        var enabled = valid && this.filesCorrect;
        this.uploadWidget.setUploadEnabled(enabled);
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

        this.$('.c-submission-mismatch-container').html(mismatchTemplate({
            matchInfo
        }));

        this.hasFiles = true;
        this.filesCorrect = matchInfo.ok;

        this.validateInputs();
    },

    _updateApproach: function () {
        this.approach = this.$('.c-submission-approach-input').val().trim();
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
        this.submission.on('c:submissionPosted', function () {
            router.navigate(`submission/${this.submission.id}`, {trigger: true});
        }, this).postSubmission({
            phaseId: this.phase.id,
            folderId: this.folder.id,
            title: this.title,
            organization: this.organization,
            organizationUrl: this.organizationUrl,
            documentationUrl: this.documentationUrl,
            approach: this.approach
        });
    }
});

export default SubmitView;
