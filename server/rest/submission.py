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
import math
import os
import posixpath

from ..constants import PluginSettings
from ..utility.user_emails import getPhaseUserEmails
from ..models.phase import Phase
from ..models.submission import Submission
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute, describeRoute
from girder.api.rest import Resource, filtermodel, loadmodel
from girder.constants import AccessType, SortDir
from girder.models.model_base import AccessException, ValidationException
from girder.models.folder import Folder
from girder.plugins.worker import utils
from girder.utility import mail_utils


class Submission(Resource):
    def __init__(self):
        super(Submission, self).__init__()

        self.resourceName = 'covalic_submission'

        self.route('GET', (), self.listSubmissions)
        self.route('GET', ('approaches',), self.listUserApproaches)
        self.route('GET', (':id',), self.getSubmission)
        self.route('GET', ('unscored',), self.getUnscoredSubmissions)
        self.route('POST', (), self.postSubmission)
        self.route('PUT', (':id',), self.updateSubmission)
        self.route('POST', (':id', 'score'), self.postScore)
        self.route('DELETE', (':id',), self.deleteSubmission)

    def _filterScore(self, phase, submission, user):
        """
        If the phase is configured to hide scores from participants, removes
        the relevant score fields from the document. Users with WRITE access
        or above on the phase will still be able to view the scores.

        Additionally, ensures that any NaN or Infinity score values are coerced
        to corresponding strings so they can be JSON encoded.
        """
        if (phase.get('hideScores') and
                not self.model('phase', 'covalic').hasAccess(
                    phase, user, level=AccessType.WRITE)):
            submission.pop('score', None)
            submission.pop('overallScore', None)
        else:
            # coerce any nans or infs to strings
            for dataset in (submission.get('score') or ()):
                for metric in dataset['metrics']:
                    if metric['value'] is not None:
                        v = float(metric['value'])
                        if math.isnan(v) or math.isinf(v):
                            metric['value'] = str(v)
            v = submission.get('overallScore') or 0
            if math.isnan(v) or math.isinf(v):
                submission['overallScore'] = str(v)

        return submission

    def _checkRequireParam(self, phase, params, paramName, requireOptionName):
        """
        Require a parameter conditionally, based on a phase property.

        :param phase: The phase.
        :param params: Parameters.
        :param paramName: Parameter name.
        :param requireOptionName: Phase property that indicates whether the parameter is required.
        """
        if phase.get(requireOptionName, False):
            self.requireParams(paramName, params)

    def _getStrippedParam(self, params, name):
        """
        Return the stripped parameter, or None if the parameter doesn't exist.

        :param params: Parameters.
        :param name: Parameter name.
        :return: The stripped parameter, or None.
        """
        param = params.get(name)
        if param is not None:
            param = param.strip()
        return param

    @access.public
    @filtermodel(model='submission', plugin='covalic')
    @autoDescribeRoute(
        Description('List submissions to a challenge phase.')
        .modelParam('phaseId', 'The ID of the phase.', model='phase', plugin='covalic',
                    paramType='query', level=AccessType.READ)
        .modelParam('userId', 'Show only results for the given user.', model='user',
                    paramType='query', level=AccessType.READ, required=False, destName='userFilter')
        .param('latest', 'Only include the latest scored submission for each user.',
               required=False, dataType='boolean', default=True)
        .param('approach', 'Only include this approach in the results',
               required=False)
        .pagingParams(defaultSort='overallScore', defaultSortDir=SortDir.DESCENDING)
    )
    def listSubmissions(self, phase, userFilter, latest, limit, offset, sort, approach):
        user = self.getCurrentUser()

        # If scores are hidden, do not allow sorting by score fields
        if (phase.get('hideScores') and
                not self.model('phase', 'covalic').hasAccess(
                    phase, user, AccessType.WRITE)):
            for field, _ in sort:
                if field == 'overallScore' or field.startswith('score.'):
                    raise AccessException(
                        'Scores are hidden from participants in this phase, '
                        'you may not sort by score fields.')

        # Exclude score field
        fields = {'score': False}

        submissions = self.model('submission', 'covalic').list(
            phase, limit=limit, offset=offset, sort=sort, userFilter=userFilter,
            fields=fields, latest=latest, approach=approach)
        return [self._filterScore(phase, s, user) for s in submissions]

    @access.user
    @autoDescribeRoute(
        Description('List existing approaches for the current user.')
        .modelParam('phaseId', 'Show only approaches used in this phase',
                    model='phase', plugin='covalic', paramType='query',
                    level=AccessType.READ, required=False, destName='phase')
        .modelParam('userId', 'Show approaches used by this user (default: current user)',
                    model='user', paramType='query', level=AccessType.READ,
                    destName='user', required=False)
    )
    def listUserApproaches(self, phase, user):
        currentUser = self.getCurrentUser()
        if user is None:
            user = currentUser

        if user['_id'] != currentUser['_id']:
            self.requireAdmin(currentUser, 'Only admins can see other user\'s approaches.')

        return self.model('submission', 'covalic').listApproaches(phase=phase, user=user)

    @access.user
    @filtermodel(model=Submission)
    @autoDescribeRoute(
        Description('Make a submission to the challenge.')
        .modelParam('phaseId', 'The ID of the challenge phase to submit to.',
                    model=Phase, level=AccessType.READ, paramType='query',
                    destName='phase')
        .modelParam('folderId', 'The folder ID containing the submission data.',
                    model=Folder, level=AccessType.ADMIN, paramType='query',
                    destName='folder')
        .param('title', 'Title for the submission')
        .param('date', 'The date of the submission.', required=False)
        .param('userId', 'The ID of the user to submit on behalf of.',
               required=False)
        .param('organization', 'Organization associated with the submission.', required=False)
        .param('organizationUrl', 'URL for organization associated with the submission.',
               required=False)
        .param('documentationUrl', 'URL of documentation associated with the submission.',
               required=False)
        .param('approach', 'The submission approach.', required=False)
        .jsonParam('meta', 'A JSON object containing additional submission metadata.',
                   paramType='form', requireObject=True, required=False)
        .errorResponse('You are not a member of the participant group.', 403)
        .errorResponse('The ID was invalid.')
    )
    def postSubmission(self, phase, folder, **params):
        user = self.getCurrentUser()

        if not phase.get('active') and (not user or not user.get('admin')):
            raise ValidationException('You may not submit to this phase '
                                      'because it is not currently active.')

        self.requireParams('title', params)

        # Only users in the participant group (or with write access) may submit
        if phase['participantGroupId'] not in user['groups']:
            self.model('phase', 'covalic').requireAccess(
                phase, user, level=AccessType.WRITE)

        # Require optional fields that are enabled in phase
        organization = None
        organizationUrl = None
        documentationUrl = None
        if phase.get('enableOrganization', False):
            self._checkRequireParam(phase, params, 'organization', 'requireOrganization')
            organization = self._getStrippedParam(params, 'organization')
        if phase.get('enableOrganizationUrl', False):
            self._checkRequireParam(phase, params, 'organizationUrl', 'requireOrganizationUrl')
            organizationUrl = self._getStrippedParam(params, 'organizationUrl')
        if phase.get('enableDocumentationUrl', False):
            self._checkRequireParam(phase, params, 'documentationUrl', 'requireDocumentationUrl')
            documentationUrl = self._getStrippedParam(params, 'documentationUrl')

        approach = self._getStrippedParam(params, 'approach')

        # Site admins may override the submission creation date
        created = None
        if params['date'] is not None:
            self.requireAdmin(user, 'Administrator access required to override '
                                    'the submission creation date.')
            created = params['date']

        # Site admins may submit on behalf of another user
        if params['userId'] is not None:
            self.requireAdmin(user, 'Administrator access required to submit '
                                    'to this phase on behalf of another user.')
            user = self.model('user').load(params['userId'], force=True,
                                           exc=True)

        jobTitle = '%s submission: %s' % (phase['name'], folder['name'])
        apiUrl = os.path.dirname(cherrypy.url())
        jobModel = self.model('job', 'jobs')

        job = jobModel.createJob(
            title=jobTitle, type='covalic_score', handler='worker_handler',
            user=user)
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
            user, phase, folder, job, title, created, organization, organizationUrl,
            documentationUrl, approach, params.get('meta'))

        if not self.model('phase', 'covalic').hasAccess(
                phase, user=scoreUser, level=AccessType.ADMIN):
            self.model('phase', 'covalic').setUserAccess(
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

        return self._filterScore(phase, submission, user)

    @access.user
    @filtermodel(model=Submission)
    @autoDescribeRoute(
        Description('Overwrite the properties of a submission.')
        .modelParam('id', 'The ID of the challenge phase to submit to.',
                    model=Submission, paramType='path', destName='submission')
        .param('title', 'Title for the submission', required=False)
        .param('date', 'The date of the submission.', required=False)
        .param('organization', 'Organization associated with the submission.',
               required=False)
        .param('organizationUrl', 'URL for organization associated with the submission.',
               required=False)
        .param('documentationUrl', 'URL of documentation associated with the submission.',
               required=False)
        .param('disqualified', 'Whether the submission is disqualified. Disqualified '
               'submissions do not appear in the leaderboard.', dataType='boolean', required=False)
        .param('approach', 'The submission approach.', required=False)
        .jsonParam('meta', 'A JSON object containing additional submission metadata. '
                   'If present, replaces the existing metadata.',
                   paramType='form', requireObject=True, required=False)
        .errorResponse('ID was invalid.')
        .errorResponse('Write access to phase is required.', 403)
    )
    def updateSubmission(self, submission, **params):
        # Ensure write access on the containing challenge phase
        user = self.getCurrentUser()
        phase = self.model('phase', 'covalic').load(
            submission['phaseId'], user=user, exc=True, level=AccessType.WRITE)

        title = self._getStrippedParam(params, 'title')
        if title is not None:
            submission['title'] = title
        created = self._getStrippedParam(params, 'date')
        if created is not None:
            submission['created'] = created
        # Since only admins may use this endpoint, skip the normal checks for
        # 'enableOrganization', etc.
        organization = self._getStrippedParam(params, 'organization')
        if organization is not None:
            submission['organization'] = organization
        organizationUrl = self._getStrippedParam(params, 'organizationUrl')
        if organizationUrl is not None:
            submission['organizationUrl'] = organizationUrl
        documentationUrl = self._getStrippedParam(params, 'documentationUrl')
        if documentationUrl is not None:
            submission['documentationUrl'] = documentationUrl
        approach = self._getStrippedParam(params, 'approach')
        if approach is not None:
            submission['approach'] = approach
        meta = params.get('meta')
        if meta is not None:
            submission['meta'] = meta

        # Note that this does not enforce the requirement that only a single submission
        # per user per phase is marked as the 'latest' submission. If access to this endpoint
        # is expanded beyond admin users, then that requirement should be enforced.
        disqualified = params['disqualified']
        if disqualified is not None:
            submission['latest'] = not disqualified

        submission = self.model('submission', 'covalic').save(submission)

        return self._filterScore(phase, submission, user)

    @access.user
    @autoDescribeRoute(
        Description('Post a score for a given submission.')
        .modelParam('id', model='submission', plugin='covalic')
        .jsonParam(
            'score', 'The JSON object containing the scores for this submission.',
            paramType='body',
            schema={
                "$schema": "http://json-schema.org/schema#",
                'type': 'array',
                'items': {'$ref': '#/definitions/score'},
                'definitions': {
                    'score': {
                        'type': 'object',
                        'properties': {
                            'dataset': {'type': 'string'},
                            'metrics': {
                                'type': 'array',
                                'items': {'$ref': '#/definitions/metric'}
                            }
                        },
                        'required': ['dataset', 'metrics']
                    },
                    'metric': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'value': {'type': ['null', 'number', 'string']}
                        },
                        'required': ['name', 'value']
                    }
                }
            })
        .notes('This should only be called by the scoring service, not by '
               'end users.')
        .errorResponse(('ID was invalid.',
                        'Invalid JSON passed in request body.'))
        .errorResponse('Admin access was denied for the challenge phase.', 403)
    )
    def postScore(self, submission, score, params):
        # Ensure admin access on the containing challenge phase
        phase = self.model('phase', 'covalic').load(
            submission['phaseId'], user=self.getCurrentUser(), exc=True,
            level=AccessType.ADMIN)

        submission['score'] = score
        submission = self.model('submission', 'covalic').save(submission)

        # Delete the scoring user's job token since the job is now complete.
        token = self.getCurrentToken()
        self.model('token').remove(token)

        user = self.model('user').load(submission['creatorId'], force=True)
        challenge = self.model('challenge', 'covalic').load(
            phase['challengeId'], force=True)
        covalicHost = posixpath.dirname(mail_utils.getEmailUrlPrefix())

        # Mail user
        html = mail_utils.renderTemplate(
            'covalic.submissionCompleteUser.mako',
            {
                'phase': phase,
                'challenge': challenge,
                'submission': submission,
                'host': covalicHost
            })
        mail_utils.sendEmail(
            to=user['email'], subject='Your submission has been scored',
            text=html)

        # Mail admins
        emails = sorted(getPhaseUserEmails(
            phase, AccessType.WRITE, includeChallengeUsers=True))
        html = mail_utils.renderTemplate(
            'covalic.submissionCompleteAdmin.mako',
            {
                'user': user,
                'phase': phase,
                'challenge': challenge,
                'submission': submission,
                'host': covalicHost
            })
        mail_utils.sendEmail(
            to=emails, subject='A submission has been scored', text=html)

        return self._filterScore(phase, submission, user)

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
        phase = self.model('phase', 'covalic').load(
            submission['phaseId'], user=user, exc=True, level=AccessType.READ)

        return self._filterScore(phase, submission, user)

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.ADMIN)
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

    @access.user
    @loadmodel(model='submission', plugin='covalic')
    @describeRoute(
        Description('Remove a submission to a phase.')
        .notes('You must be either the owner of the submission, or have write '
               'access to the phase of the submission.')
        .param('id', 'The ID of the submission.', paramType='path')
    )
    def deleteSubmission(self, submission, params):
        user = self.getCurrentUser()
        phase = self.model('phase', 'covalic').load(submission['phaseId'],
                                                    force=True)
        if (user['_id'] == submission['creatorId'] or
                self.model('phase', 'covalic').hasAccess(
                    phase, user, AccessType.WRITE)):
            self.model('submission', 'covalic').remove(submission)
        else:
            raise AccessException(
                'You may only remove submissions that you made, or those under '
                'phases that you have permission to edit.')
