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
from girder.models.model_base import AccessControlledModel


class Submission(Model):
    def initialize(self):
        self.name = 'covalic_submission'
        leaderboardIdx = (('phaseId', 1), ('score._overall', -1))
        self.ensureIndices(('creatorId', 'phaseId'), ('created', -1),
                           leaderboardIdx)

    def validate(self, doc):
        return doc

    def createSubmission(self, creator, phase, folder, job=None):
        submission = {
            'creatorId': creator['_id'],
            'phaseId': phase['_id'],
            'folderId': folder['_id'],
            'created': datetime.datetime.utcnow(),
            'score': None
        }

        if job is not None:
            submission['jobId'] = job['_id']

        return self.save(submission)

    def filter(self, submission, user=None):
        # TODO filter
        return submission
