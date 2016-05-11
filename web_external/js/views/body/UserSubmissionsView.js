/**
* View for a user's submissions to a phase.
*/
covalic.views.UserSubmissionsView = covalic.View.extend({
    initialize: function (settings) {
        this.phase = settings.phase;
        this.user = settings.user;

        var submissionLimit = 5;
        if (!_.isNull(settings.submissionLimit)) {
            submissionLimit = Math.max(1, parseInt(settings.submissionLimit, 10));
        }

        new girder.views.LoadingAnimation({
            el: this.$el,
            parentView: this
        }).render();

        // XXX: add way to get total number of submissions without fetching all
        this.submissions = new covalic.collections.SubmissionCollection();
        this.submissions.sortField = 'created';
        this.submissions.sortDir = girder.SORT_DESC;
        this.submissions.pageLimit = submissionLimit;
        this.submissions.on('g:changed', function () {
            if (girder.currentUser.get('admin')) {
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
                        var job = new girder.models.JobModel({
                            _id: submission.get('jobId')
                        }).on('g:fetched', function () {
                            deferred.resolve();
                        }, this).on('g:error', function () {
                            deferred.reject();
                        }, this).fetch();
                        jobs.push(job);
                        promises.push(deferred.promise());
                    });
                    $.when.apply($, promises).done(_.bind(function () {
                        var jobMap = _.indexBy(jobs, 'id');
                        this.render({jobs: jobMap});
                    }, this));
                } else {
                    this.render();
                }
            } else {
                this.render();
            }
        }, this).fetch({
            phaseId: this.phase.id,
            userId: this.user.id
        });

        this.paginateWidget = new girder.views.PaginateWidget({
            collection: this.submissions,
            parentView: this
        });
    },

    render: function (params) {
        this.$el.html(covalic.templates.userSubmissionsPage({
            user: this.user,
            submissions: this.submissions,
            getShortLog: this._getShortLog,
            girder: girder,
            moment: moment,
            siteAdmin: girder.currentUser.get('admin'),
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

    /**
     * Return a string that contains the first numLines lines of a job's log.
     * The string ends in an ellipsis if any lines were omitted.
     */
    _getShortLog: function (job, numLines) {
        var logLines = job.get('log').split('\n');
        var shortLog = logLines.slice(0, numLines);
        if (logLines.length > numLines && numLines > 0) {
            shortLog.push('...');
        }
        return shortLog.join('\n');
    }
});
