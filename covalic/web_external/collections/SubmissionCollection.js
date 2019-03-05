import { SORT_DESC } from '@girder/core/constants';
import Collection from '@girder/core/collections/Collection';

import SubmissionModel from '../models/SubmissionModel';

var SubmissionCollection = Collection.extend({
    resourceName: 'covalic_submission',
    model: SubmissionModel,

    sortField: 'overallScore',
    sortDir: SORT_DESC,
    comparator: null,

    pageLimit: 100
});

export default SubmissionCollection;
