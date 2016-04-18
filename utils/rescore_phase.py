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

"""
A command-line client for Covalic to re-run the scoring algorithm on previously
submitted entries to a challenge phase. See https://github.com/girder/covalic.
"""

from __future__ import print_function

import argparse
import datetime
import girder_client

from collections import defaultdict
from time import sleep


class CovalicClient(object):
    """GirderClient wrapper providing convenience functions."""

    def __init__(self, apiUrl, username, password, token, phaseId):
        self.client = girder_client.GirderClient(apiUrl=apiUrl)

        if token is not None:
            self.client.token = token
        else:
            interactive = password is None
            self.client.authenticate(username, password, interactive)

        self.phaseId = phaseId

    def getPhase(self):
        return self.client.get('challenge_phase/' + self.phaseId, {})

    def getSubmissions(self):
        return self.client.get(
            'covalic_submission',
            {
                'phaseId': self.phaseId,
                'limit': 0,
                'sort': 'created',
                'sortdir': 1
            })

    def getJob(self, jobId):
        return self.client.get('job/' + jobId, {})

    def resubmitSubmission(self, submission):
        return self.client.post(
            'covalic_submission',
            {
                'phaseId': self.phaseId,
                'folderId': submission['folderId'],
                'title': submission['title'],
                'date': submission['created'],
                'userId': submission['creatorId']
            })


def printSubmission(submission):
    """Print relevant fields of a submission."""
    fields = ('_id', 'title', 'jobId', 'creatorId', 'creatorName')
    titleWidth = max(map(len, fields))
    for field in fields:
        print('%*s: %s' % (titleWidth, field, submission[field]))


def printSubmissions(submissions):
    """Print a list of submissions."""
    for submission in submissions:
        printSubmission(submission)
        print()


def timestamp():
    """Return a timestamp string."""
    return str(datetime.datetime.now()).split('.')[0]


def pollJobStatus(client, submissions, pollFrequency):
    if not submissions:
        return

    numSubmissions = len(submissions)

    while True:
        # Job status constants from:
        # https://github.com/girder/girder/blob/ce118c8a4cfefb6d320d32de51f5c5471e145b75/plugins/jobs/server/constants.py#L27
        #
        # class JobStatus(object):
        #     INACTIVE = 0
        #     QUEUED = 1
        #     RUNNING = 2
        #     SUCCESS = 3
        #     ERROR = 4
        #     CANCELED = 5

        sleep(pollFrequency)

        failedSubmissions = []
        statusCount = defaultdict(int)

        for submission in submissions:
            job = client.getJob(submission['jobId'])
            status = job['status']
            statusCount[status] += 1
            if status in (4, 5):
                failedSubmissions.append(submission)

        completed = statusCount[3] + statusCount[4] + statusCount[5]
        remaining = numSubmissions - completed

        print('[%s] %d of %d completed...' % (
            timestamp(), completed, numSubmissions))

        if not remaining:
            if failedSubmissions:
                print('\nERROR: %d submissions failed:\n' %
                      len(failedSubmissions))
                printSubmissions(failedSubmissions)

            break


def run(apiUrl, username, password, token, phaseId, dryRun, pollFrequency):
    """Re-run scoring algorithm on all phase submissions."""
    client = CovalicClient(apiUrl, username, password, token, phaseId)

    # Get phase
    phase = client.getPhase()
    print('Found phase "%s" (id: %s)' % (phase['name'], phaseId))

    # Get phase submissions
    submissions = client.getSubmissions()
    print('Found %d submissions:\n' % len(submissions))
    printSubmissions(submissions)

    # Resubmit submissions
    newSubmissions = []
    for submission in submissions:
        print('Resubmitting "%s" from "%s" (id: %s)...' % (
            submission['title'], submission['creatorName'], submission['_id']))
        if dryRun:
            continue

        newSubmission = client.resubmitSubmission(submission)
        newSubmissions.append(newSubmission)

    # Poll job status until complete
    pollJobStatus(client, newSubmissions, pollFrequency)

    print('Done')


def main(args):
    run(args.api_url,
        args.username,
        args.password,
        args.token,
        args.phase_id,
        args.dry_run,
        args.poll_frequency)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-n', '--dry-run', action='store_true',
        help='show what would be done, without making any changes')
    parser.add_argument(
        '--api-url',
        required=True,
        help='full URL to the RESTful API of a Girder server running Covalic '
             '(e.g. http://172.16.1.1:8080/api/v1)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--username')
    group.add_argument('--token')
    parser.add_argument('--password')
    parser.add_argument(
        '--phase-id',
        required=True,
        help='ID of phase on which to re-run scoring algorithm')
    parser.add_argument(
        '-p', '--poll-frequency',
        required=False,
        type=int,
        default=5,
        help='frequency (seconds) at which to poll submission status')

    args = parser.parse_args()
    main(args)
