covalic.views.FrontPageView = girder.views.FrontPageView.extend({
    events: {
        'click .c-participate-button': function () {
            covalic.router.navigate('challenges', {trigger: true});
        }
    },

    initialize: function () {
        girder.cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.frontPage({
            apiRoot: girder.apiRoot,
            staticRoot: girder.staticRoot,
            currentUser: girder.currentUser,
            versionInfo: girder.versionInfo
        }));

        return this;
    }
});

covalic.router.route('', 'index', function () {
    girder.events.trigger('g:navigateTo', covalic.views.FrontPageView);
});
