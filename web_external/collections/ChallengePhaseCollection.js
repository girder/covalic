import Collection from 'girder/collections/Collection';

import PhaseModel from '../models/PhaseModel';

var ChallengePhaseCollection = Collection.extend({
    resourceName: 'challenge_phase',
    model: PhaseModel,
    pageLimit: 100,

    // Override default sort field
    sortField: 'ordinal'
});

export default ChallengePhaseCollection;
