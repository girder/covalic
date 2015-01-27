#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import datetime

from girder.models.model_base import Model
from girder.plugins.covalic import scoring
from girder.utility.progress import noProgress


class Submission(Model):
    def initialize(self):
        self.name = 'covalic_submission'
        leaderboardIdx = ([
            ('phaseId', 1), ('overallScore', -1), ('latest', 1)
        ], {})
        userPhaseIdx = ([('creatorId', 1), ('phaseId', 1)], {})
        self.ensureIndices((leaderboardIdx, userPhaseIdx, 'folderId'))

    def validate(self, doc):
        if doc.get('score') is not None:
            scoring.computeAverageScores(doc['score'])
            doc['overallScore'] = scoring.computeOverallScore(doc['score'])
            doc['latest'] = True

            Model.update(self, query={
                'phaseId': doc['phaseId'],
                'creatorId': doc['creatorId'],
                'latest': True
            }, update={
                '$set': {'latest': False}
            })

        return doc

    def remove(self, doc, progress=noProgress):
        # TODO delete folders and stuff...?
        Model.remove(self, doc, progress=progress)

    def list(self, phase, limit=50, offset=0, sort=None, userFilter=None):
        q = {'phaseId': phase['_id']}

        if userFilter is not None:
            q['creatorId'] = userFilter['_id']
        else:
            q['latest'] = True

        cursor = self.find(q, limit=limit, offset=offset, sort=sort)
        for result in cursor:
            yield result

    def createSubmission(self, creator, phase, folder, job=None, title=None):
        submission = {
            'creatorId': creator['_id'],
            'creatorName': creator['firstName'] + ' ' + creator['lastName'],
            'phaseId': phase['_id'],
            'folderId': folder['_id'],
            'created': datetime.datetime.utcnow(),
            'score': None,
            'title': title
        }

        if job is not None:
            submission['jobId'] = job['_id']

        return self.save(submission)

    def filter(self, submission, user=None):
        # TODO filter
        return submission
