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
import pymongo

from girder.api import access
from girder.api.describe import Description
from girder.api.rest import Resource, loadmodel
from girder.constants import AccessType
from girder.models.model_base import ValidationException
from girder.plugins.celery_jobs import getCeleryUser


class Submission(Resource):
    def __init__(self):
        self.resourceName = 'covalic_submission'

        self.route('GET', (), self.listSubmissions)
        self.route('GET', (':id',), self.getSubmission)
        self.route('GET', ('unscored',), self.getUnscoredSubmissions)
        self.route('POST', (), self.postSubmission)
        self.route('POST', (':id', 'score'), self.postScore)

    @access.public
    @loadmodel(map={'phaseId': 'phase'}, model='phase', plugin='challenge',
               level=AccessType.READ)
    def listSubmissions(self, phase, params):
        limit, offset, sort = self.getPagingParameters(
            params, 'overallScore', defaultSortDir=pymongo.DESCENDING)

        userFilter = None
        if 'userId' in params:
            userFilter = self.model('user').load(
                params['userId'], user=self.getCurrentUser(),
                level=AccessType.READ)

        results = self.model('submission', 'covalic').list(
            phase, limit=limit, offset=offset, sort=sort, userFilter=userFilter)
        return [self.model('submission', 'covalic').filter(s) for s in results]
    listSubmissions.description = (
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
               required=False, dataType='int'))

    @access.user
    @loadmodel(map={'phaseId': 'phase'}, model='phase', plugin='challenge',
               level=AccessType.READ)
    @loadmodel(map={'folderId': 'folder'}, model='folder',
               level=AccessType.ADMIN)
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

        jobTitle = '{} submission: {}'.format(phase['name'], folder['name'])
        apiUrl = os.path.dirname(cherrypy.url())
        jobModel = self.model('job', 'jobs')

        job = jobModel.createJob(
            title=jobTitle, type='covalic_score', handler='celery', user=user)
        jobToken = jobModel.createJobToken(job)
        celeryUser = getCeleryUser()
        celeryToken = self.model('token').createToken(user=celeryUser, days=7)
        self.model('folder').setUserAccess(
            folder, user=celeryUser, level=AccessType.READ, save=True)

        groundTruth = self.model('folder').load(phase['groundTruthFolderId'],
                                                force=True)

        title = params['title'].strip()
        submission = self.model('submission', 'covalic').createSubmission(
            user, phase, folder, job, title)

        if not self.model('phase', 'challenge').hasAccess(
                phase, user=celeryUser, level=AccessType.ADMIN):
            self.model('phase', 'challenge').setUserAccess(
                phase, user=celeryUser, level=AccessType.ADMIN, save=True)

        if not self.model('folder').hasAccess(
                groundTruth, user=celeryUser, level=AccessType.READ):
            self.model('folder').setUserAccess(
                groundTruth, user=celeryUser, level=AccessType.READ,
                save=True)

        kwargs = {
            'input': {
                'submission': {
                    'type': 'http',
                    'method': 'GET',
                    'url': '/'.join((
                        apiUrl, 'folder', str(folder['_id']), 'download')),
                    'headers': {'Girder-Token': celeryToken['_id']}
                },
                'ground_truth': {
                    'type': 'http',
                    'method': 'GET',
                    'url': '/'.join((
                        apiUrl, 'folder', str(groundTruth['_id']), 'download')),
                    'headers': {'Girder-Token': celeryToken['_id']}
                }
            },
            'jobUpdate': {
                'type': 'http',
                'method': 'PUT',
                'url': '/'.join((apiUrl, 'job', str(job['_id']))),
                'headers': {'Girder-Token': jobToken['_id']}
            },
            'scoreTarget': {
                'type': 'http',
                'method': 'POST',
                'url': '/'.join((apiUrl, 'covalic_submission',
                                 str(submission['_id']), 'score')),
                'headers': {'Girder-Token': celeryToken['_id']}
            },
            'cleanup': True
        }
        job['kwargs'] = kwargs
        job['covalicSubmissionId'] = submission['_id']
        job = jobModel.save(job)
        jobModel.scheduleJob(job)

        return submission
    postSubmission.description = (
        Description('Make a submission to the challenge.')
        .param('phaseId', 'The ID of the challenge phase to submit to.')
        .param('folderId', 'The folder ID containing the submission data.')
        .param('title', 'Title for the submission')
        .errorResponse('You are not a member of the participant group.', 403)
        .errorResponse('The ID was invalid.'))

    @access.user
    @loadmodel(model='submission', plugin='covalic')
    def postScore(self, submission, params):
        # Ensure admin access on the containing challenge phase
        self.model('phase', 'challenge').load(
            submission['phaseId'], user=self.getCurrentUser(), exc=True,
            level=AccessType.ADMIN)

        submission['score'] = json.loads(cherrypy.request.body.read())
        submission = self.model('submission', 'covalic').save(submission)

        # Delete the celery user's job token since the job is now complete.
        token = self.getCurrentToken()
        self.model('token').remove(token)

        return submission
    postScore.description = (
        Description('Post a score for a given submission.')
        .notes('This should only be called by the scoring service, not by '
               'end users.')
        .param('id', 'The ID of the submission being scored.', paramType='path')
        .param('body', 'The JSON object containing the scores for this '
               'submission.', paramType='body')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the challenge phase.', 403))

    @access.public
    @loadmodel(model='submission', plugin='covalic')
    def getSubmission(self, submission, params):
        # Ensure read access on the containing challenge phase
        self.model('phase', 'challenge').load(
            submission['phaseId'], user=self.getCurrentUser(), exc=True,
            level=AccessType.READ)

        return self.model('submission', 'covalic').filter(submission)
    getSubmission.description = (
        Description('Retrieve a single submission.')
        .param('id', 'The ID of the submission.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied for the challenge phase.', 403))

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.ADMIN)
    def getUnscoredSubmissions(self, params):
        pass
    getUnscoredSubmissions.description = (
        Description('List unscored submissions for a given phase.')
        .param('phaseId', 'The ID of the phase.')
        .errorResponse('Phase ID was invalid.')
        .errorResponse('Admin access was denied for the challenge phase.', 403))
