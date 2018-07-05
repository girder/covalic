import _ from 'underscore';
import { getCurrentUser } from 'girder/auth';
import { AccessType } from 'girder/constants';
import { formatDate, DATE_SECOND } from 'girder/misc';
import ItemCollection from 'girder/collections/ItemCollection';
import FolderModel from 'girder/models/FolderModel';
import ItemModel from 'girder/models/ItemModel';
import UserModel from 'girder/models/UserModel';
import eventStream from 'girder/utilities/EventStream';
import JobModel from 'girder_plugins/jobs/models/JobModel';
import JobStatus from 'girder_plugins/jobs/JobStatus';
import JobDetailsWidget from 'girder_plugins/jobs/views/JobDetailsWidget';

import eventStreamEnabled from '../../eventStreamEnabled';
import PhaseModel from '../../models/PhaseModel';
import SubmissionModel from '../../models/SubmissionModel';
import ScoreDetailWidget from '../widgets/ScoreDetailWidget';
import router from '../../router';
import View from '../view';
import template from '../../templates/body/submissionPage.pug';
import progressTemplate from '../../templates/widgets/scoringProgress.pug';
import errorTemplate from '../../templates/widgets/submissionError.pug';
import '../../stylesheets/body/submissionPage.styl';

// We must reapply the global JobStatus changes for this bundle's
// copy of the JobStatus object, otherwise our copy of the job widgets
// will not have those modifications and rendering will fail.
// This can only go away once girder plugins are dynamically linked against
// one another.
JobStatus.registerStatus({
    WORKER_FETCHING_INPUT: {
        value: 820,
        text: 'Fetching input',
        icon: 'icon-download'
    },
    WORKER_CONVERTING_INPUT: {
        value: 821,
        text: 'Converting input',
        icon: 'icon-shuffle'
    },
    WORKER_CONVERTING_OUTPUT: {
        value: 822,
        text: 'Converting output',
        icon: 'icon-shuffle'
    },
    WORKER_PUSHING_OUTPUT: {
        value: 823,
        text: 'Pushing output',
        icon: 'icon-upload'
    }
});

// Time in ms between polling for job updates when the eventStream is disabled.
const jobPollingDelay = 1000;

