import Backbone from 'backbone';
import events from 'girder/events';
import router from 'girder/router';

router.enabled(false);

var covalicRouter = new Backbone.Router();

export default covalicRouter;

// Setup app routes
import FrontPageView from './views/body/FrontPageView';
covalicRouter.route('', 'index', function () {
    events.trigger('g:navigateTo', FrontPageView);
});
