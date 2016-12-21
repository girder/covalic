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

from tests import base
from girder.constants import AccessType


def setUpModule():
    base.enabledPlugins.append('covalic')
    base.startServer()


def tearDownModule():
    base.stopServer()


class AssetFolderTestCase(base.TestCase):
    def testAssetFolder(self):
        challengeModel = self.model('challenge', 'covalic')
        admin = self.model('user').createUser(
            email='admin@email.com', login='admin', firstName='Admin',
            lastName='Admin', password='passwd')
        challenge = challengeModel.createChallenge(
            name='challenge 1', creator=admin, public=False)
        group = self.model('group').createGroup('A group', creator=admin)

        # Make sure asset folder gets created
        resp = self.request('/challenge/%s/assets_folder' % challenge['_id'],
                            method='GET', user=admin)
        self.assertStatusOk(resp)
        folder = self.model('folder').load(
            resp.json['_id'], force=True, exc=True)
        self.assertEqual(folder['name'], 'Assets')
        self.assertEqual(folder['public'], False)
        self.assertEqual(folder['creatorId'], admin['_id'])
        self.assertEqual(folder['access'], {
            'users': [{
                'id': admin['_id'],
                'flags': [],
                'level': AccessType.ADMIN
            }],
            'groups': []
        })

        # Make sure assets folder tracks challenge ACL
        challengeModel.setGroupAccess(
            challenge, group, level=AccessType.WRITE, save=True)
        folder = self.model('folder').load(folder['_id'], force=True)
        self.assertEqual(folder['access'], {
            'users': [{
                'id': admin['_id'],
                'flags': [],
                'level': AccessType.ADMIN
            }],
            'groups': [{
                'id': group['_id'],
                'flags': [],
                'level': AccessType.WRITE
            }]
        })
