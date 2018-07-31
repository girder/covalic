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

import bson.json_util
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import filtermodel, loadmodel, getApiUrl, Resource, \
    RestException
from girder.constants import AccessType
from girder.utility.progress import ProgressContext


def _loadMetadata(params):
    if 'meta' not in params:
        return None
    try:
        meta = bson.json_util.loads(params['meta'])
    except ValueError:
        raise RestException('Parameter meta must be valid JSON.')

    if not isinstance(meta, dict):
        raise RestException('Parameter meta must be a JSON object.')
    return meta


class Phase(Resource):
    def __init__(self):
        super(Phase, self).__init__()

        self.resourceName = 'challenge_phase'

        self.route('GET', (), self.listPhases)
        self.route('GET', (':id',), self.getPhase)
        self.route('GET', (':id', 'access'), self.getAccess)
        self.route('POST', (), self.createPhase)
        self.route('POST', (':id', 'participant'), self.joinPhase)
        self.route('PUT', (':id',), self.updatePhase)
        self.route('PUT', (':id', 'access'), self.updateAccess)
        self.route('DELETE', (':id',), self.deletePhase)
        self.route('GET', (':id', 'groundtruth', 'item'), self.groundtruthItems)
        self.route('GET', (':id', 'test_data', 'item'), self.testDataItems)
        self.route('PUT', (':id', 'metrics'), self.setMetrics)
        self.route('PUT', (':id', 'scoring_info'), self.setScoringInfo)
        self.route('POST', (':id', 'metrics', 'init'), self.initMetrics)
        self.route('POST', (':id', 'rescore'), self.rescorePhase)

    @access.public
    @loadmodel(map={'challengeId': 'challenge'}, model='challenge',
               plugin='covalic', level=AccessType.READ)
    @describeRoute(
        Description('List phases for a challenge.')
        .param('challengeId', 'The ID of the challenge.')
        .param('limit', "Result set size limit (default=50).", required=False,
               dataType='int')
        .param('offset', "Offset into result set (default=0).", required=False,
               dataType='int')
        .param('sort', "Field to sort the result list by (default=ordinal)",
               required=False)
        .param('sortdir', "1 for ascending, -1 for descending (default=1)",
               required=False, dataType='int')
    )
    def listPhases(self, challenge, params):
        limit, offset, sort = self.getPagingParameters(params, 'ordinal')

        user = self.getCurrentUser()
        results = self.model('phase', 'covalic').list(
            challenge, user=user, offset=offset, limit=limit, sort=sort)
        return [self.model('phase', 'covalic').filter(p, user)
                for p in results]

    @access.user
    @loadmodel(map={'challengeId': 'challenge'}, level=AccessType.WRITE,
               model='challenge', plugin='covalic')
    @describeRoute(
        Description('Add a phase to an existing challenge.')
        .param('challengeId', 'The ID of the challenge to add the phase to.')
        .param('name', 'The name for this phase.')
        .param('description', 'Description for this phase.', required=False)
        .param('instructions', 'Instructions to participants for this phase.',
               required=False)
        .param('participantGroupId', 'If you wish to use an existing '
               'group as the participant group, pass its ID in this parameter.'
               ' If you omit this, a participant group will be automatically '
               'created for this phase.', required=False)
        .param('public', 'Whether the phase should be publicly visible.',
               dataType='boolean')
        .param('active', 'Whether the phase will accept and score additional '
               'submissions.', dataType='boolean', required=False)
        .param('startDate', 'The start date of the phase (ISO 8601 format).',
               dataType='dateTime', required=False)
        .param('endDate', 'The end date of the phase (ISO 8601 format).',
               dataType='dateTime', required=False)
        .param('type', 'The type of the phase.', required=False)
        .param('hideScores', 'Whether submission scores should be hidden from '
               'participants.', dataType='boolean', default=False,
               required=False)
        .param('matchSubmissions', 'Whether to require that submission '
               'filenames match ground truth filenames', dataType='boolean',
               default=True, required=False)
        .param('enableOrganization', 'Enable submission Organization field.', dataType='boolean',
               default=False, required=False)
        .param('enableOrganizationUrl', 'Enable submission Organization URL field.',
               dataType='boolean', default=False, required=False)
        .param('enableDocumentationUrl', 'Enable submission Documentation URL field.',
               dataType='boolean', default=False, required=False)
        .param('requireOrganization', 'Require submission Organization field.', dataType='boolean',
               default=True, required=False)
        .param('requireOrganizationUrl', 'Require submission Organization URL field.',
               dataType='boolean', default=True, required=False)
        .param('requireDocumentationUrl', 'Require submission Documentation URL field.',
               dataType='boolean', default=True, required=False)
        .param('meta', 'A JSON object containing additional metadata.',
               required=False)
    )
    def createPhase(self, challenge, params):
        self.requireParams('name', params)

        user = self.getCurrentUser()
        public = self.boolParam('public', params, default=False)
        active = self.boolParam('active', params, default=False)
        hideScores = self.boolParam('hideScores', params, default=False)
        matchSubmissions = self.boolParam('matchSubmissions', params,
                                          default=True)
        enableOrganization = self.boolParam('enableOrganization', params, default=False)
        enableOrganizationUrl = self.boolParam('enableOrganizationUrl', params, default=False)
        enableDocumentationUrl = self.boolParam('enableDocumentationUrl', params, default=False)
        requireOrganization = self.boolParam('requireOrganization', params, default=True)
        requireOrganizationUrl = self.boolParam('requireOrganizationUrl', params, default=True)
        requireDocumentationUrl = self.boolParam('requireDocumentationUrl', params, default=True)
        description = params.get('description', '').strip()
        instructions = params.get('instructions', '').strip()

        participantGroupId = params.get('participantGroupId')
        if participantGroupId:
            group = self.model('group').load(
                participantGroupId, user=user, level=AccessType.READ)
        else:
            group = None

        ordinal = len([self.model('phase', 'covalic').filter(p, user)
                       for p in self.model('phase', 'covalic').list(
                           challenge, user=user)])

        startDate = params.get('startDate')
        endDate = params.get('endDate')

        type = params.get('type', '').strip()
        meta = _loadMetadata(params)

        phase = self.model('phase', 'covalic').createPhase(
            name=params['name'].strip(), description=description,
            instructions=instructions, active=active, public=public,
            creator=user, challenge=challenge, participantGroup=group,
            ordinal=ordinal, startDate=startDate, endDate=endDate,
            type=type, hideScores=hideScores, matchSubmissions=matchSubmissions,
            enableOrganization=enableOrganization, enableOrganizationUrl=enableOrganizationUrl,
            enableDocumentationUrl=enableDocumentationUrl,
            requireOrganization=requireOrganization,
            requireOrganizationUrl=requireOrganizationUrl,
            requireDocumentationUrl=requireDocumentationUrl,
            meta=meta
        )

        return phase

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.ADMIN)
    @describeRoute(
        Description('Get the access control list for a phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the phase.', 403)
    )
    def getAccess(self, phase, params):
        return self.model('phase', 'covalic').getFullAccessList(phase)

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.ADMIN)
    @describeRoute(
        Description('Set the access control list for a challenge phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .param('access', 'The access control list as JSON.')
        .param('public', 'Whether the phase should be publicly visible.',
               dataType='boolean')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin permission denied on the phase.', 403)
    )
    def updateAccess(self, phase, params):
        self.requireParams('access', params)

        folderModel = self.model('folder')
        phaseModel = self.model('phase', 'covalic')
        folder = folderModel.load(phase['folderId'], force=True)
        public = self.boolParam('public', params, default=False)
        phaseModel.setPublic(phase, public)
        folderModel.setPublic(folder, public)

        try:
            access = json.loads(params['access'])
            folderModel.setAccessList(folder, access, save=True)
            return phaseModel.setAccessList(phase, access, save=True)
        except ValueError:
            raise RestException('The access parameter must be JSON.')

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.WRITE)
    @filtermodel(model='phase', plugin='covalic')
    @describeRoute(
        Description('Update the properties of a challenge phase.')
        .responseClass('Phase')
        .param('id', 'The ID of the phase.', paramType='path')
        .param('name', 'The name for this phase.', required=False)
        .param('description', 'Description for this phase.', required=False)
        .param('instructions', 'Instructions to participants for this phase.',
               required=False)
        .param('folderId', 'ID of the backing folder for this phase.',
               required=False)
        .param('participantGroupId', 'ID of an existing group to set as the '
               'participant group for this phase.', required=False)
        .param('groundTruthFolderId', 'ID of the ground truth folder for this '
               'phase.', required=False)
        .param('testDataFolderId', 'ID of the test dataset folder for this '
               'phase.', required=False)
        .param(
            'active', 'Whether the phase will accept and score additional '
            'submissions.', dataType='boolean', required=False)
        .param('hideScores', 'Whether submission scores should be hidden from '
               'participants.', dataType='boolean', required=False)
        .param('startDate', 'The start date of the phase (ISO 8601 format).',
               dataType='dateTime', required=False)
        .param('endDate', 'The end date of the phase (ISO 8601 format).',
               dataType='dateTime', required=False)
        .param('type', 'The type of the phase.', required=False)
        .param('matchSubmissions', 'Whether to require that submission '
               'filenames match ground truth filenames', dataType='boolean', required=False)
        .param('enableOrganization', 'Enable submission Organization field.', dataType='boolean',
               required=False)
        .param('enableOrganizationUrl', 'Enable submission Organization URL field.',
               dataType='boolean', required=False)
        .param('enableDocumentationUrl', 'Enable submission Documentation URL field.',
               dataType='boolean', required=False)
        .param('requireOrganization', 'Require submission Organization field.', dataType='boolean',
               required=False)
        .param('requireOrganizationUrl', 'Require submission Organization URL field.',
               dataType='boolean', required=False)
        .param('requireDocumentationUrl', 'Require submission Documentation URL field.',
               dataType='boolean', required=False)
        .param('meta', 'A JSON object containing additional metadata. '
               'If present, replaces the existing metadata.', required=False)
        .errorResponse('ID was invalid.')
        .errorResponse('Write permission denied on the phase.', 403)
    )
    def updatePhase(self, phase, params):
        user = self.getCurrentUser()

        phase['active'] = self.boolParam('active', params, phase['active'])
        phase['hideScores'] = self.boolParam('hideScores', params,
                                             phase.get('hideScores', False))
        phase['matchSubmissions'] = self.boolParam(
            'matchSubmissions', params, phase.get('matchSubmissions', True))
        phase['enableOrganization'] = self.boolParam(
            'enableOrganization', params, phase.get('enableOrganization', False))
        phase['enableOrganizationUrl'] = self.boolParam(
            'enableOrganizationUrl', params, phase.get('enableOrganizationUrl', False))
        phase['enableDocumentationUrl'] = self.boolParam(
            'enableDocumentationUrl', params, phase.get('enableDocumentationUrl', False))
        phase['requireOrganization'] = self.boolParam(
            'requireOrganization', params, phase.get('requireOrganization', True))
        phase['requireOrganizationUrl'] = self.boolParam(
            'requireOrganizationUrl', params, phase.get('requireOrganizationUrl', True))
        phase['requireDocumentationUrl'] = self.boolParam(
            'requireDocumentationUrl', params, phase.get('requireDocumentationUrl', True))
        phase['name'] = params.get('name', phase['name']).strip()
        phase['description'] = params.get('description',
                                          phase.get('description', '')).strip()
        phase['instructions'] = params.get(
            'instructions', phase.get('instructions', '')).strip()

        if 'ordinal' in params:
            phase['ordinal'] = int(params.get('ordinal').strip())
        if ('participantGroupId' in params and params['participantGroupId'] !=
                str(phase.get('participantGroupId'))):
            group = self.model('group').load(
                params['participantGroupId'],
                user=user, level=AccessType.READ, exc=True)
            phase['participantGroupId'] = group['_id']
        if ('folderId' in params and
                params['folderId'] != str(phase['folderId'])):
            folder = self.model('folder').load(
                params['folderId'], user=user,
                level=AccessType.READ, exc=True)
            phase['folderId'] = folder['_id']
        if ('groundTruthFolderId' in params and params['groundTruthFolderId'] !=
                str(phase.get('groundTruthFolderId'))):
            folder = self.model('folder').load(
                params['groundTruthFolderId'], user=user,
                level=AccessType.READ, exc=True)
            phase['groundTruthFolderId'] = folder['_id']
        if ('testDataFolderId' in params and params['testDataFolderId'] !=
                str(phase.get('testDataFolderId'))):
            folder = self.model('folder').load(
                params['testDataFolderId'], user=user, level=AccessType.READ,
                exc=True)
            phase['testDataFolderId'] = folder['_id']

        phase['startDate'] = params.get(
            'startDate', phase.get('startDate', None))
        phase['endDate'] = params.get(
            'endDate', phase.get('endDate', None))

        phase['type'] = params.get('type', phase.get('type', '')).strip()
        meta = _loadMetadata(params)
        if meta is not None:
            phase['meta'] = meta

        return self.model('phase', 'covalic').updatePhase(phase)

    @access.public
    @loadmodel(model='phase', plugin='covalic', level=AccessType.READ)
    @describeRoute(
        Description('Get a phase by ID.')
        .responseClass('Phase')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read permission denied on the phase.', 403)
    )
    def getPhase(self, phase, params):
        return self.model('phase', 'covalic').filter(
            phase, self.getCurrentUser())

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.READ)
    @describeRoute(
        Description('Join a phase as a competitor.')
        .responseClass('Phase')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read permission denied on the phase.', 403)
    )
    def joinPhase(self, phase, params):
        user = self.getCurrentUser()
        phase = self.model('phase', 'covalic').filter(
            phase, self.getCurrentUser())
        participantGroupId = phase['participantGroupId']
        if 'groups' not in user or participantGroupId not in user['groups']:
            participantGroup = self.model('group').load(
                participantGroupId, force=True, exc=True)
            self.model('group').addUser(participantGroup, user,
                                        level=AccessType.READ)
        return phase

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.ADMIN)
    @describeRoute(
        Description('Delete a phase.')
        .param('id', 'The ID of the phase to delete.', paramType='path')
        .param('progress', 'Whether to record progress on this task. Default '
               'is false.', required=False, dataType='boolean')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the phase.', 403)
    )
    def deletePhase(self, phase, params):
        progress = self.boolParam('progress', params, default=False)
        with ProgressContext(progress, user=self.getCurrentUser(),
                             title=u'Deleting phase ' + phase['name'],
                             message='Calculating total size...') as ctx:
            if progress:
                ctx.update(
                    total=self.model('phase', 'covalic').subtreeCount(phase))
            self.model('phase', 'covalic').remove(phase, progress=ctx)
        return {'message': 'Deleted phase %s.' % phase['name']}

    @access.public
    @loadmodel(model='phase', plugin='covalic', level=AccessType.READ)
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
    @loadmodel(model='phase', plugin='covalic', level=AccessType.READ)
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
    @loadmodel(model='phase', plugin='covalic', level=AccessType.WRITE)
    @describeRoute(
        Description('Set the metric information set for this phase.')
        .notes('If the metrics have changed, this will recompute all of the '
               'overall scores for this phase.')
        .param('id', 'ID of the phase to set metric info on.', paramType='path')
        .param('copyFrom', 'To copy the metric info from another phase, set '
               'this parameter to the ID of that phase.', required=False)
        .param('metrics', 'A JSON object representing the set of metrics for '
               'the challenge.', required=False, paramType='body')
    )
    def setMetrics(self, phase, params):
        phaseModel = self.model('phase', 'covalic')
        user = self.getCurrentUser()

        oldMetrics = phase.get('metrics', {})

        if 'copyFrom' in params:
            srcPhase = self.model('phase', 'covalic').load(
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

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.WRITE)
    @describeRoute(
        Description('Test ground truth data to set initial metric weights.')
        .notes('Runs perturbation on the ground truth images and then scores '
               'the results in order to automatically initialize the metric '
               'weights to sensible values.')
        .param('id', 'The ID of the phase.', paramType='path')
    )
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

    @access.user
    @loadmodel(model='phase', plugin='covalic', level=AccessType.ADMIN)
    @describeRoute(
        Description('Customize submission scoring behavior for this phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .param('dockerImage', 'Name of the docker image to use for scoring '
               'submissions to this phase.', required=False)
        .param('dockerArgs', 'JSON list of arguments to pass to the scoring '
               'container.', required=False)
    )
    def setScoringInfo(self, phase, params):
        phase['scoreTask'] = phase.get('scoreTask', {})

        if 'dockerImage' in params:
            phase['scoreTask']['dockerImage'] = params['dockerImage']
        if 'dockerArgs' in params:
            phase['scoreTask']['dockerArgs'] = params['dockerArgs']

        phaseModel = self.model('phase', 'covalic')
        return self.model('phase', 'covalic').filter(
            phaseModel.save(phase), self.getCurrentUser())

    @access.admin
    @loadmodel(model='phase', plugin='covalic', level=AccessType.ADMIN)
    @describeRoute(
        Description('Re-run scoring for the latest submissions in the phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Site admin access is required.', 403)
    )
    def rescorePhase(self, phase, params):
        submissionModel = self.model('submission', 'covalic')

        submissions = submissionModel.list(
            phase, limit=0, sort=[('created', 1)], fields={'score': False}, latest=True)

        # Get API URL by removing this endpoint's parameters
        apiUrl = '/'.join(cherrypy.url().split('/')[:-3])

        for submission in submissions:
            submissionModel.scoreSubmission(submission, apiUrl)
