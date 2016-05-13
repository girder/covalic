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

import os
import six
import datetime
import dateutil.parser
import dateutil.tz

from tests import base


def setUpModule():
    base.enabledPlugins.append('covalic')
    base.startServer()


def tearDownModule():
    base.stopServer()


class ChallengeTestCase(base.TestCase):
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
        self.user = self.model('user').createUser(**user)

    def testChallengeCreationRequiredParams(self):
        self.ensureRequiredParams(
                path='/challenge',
                method='POST',
                required=['name'],
                user=self.user)

    def testChallengeCreationMinimal(self):
        params = {
            'name': 'challenge'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)

    def testChallengeCreation(self):
        params = {
            'name': 'challenge',
            'description': 'description',
            'instructions': 'instructions',
            'public': True,
            'organizers': 'organizers',
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)

    def testChallengeCreationNoDates(self):
        params = {
            'name': 'challenge',
            'startDate': '',
            'endDate': ''
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)

    def testChallengeCreationStartDateOnly(self):
        params = {
            'name': 'challenge',
            'startDate': '2015-11-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)

    def testChallengeCreationEndDateOnly(self):
        params = {
            'name': 'challenge',
            'endDate': '2015-11-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)

    def testChallengeCreationStartAndEndDates(self):
        params = {
            'name': 'challenge',
            'startDate': '2015-11-01T00:00:00.000Z',
            'endDate': '2015-12-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)

    def testChallengeCreationStartAndEndDatesWrongOrder(self):
        params = {
            'name': 'challenge',
            'startDate': '2015-12-01T00:00:00.000Z',
            'endDate': '2015-11-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertValidationError(resp, 'startDate')

    def testChallengeCreationStartDateValidation(self):
        params = {
            'name': 'challenge',
            'startDate': 'invalid',
            'endDate': '2015-12-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertValidationError(resp, 'startDate')

    def testChallengeCreationEndDateValidation(self):
        params = {
            'name': 'challenge',
            'startDate': '2015-12-01T00:00:00.000Z',
            'endDate': 'invalid'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertValidationError(resp, 'endDate')

    def testListChallenges(self):
        self.model('challenge', 'covalic').createChallenge(
            name='challenge 1',
            creator=self.user,
            description='description',
            instructions='instructions',
            public=False,
            organizers='organizers',
            startDate='2014-11-01T00:00:00.000Z',
            endDate='2014-12-01T00:00:00.000Z')

        resp = self.request(path='/challenge', user=self.user)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 1)

        self.model('challenge', 'covalic').createChallenge(
            name='challenge 2',
            creator=self.user,
            description='description',
            instructions='instructions',
            public=False,
            organizers='organizers',
            startDate='2015-11-01T00:00:00.000Z',
            endDate='2015-12-01T00:00:00.000Z')

        resp = self.request(path='/challenge', user=self.user)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 2)

    def testGetChallenge(self):
        challenge = self.model('challenge', 'covalic').createChallenge(
            name='challenge 1',
            creator=self.user,
            description='description',
            instructions='instructions',
            organizers='organizers',
            startDate='2015-11-01T14:00:00.000Z',
            endDate='2015-12-01T14:00:00.000Z')

        resp = self.request(path='/challenge/%s' % challenge['_id'],
                            user=self.user)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['name'], 'challenge 1')
        self.assertEqual(resp.json['description'], 'description')
        self.assertEqual(resp.json['instructions'], 'instructions')
        self.assertEqual(resp.json['organizers'], 'organizers')
        startDate = dateutil.parser.parse(resp.json['startDate'])
        startDate = startDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(startDate, datetime.datetime(2015, 11, 1, 14, 0, 0, 0,
                                                      dateutil.tz.tzutc()))
        endDate = dateutil.parser.parse(resp.json['endDate'])
        endDate = endDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(endDate, datetime.datetime(2015, 12, 1, 14, 0, 0, 0,
                                                    dateutil.tz.tzutc()))
    def testGetChallengeInvalid(self):
        resp = self.request(path='/challenge/1', user=self.user)
        self.assertValidationError(resp, field='id')

    def testUpdateChallenge(self):
        challenge = self.model('challenge', 'covalic').createChallenge(
            name='challenge 1',
            creator=self.user,
            description='description',
            instructions='instructions',
            organizers='organizers',
            startDate='2015-01-01T14:00:00.000Z',
            endDate='2015-02-01T14:00:00.000Z')

        params = {
            'name': 'challenge 1 updated',
            'description': 'description updated',
            'instructions': 'instructions updated',
            'organizers': 'organizers updated',
            'startDate': '2015-03-01T14:00:00.000Z',
            'endDate': '2015-04-01T14:00:00.000Z'
        }
        resp = self.request(path='/challenge/%s' % challenge['_id'],
                            method='PUT', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['name'], 'challenge 1 updated')
        self.assertEqual(resp.json['description'], 'description updated')
        self.assertEqual(resp.json['instructions'], 'instructions updated')
        self.assertEqual(resp.json['organizers'], 'organizers updated')
        startDate = dateutil.parser.parse(resp.json['startDate'])
        startDate = startDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(startDate, datetime.datetime(2015, 3, 1, 14, 0, 0, 0,
                                                      dateutil.tz.tzutc()))
        endDate = dateutil.parser.parse(resp.json['endDate'])
        endDate = endDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(endDate, datetime.datetime(2015, 4, 1, 14, 0, 0, 0,
                                                    dateutil.tz.tzutc()))
    def testChallengeClearDates(self):
        challenge = self.model('challenge', 'covalic').createChallenge(
            name='challenge',
            creator=self.user,
            startDate='2015-01-01T14:00:00.000Z',
            endDate='2015-02-01T14:00:00.000Z')

        params = {
            'startDate': '',
            'endDate': ''
        }
        resp = self.request(path='/challenge/%s' % challenge['_id'],
                            method='PUT', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertTrue(not resp.json['startDate'])
        self.assertTrue(not resp.json['endDate'])

    def testChallengeDeletion(self):
        challenge = self.model('challenge', 'covalic').createChallenge(
            name='challenge', creator=self.user)

        resp = self.request(path='/challenge/%s' % challenge['_id'],
                            method='DELETE', user=self.user)
        self.assertStatusOk(resp)

    def testChallengeDeletionInvalid(self):
        resp = self.request(path='/challenge/1', method='DELETE', user=self.user)
        self.assertValidationError(resp, 'id')
