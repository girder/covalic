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
    @loadmodel(model='phase', plugin='challenge', level=AccessType.READ)
    def groundtruthItems(self, phase, params):
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

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.WRITE)
    def setMetrics(self, phase, params):
        phaseModel = self.model('phase', 'challenge')
        user = self.getCurrentUser()

        oldMetrics = phase.get('metrics', {})

        if 'copyFrom' in params:
            srcPhase = self.model('phase', 'challenge').load(
                params['copyFrom'], level=AccessType.READ, exc=True, user=user)

            phase['metrics'] = srcPhase.get('metrics', {})
        else:
            phase['metrics'] = self.getBodyJson()

        # Determine if metrics IDs or weights changed at all
        newMetrics = phase['metrics']
        changed = set(oldMetrics.keys()) != set(newMetrics.keys())
        if not changed:
            for key in oldMetrics.iterkeys():
                if oldMetrics[key].get('weight') != \
                        newMetrics[key].get('weight'):
                    changed = True
                    break

        # If they have changed, recompute all scores using the new weights
        if changed:
            # TODO progress context
            self.model('submission', 'covalic').recomputeOverallScores(phase)

        return phaseModel.filter(phaseModel.save(phase), user)
    setMetrics.description = (
        Description('Set the metric information set for this phase.')
        .notes('If the metrics have changed, this will recompute all of the '
               'overall scores for this phase.')
        .param('id', 'ID of the phase to set metric info on.', paramType='path')
        .param('copyFrom', 'To copy the metric info from another phase, set '
               'this parameter to the ID of that phase.', required=False)
        .param('metrics', 'A JSON object representing the set of metrics for '
               'the challenge.', required=False, paramType='body'))
