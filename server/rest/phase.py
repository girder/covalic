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
import os

from girder.api import access
from girder.api.describe import Description
from girder.api.rest import Resource, loadmodel
from girder.constants import AccessType
from girder.plugins.celery_jobs import getCeleryUser


class Phase(Resource):
    """
    Contains additional routes for the challenge_phase resource type; they are
    bound in the load() method for this plugin.
    """

    @access.user
    @loadmodel(map={'id': 'phase'}, level=AccessType.WRITE,
               model='phase', plugin='challenge')
    @loadmodel(map={'folderId': 'folder'}, level=AccessType.ADMIN,
               model='folder')
    def postSubmission(self, phase, folder, params):
        user = self.getCurrentUser()
        title = '{} submission: {}'.format(phase['name'], folder['name'])
        apiUrl = os.path.dirname(os.path.dirname(os.path.dirname(
            cherrypy.url())))
        jobModel = self.model('job', 'jobs')

        job = jobModel.createJob(
            title=title, type='covalic_score', handler='celery', user=user)
        jobToken = jobModel.createJobToken(job)
        celeryUser = getCeleryUser()
        celeryToken =self.model('token').createToken(user=celeryUser, days=7)
        self.model('folder').setUserAccess(
            folder, user=celeryUser, level=AccessType.READ, save=True)

        if not self.model('phase', 'challenge').hasAccess(
            phase, user=celeryUser, level=AccessType.ADMIN):
                self.model('phase', 'challenge').setUserAccess(
                    phase, user=celeryUser, level=AccessType.ADMIN, save=True)

        kwargs = {
            'input': [{
                'type': 'http',
                'method': 'GET',
                'url': '/'.join((
                    apiUrl, 'folder', str(folder['_id']), 'download')),
                'headers': {'Girder-Token': celeryToken['_id']}
            }],
            'jobUpdate': {
                'type': 'http',
                'method': 'PUT',
                'url': '/'.join((apiUrl, 'job', str(job['_id']))),
                'headers': {'Girder-Token': jobToken['_id']}
            },
            'scoreTarget': {
                'type': 'http',
                'method': 'POST',
                'url': '/'.join((apiUrl, 'challenge_phase', str(phase['_id']),
                                 'score')),
                'headers': {'Girder-Token': celeryToken['_id']}
            }
        }
        job['kwargs'] = kwargs
        job = jobModel.save(job)
        jobModel.scheduleJob(job)

        return job
    postSubmission.description = (
        Description('Make a submission to the challenge.')
        .param('id', 'The ID of the challenge phase to submit to.',
               paramType='path')
        .param('folderId', 'The folder ID containing the submission data.'))

    @access.user
    @loadmodel(map={'id': 'phase'}, level=AccessType.ADMIN,
               model='phase', plugin='challenge')
    def postScore(self, phase, params):
        # TODO delete self.getCurrentToken()
        pass
    postScore.description = (
        Description('Post a score for this phase.')
        .notes('This should only be called by the scoring service, not by '
               'end users.')
        .param('id', 'The ID of the phase that was submitted to.',
               paramType='path')
        .errorResponse('ID was invalid.'))
