// TODO what makes most sense
// covalic.collections.ChallengeCollection = covalic.Collection.extend
// covalic.collections.ChallengeCollection = girder.Collection.extend
// or
girder.collections.ChallengeCollection = girder.Collection.extend({
    resourceName: 'challenge',
    // TODO
    // and here, is there any reason to create a covalic.model?
    // what if some other app wanted to use this library?
    model: girder.models.ChallengeModel,

    pageLimit: 100
});
