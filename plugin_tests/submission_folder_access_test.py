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

import six

from girder.constants import AccessType
from girder.models.folder import Folder
from girder.models.user import User
from tests import base

from covalic.models.challenge import Challenge
from covalic.models.phase import Phase
from covalic.models.submission import Submission


def setUpModule():
    base.enabledPlugins.append('covalic')
    base.startServer()


def tearDownModule():
    base.stopServer()


class SubmissionFolderAccessTestCase(base.TestCase):
    @staticmethod
    def _filterUserAccessKeys(folder):
        """
        Filter a folder's user access control list to contain only keys relevant
        for this test. In certain workflows,
        AccessControlledModel.getFullAccessList() adds additional keys such as
        'login' and 'name'. Removing the additional keys simplifies writing
        equality assertions.
        """
        for item in folder['access']['users']:
            toDelete = [key for key in six.viewkeys(item)
                        if key not in ('id', 'level')]
            for key in toDelete:
                del item[key]

    def testSubmissionFolderAccess(self):
        # Create users
        challengeAdmin = User().createUser(
            email='challenge@email.com', login='challenge',
            firstName='Challenge', lastName='Admin', password='passwd')
        phaseAdmin1 = User().createUser(
            email='phase1@email.com', login='phase1',
            firstName='Phase', lastName='Admin 1', password='passwd')
        phaseAdmin2 = User().createUser(
            email='phase2@email.com', login='phase2',
            firstName='Phase', lastName='Admin 2', password='passwd')
        user1 = User().createUser(
            email='user1@email.com', login='user1',
            firstName='User', lastName='1', password='passwd')

        # Create challenge and phase
        challenge = Challenge().createChallenge(
            name='challenge 1', creator=challengeAdmin, public=False)
        phase = Phase().createPhase(
            name='phase 1', challenge=challenge, creator=phaseAdmin1,
            ordinal=1)

        # Add phaseAdmin2 and user 1 as phase admins
        Phase().setUserAccess(phase, phaseAdmin2, AccessType.WRITE,
                              save=True)
        Phase().setUserAccess(phase, user1, AccessType.WRITE, save=True)

        # Create folder and submission as user1
        submissionFolder = Folder().createFolder(
            parent=user1, name='submission 1', parentType='user', creator=user1)
        Submission().createSubmission(
            creator=user1, phase=phase, folder=submissionFolder)

        # Submission folder ACL should include phase admins with read access
        submissionFolder = Folder().load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 3)
        self._filterUserAccessKeys(submissionFolder)
        six.assertCountEqual(self, submissionFolder['access']['users'], [
            {
                'id': user1['_id'],
                'level': AccessType.ADMIN
            },
            {
                'id': phaseAdmin1['_id'],
                'level': AccessType.READ
            },
            {
                'id': phaseAdmin2['_id'],
                'level': AccessType.READ
            }
        ])

        # Remove user1 as phase admin. This shouldn't change folder ACL because
        # user1 is the folder's owner.
        Phase().setUserAccess(phase, user1, None, save=True)
        submissionFolder = Folder().load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 3)
        self._filterUserAccessKeys(submissionFolder)
        six.assertCountEqual(self, submissionFolder['access']['users'], [
            {
                'id': user1['_id'],
                'level': AccessType.ADMIN
            },
            {
                'id': phaseAdmin1['_id'],
                'level': AccessType.READ
            },
            {
                'id': phaseAdmin2['_id'],
                'level': AccessType.READ
            }
        ])

        # Remove phaseAdmin2 as a phase admin. This should remove phaseAdmin2
        # from the submission folder ACL.
        Phase().setUserAccess(phase, phaseAdmin2, None, save=True)
        submissionFolder = Folder().load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 2)
        self._filterUserAccessKeys(submissionFolder)
        six.assertCountEqual(self, submissionFolder['access']['users'], [
            {
                'id': user1['_id'],
                'level': AccessType.ADMIN
            },
            {
                'id': phaseAdmin1['_id'],
                'level': AccessType.READ
            }
        ])

        # Re-add phaseAdmin2 as phase admin. This should add phaseAdmin2 back to
        # the submission folder ACL.
        Phase().setUserAccess(phase, phaseAdmin2, AccessType.WRITE,
                              save=True)
        submissionFolder = Folder().load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 3)
        self._filterUserAccessKeys(submissionFolder)
        six.assertCountEqual(self, submissionFolder['access']['users'], [
            {
                'id': user1['_id'],
                'level': AccessType.ADMIN
            },
            {
                'id': phaseAdmin1['_id'],
                'level': AccessType.READ
            },
            {
                'id': phaseAdmin2['_id'],
                'level': AccessType.READ
            }
        ])

        # Change phaseAdmin2's access to read-only. This should remove
        # phaseAdmin2 from the submission folder ACL.
        Phase().setUserAccess(phase, phaseAdmin2, AccessType.READ, save=True)
        submissionFolder = Folder().load(
            submissionFolder['_id'], force=True, exc=True)
        self.assertEqual(len(submissionFolder['access']['users']), 2)
        self._filterUserAccessKeys(submissionFolder)
        six.assertCountEqual(self, submissionFolder['access']['users'], [
            {
                'id': user1['_id'],
                'level': AccessType.ADMIN
            },
            {
                'id': phaseAdmin1['_id'],
                'level': AccessType.READ
            }
        ])

        # Verify that the phase can be modified and saved successfully if a
        # submission folder has been deleted
        Folder().remove(submissionFolder)
        Phase().setUserAccess(phase, phaseAdmin1, None, save=True)
