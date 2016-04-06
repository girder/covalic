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
        admin = self.model('user').createUser(
            email='admin@email.com', login='admin', firstName='Admin',
            lastName='Admin', password='passwd')
        challenge = self.model('challenge', 'challenge').createChallenge(
            name='challenge 1',
            creator=self.user1,
            public=False)
