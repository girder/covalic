import _ from 'underscore';
import Backbone from 'backbone';
import events from 'girder/events';
import girderRouter from 'girder/router';
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
