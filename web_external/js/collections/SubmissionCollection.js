covalic.collections.SubmissionCollection = girder.Collection.extend({
    resourceName: 'covalic_submission',
    model: covalic.models.SubmissionModel,

    sortField: 'overallScore',
    sortDir: girder.SORT_DESC,
    comparator: null,

    pageLimit: 100
});
