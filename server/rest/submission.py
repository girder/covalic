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

import cherrypy
import json
import os
import posixpath

from ..constants import PluginSettings
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, filtermodel, loadmodel
from girder.constants import AccessType, SortDir
from girder.models.model_base import AccessException, ValidationException
from girder.utility import mail_utils


class Submission(Resource):
    def __init__(self):
        super(Submission, self).__init__()

        self.resourceName = 'covalic_submission'

        self.route('GET', (), self.listSubmissions)
        self.route('GET', (':id',), self.getSubmission)
        self.route('GET', ('unscored',), self.getUnscoredSubmissions)
        self.route('POST', (), self.postSubmission)
        self.route('POST', (':id', 'score'), self.postScore)

    def _filterScore(self, phase, submission, user):
        """
        If the phase is configured to hide scores from participants, removes
        the relevant score fields from the document. Users with WRITE access
        or above on the phase will still be able to view the scores.
        """
        if (phase.get('hideScores') and
                not self.model('phase', 'challenge').hasAccess(
                    phase, user, level=AccessType.WRITE)):
            submission.pop('score', None)
            submission.pop('overallScore', None)
        return submission

    @access.public
    @loadmodel(map={'phaseId': 'phase'}, model='phase', plugin='challenge',
               level=AccessType.READ)
    @filtermodel(model='submission', plugin='covalic')
    @describeRoute(
        Description('List submissions to a challenge phase.')
        .param('phaseId', 'The ID of the phase.')
        .param('userId', 'Show only results for the given user.',
               required=False)
        .param('limit', "Result set size limit (default=50).", required=False,
               dataType='int')
        .param('offset', "Offset into result set (default=0).", required=False,
               dataType='int')
        .param('sort', 'Field to sort the result list by ('
               'default=overallScore)', required=False)
        .param('sortdir', "1 for ascending, -1 for descending (default=-1)",
               required=False, dataType='int')
    )
    def listSubmissions(self, phase, params):
        limit, offset, sort = self.getPagingParameters(
            params, 'overallScore', defaultSortDir=SortDir.DESCENDING)
        userFilter = None
        user = self.getCurrentUser()

        # If scores are hidden, do not allow sorting by score fields
        if (phase.get('hideScores') and
                not self.model('phase', 'challenge').hasAccess(
                    phase, user, AccessType.WRITE)):
            for field, _ in sort:
                if field == 'overallScore' or field.startswith('score.'):
                    raise AccessException(
                        'Scores are hidden from participants in this phase, '
                        'you may not sort by score fields.')

        if 'userId' in params:
            userFilter = self.model('user').load(
                params['userId'], user=user, level=AccessType.READ)

        submissions = self.model('submission', 'covalic').list(
            phase, limit=limit, offset=offset, sort=sort, userFilter=userFilter)
        return [self._filterScore(phase, s, user) for s in submissions]

    @access.user
    @loadmodel(map={'phaseId': 'phase'}, model='phase', plugin='challenge',
               level=AccessType.READ)
    @loadmodel(map={'folderId': 'folder'}, model='folder',
               level=AccessType.ADMIN)
    @filtermodel(model='submission', plugin='covalic')
    @describeRoute(
        Description('Make a submission to the challenge.')
        .param('phaseId', 'The ID of the challenge phase to submit to.')
        .param('folderId', 'The folder ID containing the submission data.')
        .param('title', 'Title for the submission')
        .errorResponse('You are not a member of the participant group.', 403)
        .errorResponse('The ID was invalid.')
    )
    def postSubmission(self, phase, folder, params):
        user = self.getCurrentUser()

        if not phase.get('active') and (not user or not user.get('admin')):
            raise ValidationException('You may not submit to this phase '
                                      'because it is not currently active.')

        self.requireParams('title', params)

        # Only users in the participant group (or with write access) may submit
        if phase['participantGroupId'] not in user['groups']:
            self.model('phase', 'challenge').requireAccess(
                phase, user, level=AccessType.WRITE)

        jobTitle = '%s submission: %s' % (phase['name'], folder['name'])
        apiUrl = os.path.dirname(cherrypy.url())
        jobModel = self.model('job', 'jobs')

        job = jobModel.createJob(
            title=jobTitle, type='covalic_score', handler='worker_handler',
            user=user)
        jobToken = jobModel.createJobToken(job)
        scoreUserId = self.model('setting').get(PluginSettings.SCORING_USER_ID)

        if not scoreUserId:
            raise Exception('No scoring user ID is set. Please set one on the '
                            'plugin configuration page.')
        scoreUser = self.model('user').load(scoreUserId, force=True)

        if not scoreUser:
            raise Exception('Invalid scoring user setting (%s).' % scoreUserId)

        scoreToken = self.model('token').createToken(user=scoreUser, days=7)
        self.model('folder').setUserAccess(
            folder, user=scoreUser, level=AccessType.READ, save=True)

        groundTruth = self.model('folder').load(phase['groundTruthFolderId'],
                                                force=True)

        title = params['title'].strip()
        submission = self.model('submission', 'covalic').createSubmission(
            user, phase, folder, job, title)

        if not self.model('phase', 'challenge').hasAccess(
                phase, user=scoreUser, level=AccessType.ADMIN):
            self.model('phase', 'challenge').setUserAccess(
                phase, user=scoreUser, level=AccessType.ADMIN, save=True)

        if not self.model('folder').hasAccess(
                groundTruth, user=scoreUser, level=AccessType.READ):
            self.model('folder').setUserAccess(
                groundTruth, user=scoreUser, level=AccessType.READ,
                save=True)

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
                    'format': 'string',
                    'target': 'filepath',
                    'filename': 'submission.zip'
                }, {
                    'id': 'groundtruth',
                    'type': 'string',
                    'format': 'string',
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
                'submission': {
                    'mode': 'http',
                    'method': 'GET',
                    'url': '/'.join((
                        apiUrl, 'folder', str(folder['_id']), 'download')),
                    'headers': {'Girder-Token': scoreToken['_id']}
                },
                'groundtruth': {
                    'mode': 'http',
                    'method': 'GET',
                    'url': '/'.join((
                        apiUrl, 'folder', str(groundTruth['_id']),
                        'download')),
                    'headers': {'Girder-Token': scoreToken['_id']}
                }
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
            'jobInfo': {
                'method': 'PUT',
                'url': '/'.join((apiUrl, 'job', str(job['_id']))),
                'headers': {'Girder-Token': jobToken['_id']},
                'logPrint': True
            },
            'validate': False,
            'auto_convert': False,
            'cleanup': True
        }
        job['kwargs'] = kwargs
        job['covalicSubmissionId'] = submission['_id']
        job = jobModel.save(job)
        jobModel.scheduleJob(job)

        return self._filterScore(phase, submission, user)

    @access.user
    @loadmodel(model='submission', plugin='covalic')
    @describeRoute(
        Description('Post a score for a given submission.')
        .notes('This should only be called by the scoring service, not by '
               'end users.')
        .param('id', 'The ID of the submission being scored.', paramType='path')
        .param('body', 'The JSON object containing the scores for this '
               'submission.', paramType='body')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the challenge phase.', 403)
    )
    def postScore(self, submission, params):
        # Ensure admin access on the containing challenge phase
        phase = self.model('phase', 'challenge').load(
            submission['phaseId'], user=self.getCurrentUser(), exc=True,
            level=AccessType.ADMIN)

        submission['score'] = json.loads(cherrypy.request.body.read())
        submission = self.model('submission', 'covalic').save(submission)

        # Delete the scoring user's job token since the job is now complete.
        token = self.getCurrentToken()
        self.model('token').remove(token)

        user = self.model('user').load(submission['creatorId'], force=True)
        challenge = self.model('challenge', 'challenge').load(
            phase['challengeId'], force=True)
        covalicHost = posixpath.dirname(mail_utils.getEmailUrlPrefix())
        html = mail_utils.renderTemplate('covalic.submissionComplete.mako', {
            'phase': phase,
            'challenge': challenge,
            'submission': submission,
            'host': covalicHost
        })
        mail_utils.sendEmail(
            to=user['email'], subject='Your submission has been scored',
            text=html)

        return submission

    @access.public
    @loadmodel(model='submission', plugin='covalic')
    @filtermodel(model='submission', plugin='covalic')
    @describeRoute(
        Description('Retrieve a single submission.')
        .param('id', 'The ID of the submission.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the challenge phase.', 403)
    )
    def getSubmission(self, submission, params):
        # Ensure read access on the containing challenge phase
        user = self.getCurrentUser()
        phase = self.model('phase', 'challenge').load(
            submission['phaseId'], user=user, exc=True, level=AccessType.READ)

        return self._filterScore(phase, submission, user)

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.ADMIN)
    def getUnscoredSubmissions(self, params):
        # TODO implement
        pass
    getUnscoredSubmissions.description = (
        Description('List unscored submissions for a given phase.')
        .param('phaseId', 'The ID of the phase.')
        .param('limit', "Result set size limit (default=50).", required=False,
               dataType='int')
        .param('offset', "Offset into result set (default=0).", required=False,
               dataType='int')
        .param('sort', 'Field to sort the result list by (default=created)',
               required=False)
        .errorResponse('Phase ID was invalid.')
        .errorResponse('Admin access was denied for the challenge phase.', 403))
