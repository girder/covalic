import _ from 'underscore';
import Backbone from 'backbone';
import events from 'girder/events';
import router from 'girder/router';
import { parseQueryString } from 'girder/misc';

router.enabled(false);

var covalicRouter = new Backbone.Router();

export default covalicRouter;

// Setup app routes
import FrontPageView from './views/body/FrontPageView';
covalicRouter.route('', 'index', function () {
    events.trigger('g:navigateTo', FrontPageView);
});

import ChallengesView from './views/body/ChallengesView';
covalicRouter.route('challenges', 'challenges', function (params) {
    params = parseQueryString(params);

    var timeframe = null;
    if (_.has(params, 'timeframe')) {
        timeframe = params.timeframe;
    }

    events.trigger('g:navigateTo', ChallengesView, {
        timeframe: timeframe
    });
});
