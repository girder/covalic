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

from girder.constants import AccessType
from girder.models.user import User
from tests import base

from covalic.models.challenge import Challenge
from covalic.models.phase import Phase
from covalic.utility.user_emails import getChallengeUserEmails, getPhaseUserEmails


def setUpModule():
    base.enabledPlugins.append('covalic')
    base.startServer()


def tearDownModule():
    base.stopServer()


class EmailUtilityTestCase(base.TestCase):
    def setUp(self):
        base.TestCase.setUp(self)

        # Create user 1
        user = {
            'email': 'user1@email.com',
            'login': 'user1login',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'user1password',
            'admin': False
        }
        self.user1 = User().createUser(**user)

        # Create user 2
        user = {
            'email': 'user2@email.com',
            'login': 'user2login',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'user2password',
            'admin': False
        }
        self.user2 = User().createUser(**user)

        # Create user 3
        user = {
            'email': 'user3@email.com',
            'login': 'user3login',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'user3password',
            'admin': False
        }
        self.user3 = User().createUser(**user)

        # Create user 4
        user = {
            'email': 'user4@email.com',
            'login': 'user4login',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'user4password',
            'admin': False
        }
        self.user4 = User().createUser(**user)

        # Create user 5
        user = {
            'email': 'user5@email.com',
            'login': 'user5login',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'user5password',
            'admin': False
        }
        self.user5 = User().createUser(**user)

    def testGetChallengeUserEmails(self):
        challenge = Challenge().createChallenge(
            name='challenge 1',
            creator=self.user1,
            public=False)

        # Initially, creator should be the only user
        emails = getChallengeUserEmails(challenge, AccessType.NONE)
        self.assertIn('user1@email.com', emails)
        self.assertEqual(len(emails), 1)

        # Grant challenge access to other users
        Challenge().setUserAccess(challenge, self.user2,
                                  level=AccessType.READ)
        Challenge().setUserAccess(challenge, self.user3,
                                  level=AccessType.WRITE)
        Challenge().setUserAccess(challenge, self.user4,
                                  level=AccessType.ADMIN)
        Challenge().setUserAccess(challenge, self.user5,
                                  level=AccessType.READ)
        Challenge().save(challenge)

        # Verify users with READ access or above
        emails = getChallengeUserEmails(challenge, AccessType.READ)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user2@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertIn('user5@email.com', emails)
        self.assertEqual(len(emails), 5)

        # Verify users with WRITE access or above
        emails = getChallengeUserEmails(challenge, AccessType.WRITE)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertEqual(len(emails), 3)

        # Verify users with ADMIN access or above
        emails = getChallengeUserEmails(challenge, AccessType.ADMIN)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertEqual(len(emails), 2)

    def testGetPhaseAdminEmail(self):
        challenge = Challenge().createChallenge(
            name='challenge 1',
            creator=self.user1,
            public=False)

        phase = Phase().createPhase(
            challenge=challenge,
            name='phase 1',
            creator=self.user1,
            ordinal=0)

        # Initially, creator should be the only user
        emails = getPhaseUserEmails(phase, AccessType.NONE,
                                    includeChallengeUsers=False)
        self.assertIn('user1@email.com', emails)
        self.assertEqual(len(emails), 1)

        # Grant phase access to other users
        Phase().setUserAccess(phase, self.user2, level=AccessType.READ)
        Phase().setUserAccess(phase, self.user3, level=AccessType.WRITE)
        Phase().setUserAccess(phase, self.user4, level=AccessType.ADMIN)
        Phase().setUserAccess(phase, self.user5, level=AccessType.READ)
        Phase().save(phase)

        # Verify users with READ access or above
        emails = getPhaseUserEmails(phase, AccessType.READ,
                                    includeChallengeUsers=False)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user2@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertIn('user5@email.com', emails)
        self.assertEqual(len(emails), 5)

        # Verify users with WRITE access or above
        emails = getPhaseUserEmails(phase, AccessType.WRITE,
                                    includeChallengeUsers=False)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertEqual(len(emails), 3)

        # Verify users with ADMIN access or above
        emails = getPhaseUserEmails(phase, AccessType.ADMIN,
                                    includeChallengeUsers=False)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertEqual(len(emails), 2)

    def testGetPhaseAdminEmailIncludeChallengeAdmins(self):
        challenge = Challenge().createChallenge(
            name='challenge 1',
            creator=self.user1,
            public=False)

        phase = Phase().createPhase(
            challenge=challenge,
            name='phase 1',
            creator=self.user1,
            ordinal=0)

        # Initially, creator should be the only user, and the creator's email
        # should be returned only once
        emails = getPhaseUserEmails(phase, AccessType.NONE,
                                    includeChallengeUsers=True)
        self.assertIn('user1@email.com', emails)
        self.assertEqual(len(emails), 1)

        # Grant challenge access to other users
        Challenge().setUserAccess(challenge, self.user2, level=AccessType.READ)
        Challenge().setUserAccess(challenge, self.user3, level=AccessType.WRITE)
        Challenge().setUserAccess(challenge, self.user4, level=AccessType.ADMIN)
        Challenge().save(challenge)

        # Verify users with READ access or above
        emails = getPhaseUserEmails(phase, AccessType.READ,
                                    includeChallengeUsers=True)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user2@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertEqual(len(emails), 4)

        # Verify users with WRITE access or above
        emails = getPhaseUserEmails(phase, AccessType.WRITE,
                                    includeChallengeUsers=True)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertEqual(len(emails), 3)

        # Verify users with ADMIN access or above
        emails = getPhaseUserEmails(phase, AccessType.ADMIN,
                                    includeChallengeUsers=True)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertEqual(len(emails), 2)

        # Grant phase access to another user
        Phase().setUserAccess(phase, self.user5, level=AccessType.ADMIN)
        Phase().save(phase)

        # Verify users with READ access or above
        emails = getPhaseUserEmails(phase, AccessType.READ,
                                    includeChallengeUsers=True)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user2@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertIn('user5@email.com', emails)
        self.assertEqual(len(emails), 5)

        # Verify users with WRITE access or above
        emails = getPhaseUserEmails(phase, AccessType.WRITE,
                                    includeChallengeUsers=True)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user3@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertIn('user5@email.com', emails)
        self.assertEqual(len(emails), 4)

        # Verify users with ADMIN access or above
        emails = getPhaseUserEmails(phase, AccessType.ADMIN,
                                    includeChallengeUsers=True)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user4@email.com', emails)
        self.assertIn('user5@email.com', emails)
        self.assertEqual(len(emails), 3)

        # Verify that only phase emails are returned when
        # includeChallengeUsers is False
        emails = getPhaseUserEmails(phase, AccessType.NONE,
                                    includeChallengeUsers=False)
        self.assertIn('user1@email.com', emails)
        self.assertIn('user5@email.com', emails)
        self.assertEqual(len(emails), 2)
