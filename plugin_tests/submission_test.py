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

import json
import mock

from tests import base


def setUpModule():
    base.enabledPlugins.append('covalic')
    base.startServer()


def tearDownModule():
    base.stopServer()


class SubmissionBase(base.TestCase):
    def setUp(self):
        super(SubmissionBase, self).setUp()

        from girder.plugins.jobs.models.job import Job
        from girder.plugins.worker.constants import PluginSettings as WorkerSettings
        from girder.plugins.covalic.constants import PluginSettings as CovalicSettings

        self.scheduleJobMock = mock.patch.object(Job, 'scheduleJob')
        self.scheduleJobMock.start()

        self.model('setting').set(WorkerSettings.API_URL, 'http://example.com/api/v1')

        user = {
            'email': 'admin@email.com',
            'login': 'amdinlogin',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'adminpassword',
            'admin': True
        }
        self.admin = self.model('user').createUser(**user)

        user = {
            'email': 'good@email.com',
            'login': 'goodlogin',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'goodpassword',
            'admin': False
        }
        self.user = self.model('user').createUser(**user)

        self.group = self.model('group').createGroup('phase1', self.admin)
        self.model('group').addUser(self.group, self.user)

        user = {
            'email': 'scoring@email.com',
            'login': 'scoringlogin',
            'firstName': 'First',
            'lastName': 'Last',
            'password': 'scoringpassword',
            'admin': False
        }
        self.scoringUser = self.model('user').createUser(**user)
        self.model('setting').set(
            CovalicSettings.SCORING_USER_ID,
            self.scoringUser['_id']
        )

        self.challenge = self.model('challenge', 'covalic').createChallenge(
            name='challenge 1',
            creator=self.admin,
            public=False)

        metrics = {
            'accuracy': {'weight': 0.5},
            'error': {'weight': 0.5}
        }
        self.phase1 = self.model('phase', 'covalic').createPhase(
            'phase 1', self.challenge, creator=self.admin, ordinal=1
        )
        self.phase1['metrics'] = metrics
        self.phase1['active'] = True
        self.phase1['participantGroupId'] = self.group['_id']
        self.model('phase', 'covalic').save(self.phase1)
        self.phase2 = self.model('phase', 'covalic').createPhase(
            'phase 2', self.challenge, creator=self.admin, ordinal=2
        )
        self.phase2['metrics'] = metrics
        self.model('phase', 'covalic').save(self.phase2)

    def tearDown(self):
        self.scheduleJobMock.stop()
        super(SubmissionBase, self).tearDown()

    def createSubmission(self, phase, user, title, score=None, **kwargs):
        folder = self.model('folder').createFolder(
            user, title, parentType='user', creator=user)
        submission = self.model('submission', 'covalic').createSubmission(
            user, phase, folder, title=title, **kwargs)
        if score is not None:
            scoreDict = [{
                'dataset': 'dataset1',
                'metrics': [{
                    'name': 'accuracy',
                    'value': score[0]
                }, {
                    'name': 'error',
                    'value': score[1]
                }]
            }]
            submission['score'] = scoreDict
        return self.model('submission', 'covalic').save(submission)

    def generateSubmissionList(self, userApproaches=None, adminApproaches=None):
        userApproaches = userApproaches or [None, None, None]
        adminApproaches = adminApproaches or [None, None, None]
        for i in range(3):
            score = [
                0.25 * (i + 1),
                0.25 * (4 - i),
            ]
            self.createSubmission(
                self.phase1, self.user, 'User submission %i phase 1' % i, score=score,
                approach=userApproaches[i]
            )
            self.createSubmission(
                self.phase1, self.admin, 'Admin submission %i phase 1' % i, score=score,
                approach=adminApproaches[i]
            )
            self.createSubmission(
                self.phase2, self.user, 'User submission %i phase 2' % i, score=score
            )
            self.createSubmission(
                self.phase2, self.admin, 'Admin submission %i phase 2' % i, score=score
            )


