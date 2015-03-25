covalic.collections.ChallengePhaseCollection = girder.Collection.extend({
    resourceName: 'challenge_phase',
    model: covalic.models.PhaseModel,
    pageLimit: 100,

    // Override default sort field
    sortField: 'ordinal'
});
