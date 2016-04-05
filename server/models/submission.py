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

from girder.constants import AccessType
from girder.models.model_base import Model
from girder.plugins.challenge.models.utility import validateDate
from girder.plugins.covalic import scoring
from girder.utility.progress import noProgress


class Submission(Model):
    def initialize(self):
        self.name = 'covalic_submission'
        leaderboardIdx = ([
            ('phaseId', 1), ('overallScore', -1), ('latest', 1)
        ], {})
        userPhaseIdx = ([('creatorId', 1), ('phaseId', 1)], {})
        self.ensureIndices((leaderboardIdx, userPhaseIdx, 'folderId',
                            'overallScore'))
        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'creatorId', 'creatorName', 'phaseId', 'folderId', 'created',
            'score', 'title', 'latest', 'overallScore', 'jobId'
        ))

    def validate(self, doc):
        if doc.get('created'):
            doc['created'] = validateDate(doc.get('created'), 'created')

        if doc.get('score') is not None and doc.get('overallScore') is None:
            scoring.computeAverageScores(doc['score'])
            phase = self.model('phase', 'challenge').load(
                doc['phaseId'], force=True)
            doc['overallScore'] = scoring.computeOverallScore(doc, phase)
            doc['latest'] = True

            Model.update(self, query={
                'phaseId': doc['phaseId'],
                'creatorId': doc['creatorId'],
                'latest': True
            }, update={
                '$set': {'latest': False}
            })

        return doc

    def getAllSubmissions(self, phase, filter=None):
        """
        Return a cursor of all submissions to a given phase.

        :param phase: The phase.
        :param filter: Any additional filtering rules for the result set.
        :type filter: dict
        """
        if filter is None:
            filter = {}
        filter['phaseId'] = phase['_id']

        return self.find(filter, limit=0)

    def recomputeOverallScores(self, phase):
        """
        Recompute all of the overall score values for the submissions of a
        given phase. This might be fairly expensive, so it should only be done
        if the metric identifiers or weighting values actually change.

        :param phase: The phase to recompute all submissions on.
        """
        for submission in self.getAllSubmissions(phase):
            if submission.get('score'):
                submission['overallScore'] = scoring.computeOverallScore(
                    submission, phase)
                self.save(submission, validate=False)

    def remove(self, doc, progress=noProgress):
        folder = self.model('folder').load(doc['folderId'], force=True)
        if folder:
            self.model('folder').remove(folder)

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

    def createSubmission(self, creator, phase, folder, job=None, title=None,
                         created=None):
        submission = {
            'creatorId': creator['_id'],
            'creatorName': creator['firstName'] + ' ' + creator['lastName'],
            'phaseId': phase['_id'],
            'folderId': folder['_id'],
            'created': created or datetime.datetime.utcnow(),
            'score': None,
            'title': title
        }

        if job is not None:
            submission['jobId'] = job['_id']

        return self.save(submission)