class SubmissionModelTest(SubmissionBase):
    def testCreateAndDelete(self):
        job = self.model('job', 'jobs').createJob(
            title='submission', type='covalic_score', handler='null_handler',
            user=self.user
        )
        submission = self.createSubmission(
            self.phase1, self.user, 'Phase 1 submission',
            job=job,
            organization='org1',
            organizationUrl='http://example.com',
            documentationUrl='http://example.com/docs'
        )

        self.assertIsNotNone(submission)

        # 'default' should be injected as the approach, but it should not be present
        # in the database.
        self.assertEqual(submission['approach'], 'default')
        self.assertNotIn('approach', self.model('submission', 'covalic').findOne(submission['_id']))

        self.model('submission', 'covalic').remove(submission)
        self.assertIsNone(self.model('submission', 'covalic').findOne(submission['_id']))
        self.assertIsNone(self.model('folder').findOne(submission['folderId']))

    def testCreateWithApproach(self):
        submission = self.createSubmission(
            self.phase1, self.user, 'Phase 1 submission',
            approach='Approach 1'
        )
        self.assertIsNotNone(submission)
        self.assertEqual(submission['approach'], 'Approach 1')

    def testCreateWithEmptyStringApproach(self):
        submission = self.createSubmission(
            self.phase1, self.user, 'Phase 1 submission',
            approach=''
        )
        self.assertIsNotNone(submission)
        self.assertEqual(submission['approach'], 'default')

    def testListSubmissionsByPhase(self):
        self.generateSubmissionList()
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, latest=False))
        self.assertEqual(len(submissions), 6)

    def testListSubmissionsByUser(self):
        self.generateSubmissionList()
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, latest=False, userFilter=self.admin))
        self.assertEqual(len(submissions), 3)

    def testListLatestSubmissions(self):
        self.generateSubmissionList()
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, latest=True))
        self.assertEqual(len(submissions), 2)

    def testListByApproach(self):
        userApproaches = ['A', 'C', 'B']
        adminApproaches = ['A', 'default', 'D']
        self.generateSubmissionList(
            userApproaches=userApproaches, adminApproaches=adminApproaches
        )

        # by approach only
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, approach='default', latest=False))
        self.assertEqual(len(submissions), 1)
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, approach='A', latest=False))
        self.assertEqual(len(submissions), 2)

        # by approach and user
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, userFilter=self.user, approach='default', latest=False))
        self.assertEqual(len(submissions), 0)
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, userFilter=self.admin, approach='default', latest=False))
        self.assertEqual(len(submissions), 1)
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, userFilter=self.user, approach='A', latest=False))
        self.assertEqual(len(submissions), 1)

        # approach == '' should be the same as 'default'
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, userFilter=self.admin, approach='', latest=False))
        self.assertEqual(len(submissions), 1)

    def testListLatestByApproach(self):
        userApproaches = ['A', 'A', 'D']
        adminApproaches = ['default', 'D', 'default']
        self.generateSubmissionList(
            userApproaches=userApproaches, adminApproaches=adminApproaches
        )

        # by approach only
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, approach='default'))
        self.assertEqual(len(submissions), 1)
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, approach='D'))
        self.assertEqual(len(submissions), 2)

        # by approach and user
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, userFilter=self.user, approach='default'))
        self.assertEqual(len(submissions), 0)
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, userFilter=self.admin, approach='default'))
        self.assertEqual(len(submissions), 2)
        submissions = list(self.model('submission', 'covalic').list(
            self.phase1, userFilter=self.user, approach='D'))
        self.assertEqual(len(submissions), 1)

    def testListSubmissionApproaches(self):
        userApproaches = ['A', 'c', 'b']
        adminApproaches = ['A', 'default', 'd']
        self.generateSubmissionList(
            userApproaches=userApproaches, adminApproaches=adminApproaches
        )

        # list all globally
        self.assertEqual(
            self.model('submission', 'covalic').listApproaches(),
            ['A', 'b', 'c', 'd', 'default']
        )

        # list by phase
        self.assertEqual(
            self.model('submission', 'covalic').listApproaches(phase=self.phase1),
            ['A', 'b', 'c', 'd', 'default']
        )
        self.assertEqual(
            self.model('submission', 'covalic').listApproaches(phase=self.phase2),
            ['default']
        )

        # list by user
        self.assertEqual(
            self.model('submission', 'covalic').listApproaches(user=self.admin),
            ['A', 'd', 'default']
        )
        self.assertEqual(
            self.model('submission', 'covalic').listApproaches(user=self.user),
            ['A', 'b', 'c', 'default']
        )

        # list by user and phase
        self.assertEqual(
            self.model('submission', 'covalic').listApproaches(user=self.admin, phase=self.phase1),
            ['A', 'd', 'default']
        )
        self.assertEqual(
            self.model('submission', 'covalic').listApproaches(user=self.user, phase=self.phase2),
            ['default']
        )

    def testRecomputeOverallScores(self):
        self.generateSubmissionList()

        submission = self.model('submission', 'covalic').findOne(
            {'title': 'User submission 0 phase 1'})
        self.assertEqual(submission['overallScore'], (1.0 + 0.25) / 2.0)

        self.phase1['metrics'] = {
            'accuracy': {'weight': 0.3},
            'error': {'weight': 0.7}
        }
        self.model('phase', 'covalic').save(self.phase1)
        self.model('submission', 'covalic').recomputeOverallScores(self.phase1)

        submission = self.model('submission', 'covalic').findOne(
            {'title': 'User submission 0 phase 1'})
        self.assertEqual(submission['overallScore'], 0.25 * 0.3 + 1.0 * 0.7)

    def testCreateUnscored(self):
        self.generateSubmissionList()
        submission = self.createSubmission(self.phase1, self.user, 'no score')
        self.assertNotIn('latest', submission)
        latest = self.model('submission', 'covalic').findOne({'title': 'User submission 2 phase 1'})
        self.assertEqual(latest['latest'], True)

    def testScoreSubmission(self):
        submission = self.createSubmission(self.phase1, self.user, 'submission')
        self.assertNotIn('jobId', submission)

        submission = self.model('submission', 'covalic').scoreSubmission(
            submission, 'http://127.0.0.1/api/v1')
        self.assertIn('jobId', submission)

        job = self.model('job', 'jobs').load(submission['jobId'], force=True)
        self.assertIsNotNone(job)


