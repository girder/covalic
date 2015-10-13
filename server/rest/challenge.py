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

from girder.api import access
from girder.api.describe import Description
from girder.api.rest import loadmodel
from girder.constants import AccessType
from girder.plugins.challenge.rest.challenge import Challenge
from girder.plugins.thumbnails.worker import createThumbnail


class ChallengeExt(Challenge):
    def __init__(self):
        Challenge.__init__(self)

        self.route('GET', (':id', 'thumbnail', 'download'), self.downloadThumb)
        self.route('GET', (':id', 'assets_folder'), self.getAssetsFolder)
        self.route('POST', (':id', 'thumbnail'), self.createThumb)
        self.route('DELETE', (':id', 'thumbnail'), self.removeThumb)

    @access.public
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.READ)
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
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.WRITE)
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

        newThumb = createThumbnail(
            width=size, height=size, crop=True, fileId=file['_id'],
            attachToType='item', attachToId=file['itemId'])
        challenge['thumbnails'].insert(i, {
            'size': size,
            'fileId': newThumb['_id']
        })
        self.model('challenge', 'challenge').save(challenge)

        return self.model('file').filter(newThumb, user)
    createThumb.description = (
        Description('Create a new thumbnail for this challenge.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .param('size', 'Side length of the thumbnail image.', dataType='int')
        .param('fileId', 'The source image file ID.'))

    @access.public
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.READ)
    def getAssetsFolder(self, challenge, params):
        user = self.getCurrentUser()

        collection = self.model('collection').load(
            challenge['collectionId'], force=True)

        folder = self.model('folder').createFolder(
            parentType='collection', parent=collection,
            name='Assets', creator=user, reuseExisting=True,
            description='Assets related to this challenge.')
        self.model('folder').requireAccess(folder, user=user,
                                           level=AccessType.READ)
        return self.model('folder').filter(folder, user)
    getAssetsFolder.description = (
        Description('Get the folder containing assets related to this '
                    'challenge.')
        .param('id', 'The ID of the challenge', paramType='path'))

    @access.user
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.WRITE)
    def removeThumb(self, challenge, params):
        del challenge['thumbnailSourceId']
        del challenge['thumbnails']
        self.model('challenge', 'challenge').save(challenge)

        return {'message': 'Thumbnail deleted.'}
    removeThumb.description = (
        Description('Remove the thumbnail for a challenge.')
        .param('id', 'The ID of the challenge.', paramType='path'))
