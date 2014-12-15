/**
* View for an individual submission.
*/
covalic.views.SubmissionView = covalic.View.extend({
    initialize: function (settings) {
        this.submission = settings.submission;

        if (!this.submission.get('score')) {
            this.job = new girder.models.JobModel({
                _id: this.submission.get('jobId')
            });
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
                submission: this.submission
            }).render();
        }
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
    }, this).on('g:error', function () {
        girder.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
