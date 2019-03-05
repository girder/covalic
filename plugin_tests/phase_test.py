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
import dateutil.parser
import dateutil.tz
import json
import mock

from tests import base


def setUpModule():
    base.enabledPlugins.append('covalic')
    base.startServer()


def tearDownModule():
    base.stopServer()


class PhaseTestCase(base.TestCase):
    def setUp(self):
        base.TestCase.setUp(self)

        adminUser = {
            'email': 'admin@email.com',
            'login': 'adminlogin',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'adminpassword',
            'admin': True
        }
        self.admin = self.model('user').createUser(**adminUser)

        user = {
            'email': 'good@email.com',
            'login': 'goodlogin',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'goodpassword',
            'admin': False
        }
        self.user = self.model('user').createUser(**user)

        self.challenge = self.model('challenge', 'covalic').createChallenge(
            name='challenge 1',
            creator=self.user,
            public=False)

    def testPhaseCreationMinimal(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'phase'
        }
        resp = self.request(path='/challenge_phase', method='POST',
                            user=self.user, params=params)
        self.assertStatusOk(resp)

    def testPhaseCreation(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'phase',
            'description': 'description',
            'instructions': 'instructions',
            'active': True
        }
        resp = self.request(path='/challenge_phase', method='POST',
                            user=self.user, params=params)
        self.assertStatusOk(resp)

    def testPhaseCreationNoDates(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'startDate': '',
            'endDate': ''
        }
        resp = self.request(path='/challenge_phase', method='POST',
                            user=self.user, params=params)
        self.assertStatusOk(resp)

    def testPhaseCreationStartDateOnly(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'startDate': '2015-11-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge_phase', method='POST',
                            user=self.user, params=params)
        self.assertStatusOk(resp)

    def testPhaseCreationEndDateOnly(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'endDate': '2015-11-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge_phase', method='POST',
                            user=self.user, params=params)
        self.assertStatusOk(resp)

    def testPhaseCreationStartAndEndDates(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'startDate': '2015-11-01T00:00:00.000Z',
            'endDate': '2015-12-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)

    def testPhaseCreationStartAndEndDatesWrongOrder(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'startDate': '2015-12-01T00:00:00.000Z',
            'endDate': '2015-11-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertValidationError(resp, 'startDate')

    def testPhaseCreationStartDateValidation(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'startDate': 'invalid',
            'endDate': '2015-12-01T00:00:00.000Z'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertValidationError(resp, 'startDate')

    def testPhaseCreationEndDateValidation(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'startDate': '2015-12-01T00:00:00.000Z',
            'endDate': 'invalid'
        }
        resp = self.request(path='/challenge', method='POST', user=self.user,
                            params=params)
        self.assertValidationError(resp, 'endDate')

    def testPhaseCreationWithMetadata(self):
        params = {
            'challengeId': str(self.challenge['_id']),
            'name': 'challenge',
            'meta': json.dumps({'test': 1})
        }
        resp = self.request(path='/challenge_phase', method='POST', user=self.user,
                            params=params)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json.get('meta'), {'test': 1})

        resp = self.request(path='/challenge_phase/%s' % resp.json['_id'], method='GET',
                            user=self.user)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json.get('meta'), {'test': 1})

    def testListPhase(self):
        self.model('phase', 'covalic').createPhase(
            challenge=self.challenge,
            name='phase 1',
            creator=self.user,
            ordinal=0)

        params = {
            'challengeId': str(self.challenge['_id'])
        }
        resp = self.request(path='/challenge_phase', user=self.user,
                            params=params)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 1)

        self.model('phase', 'covalic').createPhase(
            challenge=self.challenge,
            name='phase 2',
            creator=self.user,
            ordinal=1)

        resp = self.request(path='/challenge_phase', user=self.user,
                            params=params)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 2)

    def testGetPhase(self):
        phase = self.model('phase', 'covalic').createPhase(
            challenge=self.challenge,
            name='phase 1',
            creator=self.user,
            ordinal=1,
            description='description',
            instructions='instructions',
            active=True,
            startDate='2015-11-01T14:00:00.000Z',
            endDate='2015-12-01T14:00:00.000Z',
            type='type',
            hideScores=True,
            matchSubmissions=False,
            enableOrganization=True,
            enableOrganizationUrl=True,
            enableDocumentationUrl=True,
            requireOrganization=False,
            requireOrganizationUrl=False,
            requireDocumentationUrl=False)

        resp = self.request(path='/challenge_phase/%s' % phase['_id'],
                            user=self.user)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['challengeId'], str(self.challenge['_id']))
        self.assertEqual(resp.json['name'], 'phase 1')
        self.assertEqual(resp.json['ordinal'], 1)
        self.assertEqual(resp.json['description'], 'description')
        self.assertEqual(resp.json['instructions'], 'instructions')
        self.assertTrue(resp.json['active'])
        startDate = dateutil.parser.parse(resp.json['startDate'])
        startDate = startDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(startDate, datetime.datetime(2015, 11, 1, 14, 0, 0, 0,
                                                      dateutil.tz.tzutc()))
        endDate = dateutil.parser.parse(resp.json['endDate'])
        endDate = endDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(endDate, datetime.datetime(2015, 12, 1, 14, 0, 0, 0,
                                                    dateutil.tz.tzutc()))
        self.assertEqual(resp.json['type'], 'type')
        self.assertTrue(resp.json['hideScores'])
        self.assertFalse(resp.json['matchSubmissions'])
        self.assertTrue(resp.json['enableOrganization'])
        self.assertTrue(resp.json['enableOrganizationUrl'])
        self.assertTrue(resp.json['enableDocumentationUrl'])
        self.assertFalse(resp.json['requireOrganization'])
        self.assertFalse(resp.json['requireOrganizationUrl'])
        self.assertFalse(resp.json['requireDocumentationUrl'])

    def testGetPhaseInvalid(self):
        resp = self.request(path='/challenge_phase/1', user=self.user)
        self.assertValidationError(resp, field='id')

    def testUpdatePhase(self):
        phase = self.model('phase', 'covalic').createPhase(
            challenge=self.challenge,
            name='phase 1',
            creator=self.user,
            ordinal=1,
            description='description',
            instructions='instructions',
            active=True,
            startDate='2015-11-01T14:00:00.000Z',
            endDate='2015-12-01T14:00:00.000Z',
            type='type',
            hideScores=True,
            matchSubmissions=False,
            enableOrganization=True,
            enableOrganizationUrl=True,
            enableDocumentationUrl=True,
            requireOrganization=False,
            requireOrganizationUrl=False,
            requireDocumentationUrl=False)

        params = {
            'name': 'phase 1 updated',
            'ordinal': 2,
            'description': 'description updated',
            'instructions': 'instructions updated',
            'active': False,
            'startDate': '2015-03-01T14:00:00.000Z',
            'endDate': '2015-04-01T14:00:00.000Z',
            'type': 'type updated',
            'hideScores': False,
            'matchSubmissions': True,
            'enableOrganization': False,
            'enableOrganizationUrl': False,
            'enableDocumentationUrl': False,
            'requireOrganization': True,
            'requireOrganizationUrl': True,
            'requireDocumentationUrl': True
        }
        resp = self.request(path='/challenge_phase/%s' % phase['_id'],
                            method='PUT', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['name'], 'phase 1 updated')
        self.assertEqual(resp.json['ordinal'], 2)
        self.assertEqual(resp.json['description'], 'description updated')
        self.assertEqual(resp.json['instructions'], 'instructions updated')
        self.assertFalse(resp.json['active'])
        startDate = dateutil.parser.parse(resp.json['startDate'])
        startDate = startDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(startDate, datetime.datetime(2015, 3, 1, 14, 0, 0, 0,
                                                      dateutil.tz.tzutc()))
        endDate = dateutil.parser.parse(resp.json['endDate'])
        endDate = endDate.replace(tzinfo=dateutil.tz.tzutc())
        self.assertEqual(endDate, datetime.datetime(2015, 4, 1, 14, 0, 0, 0,
                                                    dateutil.tz.tzutc()))
        self.assertEqual(resp.json['type'], 'type updated')
        self.assertFalse(resp.json['hideScores'])
        self.assertTrue(resp.json['matchSubmissions'])
        self.assertFalse(resp.json['enableOrganization'])
        self.assertFalse(resp.json['enableOrganizationUrl'])
        self.assertFalse(resp.json['enableDocumentationUrl'])
        self.assertTrue(resp.json['requireOrganization'])
        self.assertTrue(resp.json['requireOrganizationUrl'])
        self.assertTrue(resp.json['requireDocumentationUrl'])

    def testPhaseUpdateMetadata(self):
        phase = self.model('phase', 'covalic').createPhase(
            challenge=self.challenge,
            name='phase 1',
            creator=self.user,
            ordinal=1,
            meta={'test': 1}
        )
        params = {
            'meta': json.dumps({'test2': 2})
        }
        resp = self.request(path='/challenge_phase/%s' % phase['_id'],
                            method='PUT', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json.get('meta'), {'test2': 2})

    def testPhaseClearDates(self):
        phase = self.model('phase', 'covalic').createPhase(
            challenge=self.challenge,
            name='phase',
            creator=self.user,
            ordinal=1,
            startDate='2015-11-01T14:00:00.000Z',
            endDate='2015-12-01T14:00:00.000Z')

        params = {
            'startDate': '',
            'endDate': ''
        }
        resp = self.request(path='/challenge_phase/%s' % phase['_id'],
                            method='PUT', user=self.user, params=params)
        self.assertStatusOk(resp)
        self.assertTrue(not resp.json['startDate'])
        self.assertTrue(not resp.json['endDate'])

    def testPhaseDeletion(self):
        phase = self.model('phase', 'covalic').createPhase(
            challenge=self.challenge,
            name='phase',
            creator=self.user,
            ordinal=0)

        resp = self.request(path='/challenge_phase/%s' % phase['_id'],
                            method='DELETE', user=self.user)
        self.assertStatusOk(resp)

    def testPhaseDeletionInvalid(self):
        resp = self.request(path='/challenge_phase/1', method='DELETE',
                            user=self.user)
        self.assertValidationError(resp, 'id')

    def testPhaseRescore(self):
        from girder.plugins.covalic.constants import PluginSettings as CovalicSettings
        from girder.plugins.jobs.models.job import Job

        # Configure scoring user
        scoringUserParams = {
            'email': 'scoring@email.com',
            'login': 'scoringlogin',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'scoringpassword',
            'admin': False
        }
        scoringUser = self.model('user').createUser(**scoringUserParams)

        self.model('setting').set(
            CovalicSettings.SCORING_USER_ID,
            scoringUser['_id']
        )

        # Create phase
        metrics = {
            'accuracy': {'weight': 0.5},
            'error': {'weight': 0.5}
        }
        phase = self.model('phase', 'covalic').createPhase(
            'phase 1', self.challenge, creator=self.user, ordinal=1)
        phase['metrics'] = metrics
        phase['active'] = True
        phase = self.model('phase', 'covalic').save(phase)

        # Create submission
        folder = self.model('folder').createFolder(
            self.user, 'submission', parentType='user', creator=self.user)
        submission = self.model('submission', 'covalic').createSubmission(
            self.user, phase, folder, title='submission')

        # Add score to submission
        scoreDict = [{
            'dataset': 'dataset1',
            'metrics': [{
                'name': 'accuracy',
                'value': 0.9
            }, {
                'name': 'error',
                'value': 0.1
            }]
        }]
        submission['score'] = scoreDict
        submission = self.model('submission', 'covalic').save(submission)

        # User can't re-score phase
        resp = self.request(path='/challenge_phase/%s/rescore' % phase['_id'], method='POST',
                            user=self.user)
        self.assertStatus(resp, 403)

        # Rescore phase as admin
        self.assertNotIn('jobId', submission)
        with mock.patch.object(Job, 'scheduleJob'):
            resp = self.request(path='/challenge_phase/%s/rescore' % phase['_id'], method='POST',
                                user=self.admin)
            self.assertStatusOk(resp)

        submission = self.model('submission', 'covalic').load(submission['_id'])
        self.assertIn('jobId', submission)
