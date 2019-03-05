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

import datetime

from girder.models.user import User
from tests import base

from covalic.models.challenge import Challenge


def setUpModule():
    base.enabledPlugins.append('covalic')
    base.startServer()


def tearDownModule():
    base.stopServer()


class ChallengeTimeframeTestCase(base.TestCase):
    def setUp(self):
        base.TestCase.setUp(self)

        user = {
            'email': 'good@email.com',
            'login': 'goodlogin',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'goodpassword',
            'admin': False
        }
        self.user = User().createUser(**user)

        # Create sets of challenges with combinations of specified/empty/null
        # start/end dates

        now = datetime.datetime.utcnow()
        date1 = now - datetime.timedelta(2)
        date2 = now - datetime.timedelta(1)
        date3 = now + datetime.timedelta(1)
        date4 = now + datetime.timedelta(2)

        # Neither date specified
        Challenge().createChallenge(
            name='neither (null)',
            creator=self.user,
            startDate=None,
            endDate=None)
        Challenge().createChallenge(
            name='neither (empty)',
            creator=self.user,
            startDate='',
            endDate='')

        # Only start date specified
        Challenge().createChallenge(
            name='only start, in past (null)',
            creator=self.user,
            startDate=date2,
            endDate=None)
        Challenge().createChallenge(
            name='only start, in past (empty)',
            creator=self.user,
            startDate=date2,
            endDate='')
        Challenge().createChallenge(
            name='only start, in future (null)',
            creator=self.user,
            startDate=date3,
            endDate=None)
        Challenge().createChallenge(
            name='only start, in future (empty)',
            creator=self.user,
            startDate=date3,
            endDate='')

        # Only end date specified
        Challenge().createChallenge(
            name='only end, in past (null)',
            creator=self.user,
            startDate=None,
            endDate=date2)
        Challenge().createChallenge(
            name='only end, in past (empty)',
            creator=self.user,
            startDate='',
            endDate=date2)
        Challenge().createChallenge(
            name='only end, in future (null)',
            creator=self.user,
            startDate=None,
            endDate=date3)
        Challenge().createChallenge(
            name='only end, in future (empty)',
            creator=self.user,
            startDate='',
            endDate=date3)

        # Both dates specified
        Challenge().createChallenge(
            name='both, in past',
            creator=self.user,
            startDate=date1,
            endDate=date2)
        Challenge().createChallenge(
            name='both, active',
            creator=self.user,
            startDate=date2,
            endDate=date3)
        Challenge().createChallenge(
            name='both, in future',
            creator=self.user,
            startDate=date3,
            endDate=date4)

    def testListAllChallenges(self):
        params = {
            'timeframe': 'all'
        }
        resp = self.request(path='/challenge', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 13)

    def testListActiveChallenges(self):
        params = {
            'timeframe': 'active'
        }
        resp = self.request(path='/challenge', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 7)
        self.assertEqual(resp.json[0]['name'], 'both, active')
        self.assertEqual(resp.json[1]['name'], 'neither (empty)')
        self.assertEqual(resp.json[2]['name'], 'neither (null)')
        self.assertEqual(resp.json[3]['name'], 'only end, in future (empty)')
        self.assertEqual(resp.json[4]['name'], 'only end, in future (null)')
        self.assertEqual(resp.json[5]['name'], 'only start, in past (empty)')
        self.assertEqual(resp.json[6]['name'], 'only start, in past (null)')

    def testListUpcomingChallenges(self):
        params = {
            'timeframe': 'upcoming'
        }
        resp = self.request(path='/challenge', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 3)
        self.assertEqual(resp.json[0]['name'], 'both, in future')
        self.assertEqual(resp.json[1]['name'], 'only start, in future (empty)')
        self.assertEqual(resp.json[2]['name'], 'only start, in future (null)')
