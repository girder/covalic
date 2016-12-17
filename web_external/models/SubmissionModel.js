import Model from 'girder/models/Model';
import { restRequest } from 'girder/rest';

var SubmissionModel = Model.extend({
    resourceName: 'covalic_submission',

    postSubmission: function (opts) {
        restRequest({
            path: this.resourceName,
            type: 'POST',
            data: {
                folderId: opts.folderId,
                phaseId: opts.phaseId,
                title: opts.title
            }
        }).done((resp) => {
            this.set(resp);
            this.trigger('c:submissionPosted', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    downloadUrl: function () {
        return `${girder.apiRoot}/folder/${this.get('folderId')}/download`;
    }
});

export default SubmissionModel;
