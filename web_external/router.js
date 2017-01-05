import _ from 'underscore';
import Backbone from 'backbone';
import events from 'girder/events';
import girderRouter from 'girder/router';
import { AccessType } from 'girder/constants';
import { parseQueryString } from 'girder/misc';

girderRouter.enabled(false);

var router = new Backbone.Router();

export default router;

// Setup app routes
import FrontPageView from './views/body/FrontPageView';
router.route('', 'index', function () {
    events.trigger('g:navigateTo', FrontPageView);
});

import ChallengesView from './views/body/ChallengesView';
router.route('challenges', 'challenges', function (params) {
    params = parseQueryString(params);

    var timeframe = null;
    if (_.has(params, 'timeframe')) {
        timeframe = params.timeframe;
    }

    events.trigger('g:navigateTo', ChallengesView, {
        timeframe: timeframe
    });
});

import ChallengeView from './views/body/ChallengeView';
import ChallengeModel from './models/ChallengeModel';
router.route('challenge/:id', 'challenge', function (id) {
    // Fetch the challenge by id, then render the view.
    var challenge = new ChallengeModel();
    challenge.set({
        _id: id
    }).on('g:fetched', function () {
        events.trigger('g:navigateTo', ChallengeView, {
            challenge: challenge
        });
    }, this).on('g:error', function () {
        router.navigate('challenges', {trigger: true});
    }, this).fetch();
});

import PhaseView from './views/body/PhaseView';
import PhaseModel from './models/PhaseModel';
router.route('phase/:id', 'phase', function (id) {
    // Fetch the phase by id, then render the view.
    var phase = new PhaseModel({
        _id: id
    }).once('g:fetched', function () {
        events.trigger('g:navigateTo', PhaseView, {
            phase: phase
        });
    }).once('g:error', function () {
        router.navigate('challenges', {trigger: true});
    });
    phase.fetch();
});

router.route('challenge/n/:name', 'challengeByName', function (name) {
    var challenge = new ChallengeModel();
    challenge.findByName(name).once('c:found', function () {
        events.trigger('g:navigateTo', ChallengeView, {
            challenge: challenge
        });
    }).once('c:notFound', function () {
        router.navigate('challenges', {trigger: true});
    });
});

import ChallengeLearnView from './views/body/ChallengeLearnView';
router.route('challenges/learn', 'challengesLearn', function () {
    events.trigger('g:navigateTo', ChallengeLearnView);
});

import NewChallengeView from './views/body/NewChallengeView';
router.route('challenge/new', 'newChallenge', function () {
    events.trigger('g:navigateTo', NewChallengeView, {
        wizard: {
            total: 4
        }
    });
});

import NewPhaseView from './views/body/NewPhaseView';
router.route('challenge/:id/phase/new', 'newPhase', function (id) {
    var challenge = new ChallengeModel({
        _id: id
    });
    events.trigger('g:navigateTo', NewPhaseView, {
        challenge: challenge,
        wizard: {
            total: 5
        }
    });
});

import ScoringMetricsView from './views/body/ScoringMetricsView';
router.route('phase/:id/metrics', 'phaseMetrics', function (id) {
    // Fetch the phase by id, then render the view.
    var phase = new PhaseModel({
        _id: id
    }).on('g:fetched', function () {
        events.trigger('g:navigateTo', ScoringMetricsView, {
            phase: phase
        });
    }, this).on('g:error', function () {
        router.navigate('challenges', {trigger: true});
    }, this);
    phase.fetch();
});

import SubmitView from './views/body/SubmitView';
router.route('phase/:id/submit', 'phase_submit', function (id) {
    var phase = new PhaseModel({
        _id: id
    });
    phase.once('g:fetched', function () {
        events.trigger('g:navigateTo', SubmitView, {
            phase
        });
    }).once('g:error', function () {
        router.navigate('challenges', {trigger: true});
    }, this).fetch();
});

import SubmissionView from './views/body/SubmissionView';
import SubmissionModel from './models/SubmissionModel';
router.route('submission/:id', 'phase_submission', function (id) {
    var submission = new SubmissionModel({
        _id: id
    });
    submission.once('g:fetched', function () {
        events.trigger('g:navigateTo', SubmissionView, {
            submission
        });
    }).once('g:error', function () {
        router.navigate('challenges', {trigger: true});
    }).fetch();
});

import PhaseSubmissionsView from './views/body/PhaseSubmissionsView';
router.route('phase/:id/submissions', 'phaseSubmissions', function (id, params) {
    var phase = new PhaseModel({
        _id: id
    }).once('g:fetched', function () {
        if (phase.getAccessLevel() < AccessType.WRITE) {
            router.navigate('challenges', {trigger: true});
        } else {
            params = parseQueryString(params);

            var participantLimit = null;
            var submissionLimit = null;
            if (_.has(params, 'participantLimit')) {
                participantLimit = params.participantLimit;
            }
            if (_.has(params, 'submissionLimit')) {
                submissionLimit = params.submissionLimit;
            }

            events.trigger('g:navigateTo', PhaseSubmissionsView, {
                phase,
                participantLimit,
                submissionLimit
            });
        }
    }, this).on('g:error', function () {
        router.navigate('challenges', {trigger: true});
    }, this);
    phase.fetch();
});

var _wizardPage = function (route, routeName, modelType, viewType) {
    router.route(route, routeName, function (id, params) {
        var model = new modelType({_id: id}),  // eslint-disable-line new-cap
            wizard = false;

        params = parseQueryString(params);

        if (_.has(params, 'wizard')) {
            wizard = {
                total: window.parseInt(params.total),
                current: window.parseInt(params.curr)
            };
        }

        model.once('g:fetched', () => {
            events.trigger('g:navigateTo', viewType, {
                model,
                wizard
            });
        }).once('g:error', () => {
            router.navigate('challenges', {trigger: true});
        }).fetch();
    });
};

import ChallengeThumbnailView from './views/body/ChallengeThumbnailView';
_wizardPage('challenge/:id/thumbnail', 'challengeThumbnail', ChallengeModel, ChallengeThumbnailView);

import ChallengeInstructionsView from './views/body/ChallengeInstructionsView';
_wizardPage('challenge/:id/instructions', 'challengeAccess', ChallengeModel, ChallengeInstructionsView);

import ChallengeAccessView from './views/body/ChallengeAccessView';
_wizardPage('challenge/:id/access', 'challengeAccess', ChallengeModel, ChallengeAccessView);

import PhaseAccessView from './views/body/PhaseAccessView';
_wizardPage('phase/:id/access', 'phaseAccess', PhaseModel, PhaseAccessView);

import PhaseInstructionsView from './views/body/PhaseInstructionsView';
_wizardPage('phase/:id/instructions', 'phaseInstructions', PhaseModel, PhaseInstructionsView);

import PhaseInputView from './views/body/PhaseInputView';
_wizardPage('phase/:id/input', 'phaseInput', PhaseModel, PhaseInputView);

import PhaseGroundTruthView from './views/body/PhaseGroundTruthView';
_wizardPage('phase/:id/groundtruth', 'phaseGroundTruth', PhaseModel, PhaseGroundTruthView);
