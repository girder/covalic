covalic.models.PhaseModel = girder.Model.extend({
    resourceName: 'challenge_phase',

    postSubmission: function (folderId) {
        girder.restRequest({
            path: this.resourceName + '/' + this.get('_id') + '/submission',
            type: 'POST',
            data: {
                folderId: folderId
            }
        }).done(_.bind(function (resp) {
            this.trigger('c:submissionPosted', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    }
});
