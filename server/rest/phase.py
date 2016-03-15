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
from girder.api.describe import Description, describeRoute
from girder.api.rest import filtermodel, loadmodel, getApiUrl
from girder.constants import AccessType
from girder.plugins.challenge.rest.phase import Phase


class PhaseExt(Phase):
    def __init__(self):
        Phase.__init__(self)

        self.route('GET', (':id', 'groundtruth', 'item'), self.groundtruthItems)
        self.route('GET', (':id', 'test_data', 'item'), self.testDataItems)
        self.route('PUT', (':id', 'metrics'), self.setMetrics)
        self.route('PUT', (':id', 'scoring_info'), self.setScoringInfo)
        self.route('POST', (':id', 'metrics', 'init'), self.initMetrics)

    @access.public
    @loadmodel(model='phase', plugin='challenge', level=AccessType.READ)
    @filtermodel(model='item')
    @describeRoute(
        Description('List all ground truth item names for a challenge phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .pagingParams(defaultSort='name')
    )
    def groundtruthItems(self, phase, params):
        # All participants can see the names of the ground truth items in
        # order to validate their submissions, even if they don't have
        # read access to the folder.
        folder = self.model('folder').load(
            phase['groundTruthFolderId'], force=True)

        return list(self.model('folder').childItems(folder, limit=0, fields=(
            'name', '_id'
        )))

    @access.public
    @loadmodel(model='phase', plugin='challenge', level=AccessType.READ)
    @filtermodel(model='item')
    @describeRoute(
        Description('List all test data item names for a challenge phase.')
        .pagingParams(defaultSort='name')
        .param('id', 'The ID of the phase.', paramType='path')
    )
    def testDataItems(self, phase, params):
        if 'testDataFolderId' not in phase:
            return ()

        limit, offset, sort = self.getPagingParameters(params, 'name')

        folder = self.model('folder').load(
            phase['testDataFolderId'], user=self.getCurrentUser(),
            level=AccessType.READ, exc=True)

        return list(self.model('folder').childItems(
            folder, limit=limit, offset=offset, sort=sort))

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

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.WRITE)
    def initMetrics(self, phase, params):
        user = self.getCurrentUser()

        apiUrl = getApiUrl()
        jobModel = self.model('job', 'jobs')

        title = '%s: metric weight initialization' % phase['name']
        job = jobModel.createJob(
            title=title, type='covalic_weight_init', user=user,
            handler='worker_handler')
        jobToken = jobModel.createJobToken(job)

        scoreToken = self.model('token').createToken(user=user, days=7)
        groundTruth = self.model('folder').load(
            phase['groundTruthFolderId'], user=user, level=AccessType.READ,
            exc=True)

        kwargs = {
            'task': {
                'name': title,
                'mode': 'docker',
                'docker_image': 'girder/covalic-metrics:latest',
                'container_args': [
                    '/covalic/Python/RankAggregation/computeWeights.py',
                    '--groundtruth=$input{groundtruth}'
                ],
                'entrypoint': 'python',
                'inputs': [{
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
                    'method': 'PUT',
                    'format': 'string',
                    'url': '/'.join((apiUrl, 'challenge_phase',
                                     str(phase['_id']), 'metrics')),
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
        job = jobModel.save(job)
        jobModel.scheduleJob(job)

        return jobModel.filter(job, user)
    initMetrics.description = (
        Description('Test ground truth data to set initial metric weights.')
        .notes('Runs perturbation on the ground truth images and then scores '
               'the results in order to automatically initialize the metric '
               'weights to sensible values.')
        .param('id', 'The ID of the phase.', paramType='path'))

    @access.admin
    @loadmodel(model='phase', plugin='challenge', level=AccessType.ADMIN)
    def setScoringInfo(self, phase, params):
        phase['scoreTask'] = phase.get('scoreTask', {})

        if 'dockerImage' in params:
            phase['scoreTask']['dockerImage'] = params['dockerImage']
        if 'dockerArgs' in params:
            phase['scoreTask']['dockerArgs'] = params['dockerArgs']

        phaseModel = self.model('phase', 'challenge')
        return self.model('phase', 'challenge').filter(
            phaseModel.save(phase), self.getCurrentUser())
    setScoringInfo.description = (
        Description('Customize submission scoring behavior for this phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .param('dockerImage', 'Name of the docker image to use for scoring '
               'submissions to this phase.', required=False)
        .param('dockerArgs', 'JSON list of arguments to pass to the scoring '
               'container.', required=False)
        .notes('Only site administrators may use this route.')
    )
