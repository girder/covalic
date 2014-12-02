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

def computeAverageScores(score):
    """
    Compute the average score for each metric and add it as the _avg key
    under each metric in the score dict.

    :param score: The score object (metric-major, dataset-minor grouping)
    :type score: dict
    """
    for column in score:
        scores = [d['value'] for d in column['datasets']]
        column['_avg'] = sum(scores) / float(len(scores))


def computeOverallScore(score):
    """
    Compute the overall score based on the matrix of individual scores. The
    computed value will be used to define the total ordering of submissions
    to a given phase.

    :param score: The score object (metric-major, dataset-minor grouping)
    :type score: dict
    """
    pass  # TODO
