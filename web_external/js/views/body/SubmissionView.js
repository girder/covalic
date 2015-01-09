/**
* View for an individual submission.
*/
covalic.views.SubmissionView = covalic.View.extend({
    events: {
        'click .c-leaderboard-button': function () {
            covalic.router.navigate('phase/' + this.submission.get('phaseId') +
               '/leaderboard', {trigger: true});
        }
    },

    initialize: function (settings) {
        this.submission = settings.submission;

        if (!this.submission.get('score')) {
            girder.eventStream.on('g:event.job_status', this._progressHandler, this);

            if (girder.currentUser && (
                    girder.currentUser.get('_id') === this.submission.get('userId') ||
                    girder.currentUser.get('admin'))) {
                this.job = new girder.models.JobModel({
                    _id: this.submission.get('jobId')
                }).on('g:fetched', function () {
                    if (this.job.get('status') === girder.jobs_JobStatus.ERROR) {
                        this._renderProcessingError();
                    }
                }, this).fetch();
            }
        }
        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.submissionPage({
            submission: this.submission,
            created: girder.formatDate(this.submission.get('created'), girder.DATE_SECOND)
        }));

        if (this.submission.get('score')) {
            new covalic.views.ScoreDetailWidget({
                el: this.$('.c-submission-score-detail-container'),
                submission: this.submission,
                parentView: this
            }).render();
        }
    },

    _progressHandler: function (progress) {
        var status = window.parseInt(progress.data.status);
        if (progress.data._id === this.job.get('_id') &&
                status === girder.jobs_JobStatus.SUCCESS) {
            this.submission.off().on('g:fetched', function () {
                girder.eventStream.off('g:event.job_status', null, this);
                this.render();
            }, this).fetch();
        } else if (status === girder.jobs_JobStatus.ERROR) {
            this.job.fetch();
        }
    },

    // If an error occurred during processing, we'll display error info.
    _renderProcessingError: function () {
        this.$('.c-submission-display-body').html(covalic.templates.submissionError({
            job: this.job
        }));

        new girder.views.jobs_JobDetailsWidget({
            el: this.$('.c-job-details-container'),
            parentView: this,
            job: this.job
        }).render();
    }
});

covalic.router.route('submission/:id', 'phase_submission', function (id, params) {
    var submission = new covalic.models.SubmissionModel();
    submission.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.SubmissionView, {
            submission: submission
        });
    }).on('g:error', function () {
        girder.router.navigate('challenges', {trigger: true});
    }).fetch();
});