class SubmissionRestTest(SubmissionBase):
    def setUp(self):
        super(SubmissionRestTest, self).setUp()

    def testCRUDSubmissionAsAdmin(self):
        folder = self.model('folder').createFolder(
            self.admin, 'submission phase 1', parentType='user', creator=self.admin
        )

        # submit a submission on behalf of the user
        resp = self.request(
            path='/covalic_submission', method='POST', user=self.admin,
            params={
                'phaseId': self.phase1['_id'],
                'folderId': folder['_id'],
                'title': 'submission phase 1',
                'userId': self.user['_id'],
                'date': '2000-01-01 00:00:00'
            }
        )
        self.assertStatusOk(resp)
        self.assertDictContains({
            'approach': 'default',
            'created': '2000-01-01T00:00:00+00:00',
            'creatorId': str(self.user['_id']),
            'creatorName': 'First Last',
            'folderId': str(folder['_id']),
            'phaseId': str(self.phase1['_id']),
            'title': 'submission phase 1'
        }, resp.json)
        self.assertIn('jobId', resp.json)
        id = resp.json['_id']

        # modify a submission
        resp = self.request(
            path='/covalic_submission/%s' % id, method='PUT', user=self.admin,
            params={
                'approach': 'A',
                'title': 'modified title',
                'date': '2010-01-01 00:00:00',
                'organization': 'org',
                'organizationUrl': 'http://org.com',
                'documentationUrl': 'http://org.com/docs',
                'disqualified': True
            }
        )
        self.assertStatusOk(resp)
        self.assertDictContains({
            'approach': 'A',
            'created': '2010-01-01T00:00:00+00:00',
            'title': 'modified title',
            'latest': False,
            'organization': 'org',
            'organizationUrl': 'http://org.com',
            'documentationUrl': 'http://org.com/docs',
        }, resp.json)

        resp = self.request(
            path='/covalic_submission/%s' % id, user=self.admin
        )
        self.assertStatusOk(resp)

        # delete the submission and ensure it is gone
        resp = self.request(
            path='/covalic_submission/%s' % id, method='DELETE', user=self.admin
        )
        self.assertStatusOk(resp)
        resp = self.request(
            path='/covalic_submission/%s' % id, user=self.admin
        )
        self.assertStatus(resp, 400)

    def testCRUDSubmissionAsUser(self):
        folder = self.model('folder').createFolder(
            self.user, 'submission phase 1', parentType='user', creator=self.user
        )
        # user cannot override date
        resp = self.request(
            path='/covalic_submission', method='POST', user=self.user,
            params={
                'phaseId': self.phase1['_id'],
                'folderId': folder['_id'],
                'title': 'submission phase 1',
                'date': '2000-01-01 00:00:00',
                'approach': 'A'
            }
        )
        self.assertStatus(resp, 403)

        # user cannot override user
        resp = self.request(
            path='/covalic_submission', method='POST', user=self.user,
            params={
                'phaseId': self.phase1['_id'],
                'folderId': folder['_id'],
                'title': 'submission phase 1',
                'userId': self.admin['_id'],
                'approach': 'A'
            }
        )
        self.assertStatus(resp, 403)

        # user cannot post to an inactive phase
        resp = self.request(
            path='/covalic_submission', method='POST', user=self.user,
            params={
                'phaseId': self.phase2['_id'],
                'folderId': folder['_id'],
                'title': 'submission phase 1',
                'approach': 'A'
            }
        )
        self.assertStatus(resp, 400)

        # successful submission
        resp = self.request(
            path='/covalic_submission', method='POST', user=self.user,
            params={
                'phaseId': self.phase1['_id'],
                'folderId': folder['_id'],
                'title': 'submission phase 1',
                'approach': 'A'
            }
        )
        self.assertStatusOk(resp)
        self.assertDictContains({
            'approach': 'A',
            'creatorId': str(self.user['_id']),
            'creatorName': 'First Last',
            'folderId': str(folder['_id']),
            'phaseId': str(self.phase1['_id']),
            'title': 'submission phase 1'
        }, resp.json)
        self.assertIn('jobId', resp.json)
        id = resp.json['_id']

        # user cannot modify submissions
        resp = self.request(
            path='/covalic_submission/%s' % id, method='PUT', user=self.user,
            params={
                'title': 'modified title'
            }
        )
        self.assertStatus(resp, 403)

        # delete the submission and ensure it is gone
        resp = self.request(
            path='/covalic_submission/%s' % id, method='DELETE', user=self.user
        )
        self.assertStatusOk(resp)
        resp = self.request(
            path='/covalic_submission/%s' % id, user=self.admin
        )
        self.assertStatus(resp, 400)

    def testListSubmissions(self):
        self.generateSubmissionList()
        resp = self.request(
            path='/covalic_submission', user=self.user,
            params={'phaseId': self.phase1['_id']}
        )
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 2)

        resp = self.request(
            path='/covalic_submission', user=self.user,
            params={'phaseId': self.phase1['_id'], 'latest': False}
        )
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 6)

        resp = self.request(
            path='/covalic_submission', user=self.user,
            params={'phaseId': self.phase1['_id'], 'userId': self.user['_id']}
        )
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 3)

    def testListUserApproaches(self):
        userApproaches = ['A', 'c', 'b']
        adminApproaches = ['A', 'default', 'd']
        self.generateSubmissionList(
            userApproaches=userApproaches, adminApproaches=adminApproaches
        )

        # all for the current user
        resp = self.request(path='/covalic_submission/approaches', user=self.admin)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, ['A', 'd', 'default'])
        resp = self.request(path='/covalic_submission/approaches', user=self.user)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, ['A', 'b', 'c', 'default'])

        # by phase for the current user
        resp = self.request(
            path='/covalic_submission/approaches', user=self.admin,
            params={'phaseId': self.phase1['_id']}
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, ['A', 'd', 'default'])
        resp = self.request(
            path='/covalic_submission/approaches', user=self.user,
            params={'phaseId': self.phase2['_id']}
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, ['default'])

        # for a specific user as admin
        resp = self.request(
            path='/covalic_submission/approaches', user=self.admin,
            params={'phaseId': self.phase1['_id'], 'userId': self.user['_id']}
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, ['A', 'b', 'c', 'default'])

        # for self as non-admin
        resp = self.request(
            path='/covalic_submission/approaches', user=self.user,
            params={'phaseId': self.phase1['_id'], 'userId': self.user['_id']}
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, ['A', 'b', 'c', 'default'])

        # a normal user cannot query approaches for another user
        resp = self.request(
            path='/covalic_submission/approaches', user=self.user,
            params={'phaseId': self.phase1['_id'], 'userId': self.admin['_id']}
        )
        self.assertStatus(resp, 403)

    def testPostScore(self):
        submission = self.createSubmission(self.phase1, self.user, 'submission')

        score = json.dumps([{
            'dataset': 'dataset1',
            'metrics': [{
                'name': 'accuracy',
                'value': 0.1
            }, {
                'name': 'error',
                'value': 0.9
            }]
        }, {
            'dataset': 'dataset2',
            'metrics': [{
                'name': 'accuracy',
                'value': 0.3
            }, {
                'name': 'error',
                'value': None
            }]
        }])
        # users cannot submit scores
        resp = self.request(
            path='/covalic_submission/%s/score' % str(submission['_id']),
            method='POST', user=self.user,
            body=score, type='application/json'
        )
        self.assertStatus(resp, 403)

        # post a score as admin
        resp = self.request(
            path='/covalic_submission/%s/score' % str(submission['_id']),
            method='POST', user=self.admin,
            body=score, type='application/json'
        )
        self.assertStatus(resp, 200)

        # assert the score was added
        resp = self.request(
            path='/covalic_submission/%s' % str(submission['_id']), user=self.user
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['overallScore'], (0.2 + 0.9) / 2.0)
        self.assertEqual(resp.json['score'], [{
            'dataset': 'Average',
            'metrics': [{
                'name': 'accuracy',
                'value': 0.2
            }, {
                'name': 'error',
                'value': 0.9
            }]
        }, {
            'dataset': 'dataset1',
            'metrics': [{
                'name': 'accuracy',
                'value': 0.1
            }, {
                'name': 'error',
                'value': 0.9
            }]
        }, {
            'dataset': 'dataset2',
            'metrics': [{
                'name': 'accuracy',
                'value': 0.3
            }, {
                'name': 'error',
                'value': None
            }]
        }])

    def testPostRescore(self):
        submission1 = self.createSubmission(self.phase1, self.user, 'submission1')
        submission2 = self.createSubmission(self.phase1, self.user, 'submission2')

        score = json.dumps([{
            'dataset': 'dataset1',
            'metrics': [{
                'name': 'accuracy',
                'value': 0.1
            }, {
                'name': 'error',
                'value': 0.9
            }]
        }])

        # post scores as admin
        for submission in [submission1, submission2]:
            resp = self.request(
                path='/covalic_submission/%s/score' % str(submission['_id']),
                method='POST', user=self.admin,
                body=score, type='application/json'
            )
            self.assertStatus(resp, 200)

        # cannot re-score submissions that aren't 'latest'
        resp = self.request(
            path='/covalic_submission/%s/rescore' % submission1['_id'],
            method='POST', user=self.admin
        )
        self.assertStatus(resp, 400)

        # re-score submission as admin
        resp = self.request(
            path='/covalic_submission/%s/rescore' % submission2['_id'],
            method='POST', user=self.admin
        )
        self.assertStatusOk(resp)
        self.assertIn('jobId', resp.json)

        # user cannot re-score submission
        resp = self.request(
            path='/covalic_submission/%s/rescore' % submission2['_id'],
            method='POST', user=self.user
        )
        self.assertStatus(resp, 403)

    def testSubmissionWithMetadata(self):
        folder = self.model('folder').createFolder(
            self.admin, 'submission phase 1', parentType='user', creator=self.user
        )
        resp = self.request(
            path='/covalic_submission', method='POST', user=self.user,
            params={
                'phaseId': self.phase1['_id'],
                'folderId': folder['_id'],
                'title': 'submission phase 1',
                'meta': '{"test": 1}'
            }
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['meta'], {'test': 1})

        resp = self.request(
            path='/covalic_submission/%s' % resp.json['_id'],
            method='PUT', user=self.admin,
            params={
                'meta': '{"test2": 2}'
            }
        )
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['meta'], {'test2': 2})
