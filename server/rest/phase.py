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

from girder.api import access
from girder.api.describe import Description
from girder.api.rest import Resource, loadmodel
from girder.constants import AccessType


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
        token = self.model('token').createToken(days=7)
        kwargs = {
            'hello': 'world'
        }
        job = self.model('job', 'jobs').createJob(
            title=title, type='covalic_score', handler='celery', user=user,
            kwargs=kwargs)

        return job
    postSubmission.description = (
        Description('Make a submission to the challenge.')
        .param('id', 'The ID of the challenge phase to submit to.',
               paramType='path')
        .param('folderId', 'The folder ID containing the submission data.'))
