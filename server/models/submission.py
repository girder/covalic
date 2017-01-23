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
from girder.models.model_base import Model, ValidationException
from girder.plugins.covalic.utility import validateDate
from girder.plugins.covalic import scoring
from girder.utility.progress import noProgress


class Submission(Model):
    @staticmethod
    def getUserName(user):
        """Get a user's full name."""
        return user['firstName'] + ' ' + user['lastName']

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
            'score', 'title', 'latest', 'overallScore', 'jobId', 'organization', 'organizationUrl',
            'documentationUrl'
        ))

    def validate(self, doc):
        if doc.get('created'):
            doc['created'] = validateDate(doc.get('created'), 'created')

        if doc.get('score') is not None and doc.get('overallScore') is None:
            scoring.computeAverageScores(doc['score'])
            phase = self.model('phase', 'covalic').load(
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

    def list(self, phase, limit=50, offset=0, sort=None, userFilter=None,
             fields=None):
        q = {'phaseId': phase['_id']}

        if userFilter is not None:
            q['creatorId'] = userFilter['_id']
        else:
            q['latest'] = True

        cursor = self.find(q, limit=limit, offset=offset, sort=sort,
                           fields=fields)
        for result in cursor:
            yield result

    def createSubmission(self, creator, phase, folder, job=None, title=None,
                         created=None, organization=None, organizationUrl=None,
                         documentationUrl=None):
        submission = {
            'creatorId': creator['_id'],
            'creatorName': self.getUserName(creator),
            'phaseId': phase['_id'],
            'folderId': folder['_id'],
            'created': created or datetime.datetime.utcnow(),
            'score': None,
            'title': title
        }

        if organization is not None:
            submission['organization'] = organization
        if organizationUrl is not None:
            submission['organizationUrl'] = organizationUrl
        if documentationUrl is not None:
            submission['documentationUrl'] = documentationUrl

        if job is not None:
            submission['jobId'] = job['_id']

        submission = self.save(submission)
        self.updateFolderAccess(phase, (submission,))
        return submission

    def updateFolderAccess(self, phase, submissions):
        """
        Synchronize access control between the phase and submission folders for
        the phase. Phase admins should have read access on the submission
        folders.
        """
        folderModel = self.model('folder')
        userModel = self.model('user')
        phaseModel = self.model('phase', 'covalic')

        # Get phase admin users
        phaseAcl = phaseModel.getFullAccessList(phase)
        phaseAdminUserIds = set([user['id']
                                 for user in phaseAcl.get('users')
                                 if user['level'] >= AccessType.WRITE])
        phaseAdminUsers = [userModel.load(userId, force=True, exc=True)
                           for userId in phaseAdminUserIds]

        # Update submission folder ACL for current phase admins
        try:
            for sub in submissions:
                folder = folderModel.load(sub['folderId'], force=True)
                if not folder:
                    continue
                folderAcl = folderModel.getFullAccessList(folder)

                # Revoke access to users who are not phase admins; ignore folder
                # owner
                usersToRemove = [userModel.load(user['id'], force=True,
                                                exc=True)
                                 for user in folderAcl.get('users')
                                 if (user['id'] not in phaseAdminUserIds and
                                     user['id'] != folder['creatorId'])]
                for user in usersToRemove:
                    folderModel.setUserAccess(folder, user, None)

                # Add access to phase admins; ignore folder owner
                usersToAdd = [user for user in phaseAdminUsers
                              if user['_id'] != folder['creatorId']]
                for user in usersToAdd:
                    folderModel.setUserAccess(folder, user, AccessType.READ)

                # Save folder if access changed
                if usersToRemove or usersToAdd:
                    folderModel.save(folder, validate=False)
        except TypeError:
            raise ValidationException('A list of submissions is required.')
