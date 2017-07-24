import _ from 'underscore';
import 'bootstrap/js/dropdown';
import moment from 'moment';
import { getCurrentUser } from 'girder/auth';
import { SORT_DESC } from 'girder/constants';
import { confirm } from 'girder/dialog';
import events from 'girder/events';
import LoadingAnimation from 'girder/views/widgets/LoadingAnimation';
import PaginateWidget from 'girder/views/widgets/PaginateWidget';
import JobModel from 'girder_plugins/jobs/models/JobModel';
import JobStatus from 'girder_plugins/jobs/JobStatus';

import SubmissionCollection from '../../collections/SubmissionCollection';
import View from '../view';
import template from '../../templates/body/userSubmissionsPage.pug';
import '../../stylesheets/body/userSubmissionsPage.styl';

var UserSubmissionsView = View.extend({
    events: {
        'click a.c-submission-delete-link': function (event) {
            var submissionId = $(event.currentTarget).attr('c-submission-id');
            var submission = this.submissions.get(submissionId);
            confirm({
                text: `Permanently delete submission <b>${submission.escape('title')}</b> from user <b>${this.user.escape('login')}</b>?`,
                yesText: 'Delete',
                escapedHtml: true,
                confirmCallback: () => {
                    submission.once('g:deleted', function () {
                        events.trigger('g:alert', {
                            icon: 'ok',
                            text: 'Submission deleted.',
                            type: 'success',
                            timeout: 4000
                        });
                    }, this).destroy();
                }
            });
        },
        'click a.c-submission-json-link': function (event) {
            var submissionId = $(event.currentTarget).attr('c-submission-id');
            var submission = this.submissions.get(submissionId);
            var submissionJson = JSON.stringify(submission, null, 4);
            console.info(submissionJson);
        }
    },

    initialize: function (settings) {
        this.phase = settings.phase;
        this.user = settings.user;

        var submissionLimit = 5;
        if (!_.isNull(settings.submissionLimit)) {
            submissionLimit = Math.max(1, window.parseInt(settings.submissionLimit, 10));
        }

        new LoadingAnimation({
            el: this.$el,
            parentView: this
        }).render();

        // XXX: add way to get total number of submissions without fetching all
        this.submissions = new SubmissionCollection();
        this.submissions.sortField = 'created';
        this.submissions.sortDir = SORT_DESC;
        this.submissions.pageLimit = submissionLimit;
        this.submissions.on('g:changed', this._renderSubmissions, this);

        var params = {
            phaseId: this.phase.id,
            userId: this.user.id
        };
        this.submissions.on('remove', () => {
            // Re-fetch collection when a submission is deleted to ensure table
            // and pagination widget are up-to-date and consistent.
            this.submissions.fetch(params, true);
        });
        this.submissions.fetch(params);

        this.paginateWidget = new PaginateWidget({
            collection: this.submissions,
            parentView: this
        });
    },

    render: function (params) {
        this.$el.html(template({
            user: this.user,
            phase: this.phase,
            submissions: this.submissions,
            getShortLog: this._getShortLog,
            JobStatus,
            moment,
            siteAdmin: getCurrentUser().get('admin'),
            jobs: params && params.jobs
        }));

        this.paginateWidget.setElement(this.$('.c-user-submissions-pagination')).render();

        var tooltipParams = {
            container: this.$el,
            animation: false,
            delay: {show: 100}
        };

        this.$('.c-tooltip').tooltip(tooltipParams);

        // Override tooltip template to set custom inner class
        this.$('.c-job-log-tooltip').tooltip(_.extend(tooltipParams, {
            template: '<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner c-job-log-tooltip-inner"></div></div>'
        }));

        return this;
    },

    _renderSubmissions: function () {
        if (getCurrentUser().get('admin')) {
            // Assume submissions that have overallScore were successful.
            // Fetch jobs for all other submissions.
            var unscoredSubmissions =
                _.filter(this.submissions.models, function (submission) {
                    return _.isUndefined(submission.get('overallScore'));
                });
            if (unscoredSubmissions.length > 0) {
                var jobs = [];
                var promises = [];
                _.each(unscoredSubmissions, function (submission) {
                    var deferred = $.Deferred();
                    var job = new JobModel({
                        _id: submission.get('jobId')
                    }).on('g:fetched', function () {
                        deferred.resolve();
                    }, this).on('g:error', function () {
                        deferred.reject();
                    }, this);
                    job.fetch();
                    jobs.push(job);
                    promises.push(deferred.promise());
                });
                $.when.apply($, promises).done(() => {
                    var jobMap = _.indexBy(jobs, 'id');
                    this.render({jobs: jobMap});
                });
            } else {
                this.render();
            }
        } else {
            this.render();
        }
    },

    /**
     * Return a string that contains the first numLines lines of a job's log.
     * The string ends in an ellipsis if any lines were omitted.
     */
    _getShortLog: function (job, numLines) {
        var log = job.get('log');
        if (log && log.length && numLines) {
            var logLines = log.join('').split('\n');
            var shortLog = logLines.slice(0, numLines);
            if (logLines.length > numLines) {
                shortLog.push('...');
            }
            return shortLog.join('\n');
        } else {
            return '';
        }
    }
});

export default UserSubmissionsView;
