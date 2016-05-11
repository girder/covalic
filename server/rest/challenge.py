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
import datetime
import json

from girder import logger
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import filtermodel, loadmodel, Resource, RestException
from girder.constants import AccessType
from girder.plugins.thumbnails.worker import createThumbnail
from girder.utility.progress import ProgressContext
from ..utility import getAssetsFolder


class Challenge(Resource):
    def __init__(self):
        super(Challenge, self).__init__()

        self.resourceName = 'challenge'

        self.route('GET', (), self.listChallenges)
        self.route('GET', (':id',), self.getChallenge)
        self.route('GET', (':id', 'access'), self.getAccess)
        self.route('POST', (), self.createChallenge)
        self.route('PUT', (':id',), self.updateChallenge)
        self.route('PUT', (':id', 'access'), self.updateAccess)
        self.route('DELETE', (':id',), self.deleteChallenge)
        self.route('GET', (':id', 'thumbnail', 'download'), self.downloadThumb)
        self.route('GET', (':id', 'assets_folder'), self.getAssetsFolder)
        self.route('POST', (':id', 'thumbnail'), self.createThumb)
        self.route('DELETE', (':id', 'thumbnail'), self.removeThumb)

    @access.public
    @filtermodel(model='challenge', plugin='covalic')
    @describeRoute(
        Description('List challenges.')
        .pagingParams(defaultSort='name')
        .param('name', 'Pass this to find a challenge by name.', required=False)
        .param('timeframe', 'Restrict challenges by timeframe.', required=False,
               enum=['all', 'active', 'upcoming'])
    )
    def listChallenges(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'name')

        filters = {}
        if 'name' in params:
            filters['name'] = params['name']
        if 'timeframe' in params:
            timeframe = params.get('timeframe')
            now = datetime.datetime.utcnow()
            if timeframe == 'all':
                # Allow all challenges
                pass
            elif timeframe == 'active':
                # Limit to active challenges. 'Active' is defined liberally in
                # that this passes open-ended challenges.
                filters['$or'] = [
                    {
                        'startDate': {'$lte': now},
                        'endDate': {'$gt': now},
                    },
                    {
                        'startDate': {'$lte': now},
                        'endDate': {'$in': [None, '']},
                    },
                    {
                        'startDate': {'$in': [None, '']},
                        'endDate': {'$gt': now},
                    },
                    {
                        'startDate': {'$in': [None, '']},
                        'endDate': {'$in': [None, '']},
                    }]
            elif timeframe == 'upcoming':
                # Limit to challenges that start in the future. Doesn't include
                # 'active' challenges.
                filters['startDate'] = {'$gt': now}
            else:
                raise RestException('Invalid timeframe parameter.')

        user = self.getCurrentUser()
        return list(self.model('challenge', 'covalic').list(
            user=user, offset=offset, limit=limit, sort=sort, filters=filters))

    @access.user
    @filtermodel(model='challenge', plugin='covalic')
    @describeRoute(
        Description('Create a new challenge.')
        .param('name', 'The name for this challenge.')
        .param('description', 'Description for this challenge.', required=False)
        .param('instructions', 'Instructional text for this challenge.',
               required=False)
        .param('public', 'Whether the challenge should be publicly visible.',
               dataType='boolean')
        .param('organizers', 'The organizers of the challenge.',
               required=False)
        .param('startDate', 'The start date of the challenge '
               '(ISO 8601 format).', dataType='dateTime', required=False)
        .param('endDate', 'The end date of the challenge (ISO 8601 format).',
               dataType='dateTime', required=False)
    )
    def createChallenge(self, params):
        self.requireParams('name', params)
        user = self.getCurrentUser()
        public = self.boolParam('public', params, default=False)
        description = params.get('description', '').strip()
        instructions = params.get('instructions', '').strip()
        organizers = params.get('organizers', '').strip()
        startDate = params.get('startDate')
        endDate = params.get('endDate')

        return self.model('challenge', 'covalic').createChallenge(
            name=params['name'].strip(), description=description, public=public,
            instructions=instructions, creator=user, organizers=organizers,
            startDate=startDate, endDate=endDate)

    @access.user
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.WRITE)
    @filtermodel(model='challenge', plugin='covalic')
    @describeRoute(
        Description('Update the properties of a challenge.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .param('name', 'The name for this challenge.', required=False)
        .param('description', 'Description for this challenge.', required=False)
        .param('instructions', 'Instructions to participants for this '
               'challenge.', required=False)
        .param('organizers', 'The organizers of the challenge.', required=False)
        .param('startDate', 'The start date of the challenge '
               '(ISO 8601 format).', dataType='dateTime', required=False)
        .param('endDate', 'The end date of the challenge (ISO 8601 format).',
               dataType='dateTime', required=False)
        .errorResponse('ID was invalid.')
        .errorResponse('Write permission denied on the challenge.', 403)
    )
    def updateChallenge(self, challenge, params):
        challenge['name'] = params.get('name', challenge['name']).strip()
        challenge['description'] = params.get(
            'description', challenge.get('description', '')).strip()
        challenge['instructions'] = params.get(
            'instructions', challenge.get('instructions', '')).strip()
        challenge['organizers'] = params.get(
            'organizers', challenge.get('organizers', '')).strip()
        challenge['startDate'] = params.get(
            'startDate', challenge.get('startDate', None))
        challenge['endDate'] = params.get(
            'endDate', challenge.get('endDate', None))

        return self.model('challenge', 'covalic').save(challenge)

    @access.user
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.ADMIN)
    @filtermodel(model='challenge', plugin='covalic', addFields={'access'})
    @describeRoute(
        Description('Set the access control list for a challenge.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .param('access', 'The access control list as JSON.')
        .param('public', 'Whether the challenge should be publicly visible.',
               dataType='boolean')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin permission denied on the challenge.', 403)
    )
    def updateAccess(self, challenge, params):
        self.requireParams('access', params)

        public = self.boolParam('public', params, default=False)
        self.model('challenge', 'covalic').setPublic(challenge, public)

        try:
            access = json.loads(params['access'])
            return self.model('challenge', 'covalic').setAccessList(
                challenge, access, save=True)
        except ValueError:
            raise RestException('The access parameter must be JSON.')

    @access.public
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.READ)
    @filtermodel(model='challenge', plugin='covalic')
    @describeRoute(
        Description('Get a challenge by ID.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read permission denied on the challenge.', 403)
    )
    def getChallenge(self, challenge, params):
        return challenge

    @access.user
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.ADMIN)
    @describeRoute(
        Description('Get the access control list for a challenge.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the challenge.', 403)
    )
    def getAccess(self, challenge, params):
        return self.model('challenge', 'covalic').getFullAccessList(challenge)

    @access.user
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.ADMIN)
    @describeRoute(
        Description('Delete a challenge.')
        .param('id', 'The ID of the challenge to delete.', paramType='path')
        .param('progress', 'Whether to record progress on this task. Default '
               'is false.', required=False, dataType='boolean')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the challenge.', 403)
    )
    def deleteChallenge(self, challenge, params):
        progress = self.boolParam('progress', params, default=False)
        with ProgressContext(progress, user=self.getCurrentUser(),
                             title=u'Deleting challenge ' + challenge['name'],
                             message='Calculating total size...') as ctx:
            if progress:
                ctx.update(
                    total=self.model('challenge', 'covalic').subtreeCount(
                        challenge))
            self.model('challenge', 'covalic').remove(challenge, progress=ctx)
        return {'message': 'Deleted challenge %s.' % challenge['name']}

    @access.public
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.READ)
    def downloadThumb(self, challenge, params):
        self.requireParams('size', params)
        size = int(params['size'])

        if not challenge.get('thumbnails'):
            url = '//www.gravatar.com/avatar/%s?d=identicon&s=%d' % (
                challenge['name'].encode('hex'), size)
            raise cherrypy.HTTPRedirect(url)

        # We assume thumbnails are stored in ascending order of size. We return
        # the smallest one that is greater than or equal to the requested size,
        # or simply the largest one if none are large enough.
        for thumbnail in challenge['thumbnails']:
            if thumbnail['size'] >= size:
                break

        file = self.model('file').load(thumbnail['fileId'], force=True)
        return self.model('file').download(file)
    downloadThumb.description = (
        Description('Get the thumbnail for the given challenge.')
        .notes('If the challenge has no thumbnail, this will redirect to an '
               'identicon on gravatar.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .param('size', 'Side length of the image in pixels.', dataType='int'))
    downloadThumb.cookieAuth = True

    @access.user
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.WRITE)
    @loadmodel(model='file', map={'fileId': 'file'}, level=AccessType.READ)
    def createThumb(self, file, challenge, params):
        self.requireParams('size', params)
        size = int(params['size'])
        user = self.getCurrentUser()

        if challenge.get('thumbnailSourceId') != file['_id']:
            challenge['thumbnails'] = []

        challenge['thumbnailSourceId'] = file['_id']

        i = 0
        for thumbnail in challenge['thumbnails']:
            if thumbnail['size'] == size:
                return self.model('file').filter(
                    self.model('file').load(thumbnail['fileId'], force=True),
                    user)
            elif size < thumbnail['size']:
                break
            i += 1

        try:
            newThumb = createThumbnail(
                width=size, height=size, crop=True, fileId=file['_id'],
                attachToType='item', attachToId=file['itemId'])
        except IOError:
            logger.exception('Thumbnail creation IOError')
            raise RestException('Could not create thumbnail from the file.')

        challenge['thumbnails'].insert(i, {
            'size': size,
            'fileId': newThumb['_id']
        })
        self.model('challenge', 'covalic').save(challenge)

        return self.model('file').filter(newThumb, user)
    createThumb.description = (
        Description('Create a new thumbnail for this challenge.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .param('size', 'Side length of the thumbnail image.', dataType='int')
        .param('fileId', 'The source image file ID.'))

    @access.public
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.READ)
    @filtermodel(model='folder')
    @describeRoute(
        Description('Get the folder containing assets for this challenge.')
        .param('id', 'The ID of the challenge', paramType='path')
    )
    def getAssetsFolder(self, challenge, params):
        return getAssetsFolder(challenge, self.getCurrentUser())

    @access.user
    @loadmodel(model='challenge', plugin='covalic', level=AccessType.WRITE)
    def removeThumb(self, challenge, params):
        del challenge['thumbnailSourceId']
        del challenge['thumbnails']
        self.model('challenge', 'covalic').save(challenge)

        return {'message': 'Thumbnail deleted.'}
    removeThumb.description = (
        Description('Remove the thumbnail for a challenge.')
        .param('id', 'The ID of the challenge.', paramType='path'))
