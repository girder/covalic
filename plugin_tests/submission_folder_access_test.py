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


class SubmissionFolderAccessTestCase(base.TestCase):
    def testSubmissionFolderAccess(self):
        # Create users
        challengeAdmin = self.model('user').createUser(
            email='challenge@email.com', login='challenge',
            firstName='Challenge', lastName='Admin', password='passwd')
        phaseAdmin1 = self.model('user').createUser(
            email='phase1@email.com', login='phase1',
            firstName='Phase', lastName='Admin 1', password='passwd')
        phaseAdmin2 = self.model('user').createUser(
            email='phase2@email.com', login='phase2',
            firstName='Phase', lastName='Admin 2', password='passwd')
        user1 = self.model('user').createUser(
            email='user1@email.com', login='user1',
            firstName='User', lastName='1', password='passwd')

        challengeModel = self.model('challenge', 'challenge')
        phaseModel = self.model('phase', 'challenge')
        folderModel = self.model('folder')
        submissionModel = self.model('submission', 'covalic')

        # Create challenge and phase
        challenge = challengeModel.createChallenge(
            name='challenge 1', creator=challengeAdmin, public=False)
        phase = phaseModel.createPhase(
            name='phase 1', challenge=challenge, creator=phaseAdmin1, ordinal=1)

        # Add phaseAdmin2 and user 1 as phase admins
        phaseModel.setUserAccess(phase, phaseAdmin2, AccessType.WRITE, save=True)
        phaseModel.setUserAccess(phase, user1, AccessType.WRITE, save=True)

        # Create folder and submission as user1
        submissionFolder = folderModel.createFolder(
            parent=user1, name='submission 1', parentType='user', creator=user1)
        submissionModel.createSubmission(
            creator=user1, phase=phase, folder=submissionFolder)

        # Submission folder ACL should include phase admins with read access
        submissionFolder = folderModel.load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 3)
        self.assertEqual(submissionFolder['access']['users'][0]['id'],
                         user1['_id'])
        self.assertEqual(submissionFolder['access']['users'][0]['level'],
                         AccessType.ADMIN)
        self.assertEqual(submissionFolder['access']['users'][1]['id'],
                         phaseAdmin1['_id'])
        self.assertEqual(submissionFolder['access']['users'][1]['level'],
                         AccessType.READ)
        self.assertEqual(submissionFolder['access']['users'][2]['id'],
                         phaseAdmin2['_id'])
        self.assertEqual(submissionFolder['access']['users'][2]['level'],
                         AccessType.READ)

        # Remove user1 as phase admin. This shouldn't change folder ACL because
        # user1 is the folder's owner.
        phaseModel.setUserAccess(phase, user1, None, save=True)
        submissionFolder = folderModel.load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 3)
        self.assertEqual(submissionFolder['access']['users'][0]['id'],
                         user1['_id'])
        self.assertEqual(submissionFolder['access']['users'][0]['level'],
                         AccessType.ADMIN)
        self.assertEqual(submissionFolder['access']['users'][1]['id'],
                         phaseAdmin1['_id'])
        self.assertEqual(submissionFolder['access']['users'][1]['level'],
                         AccessType.READ)
        self.assertEqual(submissionFolder['access']['users'][2]['id'],
                         phaseAdmin2['_id'])
        self.assertEqual(submissionFolder['access']['users'][2]['level'],
                         AccessType.READ)

        # Remove phaseAdmin2 as a phase admin. This should remove phaseAdmin2
        # from the submission folder ACL.
        phaseModel.setUserAccess(phase, phaseAdmin2, None, save=True)
        submissionFolder = folderModel.load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 2)
        self.assertEqual(submissionFolder['access']['users'][0]['id'],
                         user1['_id'])
        self.assertEqual(submissionFolder['access']['users'][0]['level'],
                         AccessType.ADMIN)
        self.assertEqual(submissionFolder['access']['users'][1]['id'],
                         phaseAdmin1['_id'])
        self.assertEqual(submissionFolder['access']['users'][1]['level'],
                         AccessType.READ)

        # Re-add phaseAdmin2 as phase admin. This should add phaseAdmin2 back to
        # the submission folder ACL.
        phaseModel.setUserAccess(phase, phaseAdmin2, AccessType.WRITE, save=True)
        submissionFolder = folderModel.load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 3)
        self.assertEqual(submissionFolder['access']['users'][0]['id'],
                         user1['_id'])
        self.assertEqual(submissionFolder['access']['users'][0]['level'],
                         AccessType.ADMIN)
        self.assertEqual(submissionFolder['access']['users'][1]['id'],
                         phaseAdmin1['_id'])
        self.assertEqual(submissionFolder['access']['users'][1]['level'],
                         AccessType.READ)
        self.assertEqual(submissionFolder['access']['users'][2]['id'],
                         phaseAdmin2['_id'])
        self.assertEqual(submissionFolder['access']['users'][2]['level'],
                         AccessType.READ)

        # Change phaseAdmin2's access to read-only. This should remove
        # phaseAdmin2 from the submission folder ACL.
        phaseModel.setUserAccess(phase, phaseAdmin2, AccessType.READ, save=True)
        submissionFolder = folderModel.load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 2)
        self.assertEqual(submissionFolder['access']['users'][0]['id'],
                         user1['_id'])
        self.assertEqual(submissionFolder['access']['users'][0]['level'],
                         AccessType.ADMIN)
        self.assertEqual(submissionFolder['access']['users'][1]['id'],
                         phaseAdmin1['_id'])
        self.assertEqual(submissionFolder['access']['users'][1]['level'],
                         AccessType.READ)

        # Verify that the phase can be modified and saved successfully if a
        # submission folder has been deleted
        folderModel.remove(submissionFolder)
        phaseModel.setUserAccess(phase, phaseAdmin1, None, save=True)
