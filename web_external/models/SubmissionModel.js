import _ from 'underscore';
import Model from 'girder/models/Model';
import { apiRoot, restRequest } from 'girder/rest';

var SubmissionModel = Model.extend({
    resourceName: 'covalic_submission',
    sanitizedUrlFields: ['organizationUrl', 'documentationUrl'],

    postSubmission: function (opts) {
        restRequest({
            path: this.resourceName,
            type: 'POST',
            data: {
                folderId: opts.folderId,
                phaseId: opts.phaseId,
                title: opts.title,
                organization: opts.organization,
                organizationUrl: opts.organizationUrl,
                documentationUrl: opts.documentationUrl
            }
        }).done((resp) => {
            this.set(resp);
            this.trigger('c:submissionPosted', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    downloadUrl: function () {
        return `${apiRoot}/folder/${this.get('folderId')}/download`;
    },

    /**
     * Overrides the normal get() to sanitize user-provided URLs.
     */
    get: function (attribute) {
        const val = Model.prototype.get.call(this, attribute);

        if (val && _.contains(this.sanitizedUrlFields, attribute) &&
                !val.startsWith('http://') && !val.startsWith('https://')) {
            return 'http://' + val;
        } else {
            return val;
        }
    }
});

export default SubmissionModel;
