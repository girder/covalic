import Collection from '@girder/core/collections/Collection';

import ChallengeModel from '../models/ChallengeModel';

var ChallengeCollection = Collection.extend({
    resourceName: 'challenge',
    model: ChallengeModel,
    pageLimit: 100
});

export default ChallengeCollection;
