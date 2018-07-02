import _ from 'underscore';
import Backbone from 'backbone';
import events from 'girder/events';
import girderRouter from 'girder/router';
import { AccessType } from 'girder/constants';
import { parseQueryString } from 'girder/misc';

import ChallengeAccessView from './views/body/ChallengeAccessView';
import ChallengeInstructionsView from './views/body/ChallengeInstructionsView';
import ChallengeLearnView from './views/body/ChallengeLearnView';
import ChallengeModel from './models/ChallengeModel';
import ChallengeThumbnailView from './views/body/ChallengeThumbnailView';
import ChallengeView from './views/body/ChallengeView';
import ChallengesView from './views/body/ChallengesView';
import FrontPageView from './views/body/FrontPageView';
import NewChallengeView from './views/body/NewChallengeView';
import NewPhaseView from './views/body/NewPhaseView';
import PhaseAccessView from './views/body/PhaseAccessView';
import PhaseConfigureSubmissionsView from './views/body/PhaseConfigureSubmissionsView';
import PhaseGroundTruthView from './views/body/PhaseGroundTruthView';
import PhaseInputView from './views/body/PhaseInputView';
import PhaseInstructionsView from './views/body/PhaseInstructionsView';
import PhaseModel from './models/PhaseModel';
import PhaseSubmissionsView from './views/body/PhaseSubmissionsView';
import PhaseView from './views/body/PhaseView';
import ScoringMetricsView from './views/body/ScoringMetricsView';
import SubmissionModel from './models/SubmissionModel';
import SubmissionView from './views/body/SubmissionView';
import SubmitView from './views/body/SubmitView';

girderRouter.enabled(false);

var router = new Backbone.Router();

// Setup app routes
router.route('', 'index', function () {
    events.trigger('g:navigateTo', FrontPageView);
});

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

router.route('challenges/learn', 'challengesLearn', function () {
    events.trigger('g:navigateTo', ChallengeLearnView);
});

router.route('challenge/new', 'newChallenge', function () {
    events.trigger('g:navigateTo', NewChallengeView, {
        wizard: {
            total: 4
        }
    });
});

router.route('challenge/:id/phase/new', 'newPhase', function (id) {
    var challenge = new ChallengeModel({
        _id: id
    });
    events.trigger('g:navigateTo', NewPhaseView, {
        challenge: challenge,
        wizard: {
            total: 6
        }
    });
});

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
        var model = new modelType({_id: id}), // eslint-disable-line new-cap
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

_wizardPage('challenge/:id/thumbnail', 'challengeThumbnail', ChallengeModel, ChallengeThumbnailView);
_wizardPage('challenge/:id/instructions', 'challengeAccess', ChallengeModel, ChallengeInstructionsView);
_wizardPage('challenge/:id/access', 'challengeAccess', ChallengeModel, ChallengeAccessView);
_wizardPage('phase/:id/access', 'phaseAccess', PhaseModel, PhaseAccessView);
_wizardPage('phase/:id/instructions', 'phaseInstructions', PhaseModel, PhaseInstructionsView);
_wizardPage('phase/:id/input', 'phaseInput', PhaseModel, PhaseInputView);
_wizardPage('phase/:id/groundtruth', 'phaseGroundTruth', PhaseModel, PhaseGroundTruthView);
_wizardPage('phase/:id/configure_submissions', 'phaseConfigureSubmission', PhaseModel, PhaseConfigureSubmissionsView);

export default router;
