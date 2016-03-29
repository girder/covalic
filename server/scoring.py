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

from collections import defaultdict
import six


def computeAverageScores(score):
    """
    Compute the average score for each metric and add it to the score list
    under the name "Average".

    Datasets with a score of None are omitted from the average calculation.

    :param score: The score object to compute the average of. The result of the
        computation is placed at the head of the list.
    :type score: list
    """
    sums = defaultdict(float)
    counts = defaultdict(int)

    for dataset in score:
        for metric in dataset['metrics']:
            if metric['value'] is not None:
                sums[metric['name']] += float(metric['value'])
                counts[metric['name']] += 1

    metrics = [
        {
            'name': metricName,
            'value': sums[metricName] / float(counts[metricName])
        }
        for metricName in sorted(six.viewkeys(sums))]

    score.insert(0, {
        'dataset': 'Average',
        'metrics': metrics
    })


def computeOverallScore(submission, phase):
    """
    Compute the overall score based on the matrix of individual scores. This
    computes the scalar product of the weighting vector defined by the challenge
    administrators and the average scores in those metrics, using a weight of
    0 for metrics that are not defined by the admins.

    :param submission: The submission to compute the overall score on.
    :param phase: The challenge phase that was submitted to.
    """
    total = 0
    metricInfo = phase.get('metrics', {})
    averages = submission['score'][0]['metrics']

    for metric in averages:
        if metric['name'] in metricInfo:
            total += float(metric['value']) * \
                float(metricInfo[metric['name']].get('weight', 0))

    return total
