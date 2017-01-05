import _ from 'underscore';
import events from 'girder/events';
import { getCurrentUser, setCurrentUser } from 'girder/auth';
import { restRequest } from 'girder/rest';

import View from '../view';
import router from '../../router';
import template from '../../templates/layout/layoutHeaderUser.pug';
import '../../stylesheets/layout.styl';

var HeaderUserView = View.extend({
    events: {
        'click a.g-login': function () {
            events.trigger('g:loginUi');
        },

        'click a.g-register': function () {
            events.trigger('g:registerUi');
        },

        'click a.g-logout': function () {
            restRequest({
                path: 'user/authentication',
                type: 'DELETE'
            }).done(_.bind(function () {
                setCurrentUser(null);
                events.trigger('g:login');
            }, this));
        },

        'click a.g-my-settings': function () {
            router.navigate(`useraccount/${getCurrentUser().id}/info`, {trigger: true});
        }
    },

    initialize: function () {
        events.on('g:login', this.render, this);
    },

    render: function () {
        var currentUser = getCurrentUser();
        this.$el.html(template({
            user: currentUser
        }));

        if (currentUser) {
            this.$('.c-portrait-wrapper').css(
                'background-image', `url(${currentUser.getGravatarUrl(36)})`);
        }
        return this;
    }

});

export default HeaderUserView;
