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
from girder.exceptions import GirderException
from girder.models.model_base import Model, ValidationException
from girder.plugins.covalic.utility import validateDate
from girder.plugins.covalic import scoring
from girder.plugins.worker import utils
from girder.utility.progress import noProgress

from ..constants import PluginSettings


class Submission(Model):
    @staticmethod
    def getUserName(user):
        """Get a user's full name."""
        return user['firstName'] + ' ' + user['lastName']

    def initialize(self):
        self.name = 'covalic_submission'
        leaderboardIdx = ([
            ('phaseId', 1), ('overallScore', -1), ('approach', 1), ('latest', 1)
        ], {})
        userPhaseIdx = ([('creatorId', 1), ('phaseId', 1), ('approach', 1)], {})
        self.ensureIndices((leaderboardIdx, userPhaseIdx, 'folderId',
                            'overallScore', 'approach'))
        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'creatorId', 'creatorName', 'phaseId', 'folderId', 'created',
            'score', 'title', 'latest', 'overallScore', 'jobId', 'organization', 'organizationUrl',
            'documentationUrl', 'approach', 'meta'
        ))

    def load(self, *args, **kwargs):
        doc = super(Submission, self).load(*args, **kwargs)
        fields = kwargs.get('fields')
        if (fields is None or 'approach' in fields) and \
                doc is not None and doc.get('approach') is None:
            doc['approach'] = 'default'
        if doc is not None:
            doc.setdefault('meta', {})
        return doc

    def save(self, document, *args, **kwargs):
        document = super(Submission, self).save(document, *args, **kwargs)
        document.setdefault('approach', 'default')
        document.setdefault('meta', {})
        return document

    def validate(self, doc):
        if doc.get('created'):
            doc['created'] = validateDate(doc.get('created'), 'created')

        if doc.get('approach') in {'default', ''}:
            del doc['approach']

        if doc.get('score') is not None and doc.get('overallScore') is None:
            scoring.computeAverageScores(doc['score'])
            phase = self.model('phase', 'covalic').load(
                doc['phaseId'], force=True)
            doc['overallScore'] = scoring.computeOverallScore(doc, phase)
            doc['latest'] = True

            Model.update(self, query={
                'phaseId': doc['phaseId'],
                'creatorId': doc['creatorId'],
                'approach': doc.get('approach'),
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
             fields=None, latest=True, approach=None):
        q = {'phaseId': phase['_id']}

        if userFilter is not None:
            q['creatorId'] = userFilter['_id']
        elif latest:
            q['latest'] = True

        if approach is not None:
            q['approach'] = approach
            if approach in {'default', ''}:
                q['approach'] = None

        cursor = self.find(q, limit=limit, offset=offset, sort=sort,
                           fields=fields)
        for result in cursor:
            result.setdefault('approach', 'default')
            yield result

    def listApproaches(self, phase=None, user=None):
        q = {}
        if phase is not None:
            q['phaseId'] = phase['_id']

        if user is not None:
            q['creatorId'] = user['_id']

        approaches = [
            approach for approach in self.collection.distinct('approach', filter=q)
            if approach is not None
        ]
        approaches.append('default')
        return sorted(set(approaches))

    def createSubmission(self, creator, phase, folder, job=None, title=None,
                         created=None, organization=None, organizationUrl=None,
                         documentationUrl=None, approach=None, meta=None):
        submission = {
            'creatorId': creator['_id'],
            'creatorName': self.getUserName(creator),
            'phaseId': phase['_id'],
            'folderId': folder['_id'],
            'created': created or datetime.datetime.utcnow(),
            'score': None,
            'title': title,
            'meta': meta or {}
        }

        if organization is not None:
            submission['organization'] = organization
        if organizationUrl is not None:
            submission['organizationUrl'] = organizationUrl
        if documentationUrl is not None:
            submission['documentationUrl'] = documentationUrl
        if approach is not None:
            submission['approach'] = approach

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

    def scoreSubmission(self, submission, apiUrl):
        """
        Run a Girder Worker job to score a submission.
        """
        folderModel = self.model('folder')
        jobModel = self.model('job', 'jobs')
        phaseModel = self.model('phase', 'covalic')
        settingModel = self.model('setting')
        tokenModel = self.model('token')
        userModel = self.model('user')

        phase = phaseModel.load(submission['phaseId'], force=True)
        folder = folderModel.load(submission['folderId'], force=True)
        user = userModel.load(submission['creatorId'], force=True)

        jobTitle = '%s submission: %s' % (phase['name'], folder['name'])
        job = jobModel.createJob(
            title=jobTitle, type='covalic_score', handler='worker_handler', user=user)

        scoreUserId = settingModel.get(PluginSettings.SCORING_USER_ID)
        if not scoreUserId:
            raise GirderException(
                'No scoring user ID is set. Please set one on the plugin configuration page.')

        scoreUser = userModel.load(scoreUserId, force=True)
        if not scoreUser:
            raise GirderException('Invalid scoring user setting (%s).' % scoreUserId)

        scoreToken = tokenModel.createToken(user=scoreUser, days=7)
        folderModel.setUserAccess(
            folder, user=scoreUser, level=AccessType.READ, save=True)

        groundTruth = folderModel.load(phase['groundTruthFolderId'], force=True)

        if not phaseModel.hasAccess(phase, user=scoreUser, level=AccessType.ADMIN):
            phaseModel.setUserAccess(
                phase, user=scoreUser, level=AccessType.ADMIN, save=True)

        if not folderModel.hasAccess(groundTruth, user=scoreUser, level=AccessType.READ):
            folderModel.setUserAccess(
                groundTruth, user=scoreUser, level=AccessType.READ, save=True)

        task = phase.get('scoreTask', {})
        image = task.get('dockerImage') or 'girder/covalic-metrics:latest'
        containerArgs = task.get('dockerArgs') or [
            '--groundtruth=$input{groundtruth}',
            '--submission=$input{submission}'
        ]

        kwargs = {
            'task': {
                'name': jobTitle,
                'mode': 'docker',
                'docker_image': image,
                'container_args': containerArgs,
                'inputs': [{
                    'id': 'submission',
                    'type': 'string',
                    'format': 'text',
                    'target': 'filepath',
                    'filename': 'submission.zip'
                }, {
                    'id': 'groundtruth',
                    'type': 'string',
                    'format': 'text',
                    'target': 'filepath',
                    'filename': 'groundtruth.zip'
                }],
                'outputs': [{
                    'id': '_stdout',
                    'format': 'string',
                    'type': 'string'
                }]
            },
            'inputs': {
                'submission': utils.girderInputSpec(
                    folder, 'folder', token=scoreToken),
                'groundtruth': utils.girderInputSpec(
                    groundTruth, 'folder', token=scoreToken)
            },
            'outputs': {
                '_stdout': {
                    'mode': 'http',
                    'method': 'POST',
                    'format': 'string',
                    'url': '/'.join((apiUrl, 'covalic_submission',
                                     str(submission['_id']), 'score')),
                    'headers': {'Girder-Token': scoreToken['_id']}
                }
            },
            'jobInfo': utils.jobInfoSpec(job),
            'validate': False,
            'auto_convert': False,
            'cleanup': True
        }
        job['kwargs'] = kwargs
        job['covalicSubmissionId'] = submission['_id']
        job = jobModel.save(job)
        jobModel.scheduleJob(job)

        submission['jobId'] = job['_id']
        return self.save(submission, validate=False)
