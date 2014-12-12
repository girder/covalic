covalic.models.SubmissionModel = girder.Model.extend({
    resourceName: 'covalic_submission',

    postSubmission: function (phaseId, folderId) {
        girder.restRequest({
            path: this.resourceName,
            type: 'POST',
            data: {
                folderId: folderId,
                phaseId: phaseId
            }
        }).done(_.bind(function (resp) {
            this.set(resp);
            this.trigger('c:submissionPosted', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    }
});