var SubmissionView = View.extend({
    events: {
        'click .c-restart-error-submission-button': function () {
            // create a new submission with the same properties
            var submission = new SubmissionModel();
            submission.on('c:submissionPosted', function () {
                router.navigate('submission/' + submission.id, {trigger: true});
            }, this).postSubmission({
                phaseId: this.submission.get('phaseId'),
                folderId: this.submission.get('folderId'),
                title: this.submission.get('title'),
                organization: this.submission.get('organization'),
                organizationUrl: this.submission.get('organizationUrl'),
                documentationUrl: this.submission.get('documentationUrl')
            });
        },

        'click .c-download-submission-data': function () {
            // Get submission folder with details
            var submissionFolder = new FolderModel({
                _id: this.submission.get('folderId')
            });
            submissionFolder.once('g:fetched', function () {
                submissionFolder.once('g:fetched.details', function () {
                    this._downloadSubmissionData(submissionFolder);
                }, this).fetch({
                    extraPath: 'details'
                });
            }, this).fetch();
        }
    },

    initialize: function (settings) {
        this.submission = settings.submission;
        // Must unbind previous fetch handlers to avoid infinite callbacks
        this.submission.off('g:fetched');

        this.phase = new PhaseModel({
            _id: this.submission.get('phaseId')
        });
        this.job = new JobModel({
            _id: this.submission.get('jobId')
        });

        this.phase.fetch().done(() => {
            var currentUser = getCurrentUser();
            this.render();

            // Detect if the submission is unscored.  If so, then automatically
            // update the page when the scoring job status changes.
            if (!this.submission.get('score') && currentUser &&
                (currentUser.id === this.submission.get('creatorId') || currentUser.get('admin'))
            ) {
                this.job.fetch().done(() => {
                    if (this.job.get('status') === JobStatus.ERROR) {
                        this._renderProcessingError();
                    } else if (this.job.get('status') === JobStatus.SUCCESS) {
                        this.submission.fetch().done(() => this.render());
                    } else {
                        this._waitForScoringJob();
                        this.render();
                    }
                });
            }
        });
        this._pollingHandle = null;
    },

    render: function () {
        var overallScore = this.submission.get('overallScore');
        if (!_.contains(['inf', '-inf', 'nan'], overallScore)) {
            overallScore = Math.round(this.submission.get('overallScore') * 1000) / 1000;
        }

        this.$el.html(template({
            submission: this.submission,
            overallScore,
            scoreHidden: !!(this.phase.get('hideScores') &&
                            this.phase.getAccessLevel() < AccessType.WRITE),
            JobStatus,
            job: this.job,
            created: formatDate(this.submission.get('created'), DATE_SECOND),
            download: this.phase.getAccessLevel() > AccessType.READ
        }));

        var userModel = new UserModel({
            _id: this.submission.get('creatorId')
        });
        this.$('.c-user-portrait').css(
            'background-image', `url(${userModel.getGravatarUrl(64)})`);

        if (this.submission.get('score')) {
            new ScoreDetailWidget({
                el: this.$('.c-submission-score-detail-container'),
                submission: this.submission,
                phase: this.phase,
                parentView: this
            }).render();
        }
        return this;
    },

    destroy: function () {
        this._stopPollingForScore();
        View.prototype.destroy.call(this);
    },

    /**
     * Download submission data from folder. If folder contains only one item,
     * download the item directly.
     */
    _downloadSubmissionData: function (folder) {
        var numFolders = folder.get('nFolders');
        var numItems = folder.get('nItems');
        if (numFolders === 0 && numItems === 1) {
            // Download item
            var items = new ItemCollection();
            items.once('g:changed', function () {
                var item = new ItemModel({
                    _id: items.at(0).id
                }).once('g:fetched', function () {
                    item.download();
                }, this);
                item.fetch();
            }, this).fetch({
                folderId: folder.id
            });
        } else {
            // Download folder
            folder.download();
        }
    },

    _statusHandler: function (progress) {
        var status = window.parseInt(progress.data.status);
        if (progress.data._id === this.job.id && status === JobStatus.SUCCESS) {
            this.submission.off().on('g:fetched', function () {
                eventStream.off('g:event.job_status', null, this);
                eventStream.off('g:event.progress', null, this);
                this.render();
            }, this).fetch();
        } else {
            this.job.fetch();
        }
    },

    _progressHandler: function (progress) {
        if (this.job.get('progress')) {
            var percentText = '0%';

            if (progress._id === this.job.get('progress').notificationId) {
                if (progress.data.state === 'active') {
                    var width = '0', barClass = [], progressClass = [];
                    if (progress.data.total <= 0) {
                        width = '100%';
                        barClass.push('progress-bar-warning');
                        progressClass.push('progress-striped', 'active');
                    } else if (progress.data.current <= 0) {
                        width = '0';
                        percentText = '0%';
                    } else if (progress.data.current >= progress.data.total) {
                        percentText = width = '100%';
                    } else {
                        var percent = (100 * progress.data.current / progress.data.total);
                        width = Math.round(percent) + '%';
                        percentText = percent.toFixed(1) + '%';
                    }

                    this.$('.c-score-progress-container').html(progressTemplate({
                        progress,
                        width,
                        barClass: barClass.join(' '),
                        progressClass: progressClass.join(' '),
                        percentText
                    }));
                }
            }
        } else {
            this.job.once('g:fetched', function () {
                if (this.job.get('progress')) {
                    this._progressHandler(progress);
                }
            }, this).fetch();
        }
    },

    // If an error occurred during processing, we'll display error info.
    _renderProcessingError: function () {
        this.$('.c-submission-display-body').html(errorTemplate({
            job: this.job,
            adminUser: (getCurrentUser() && getCurrentUser().get('admin'))
        }));

        new JobDetailsWidget({
            el: this.$('.c-job-details-container'),
            parentView: this,
            job: this.job
        }).render();
    },

    /**
     * Respond to job updates by either polling or listening to the eventstream.
     */
    _waitForScoringJob: function () {
        if (eventStreamEnabled()) {
            eventStream.on('g:event.job_status', this._statusHandler, this);
            eventStream.on('g:event.progress', this._progressHandler, this);
        } else {
            this._stopPollingForScore();
            this._pollForScore();
        }
    },

    /**
     * Poll the job model and wait for status updates, rerendering
     * when the status changes.
     */
    _pollForScore: function () {
        this._pollingHandle = window.setTimeout(() => {
            this._pollingHandle = null;
            this.job.fetch().done(() => {
                const status = this.job.get('status');

                if (status === JobStatus.ERROR) {
                    this._renderProcessingError();
                } else if (status === JobStatus.SUCCESS) {
                    this.submission.fetch().done(() => this.render());
                } else {
                    if (status !== this._lastJobStatus) {
                        this._lastJobStatus = status;
                        this.render();
                    }
                    this._pollForScore();
                }
            });
        }, jobPollingDelay);
    },

    _stopPollingForScore: function () {
        if (this._pollingHandle) {
            window.clearTimeout(this._pollingHandle);
            this._pollingHandle = null;
        }
    }
});

export default SubmissionView;
