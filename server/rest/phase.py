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


class PhaseExt(Resource):
    @access.public
    @loadmodel(map={'id': 'phase'}, model='phase', plugin='challenge',
               level=AccessType.READ)
    def groundtruthItems(self, phase, params):
        user = self.getCurrentUser()
        # All participants can see the names of the ground truth items in
        # order to validate their submissions, even if they don't have
        # read access to the folder.
        folder = self.model('folder').load(
            phase['groundTruthFolderId'], force=True)

        results = self.model('folder').childItems(folder, limit=0)
        return [{'name': item['name']} for item in results]
    groundtruthItems.description = (
        Description('List all ground truth item names for a challenge phase.')
        .param('id', 'The ID of the phase.', paramType='path'))
