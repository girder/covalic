covalic.views.FrontPageView = girder.views.FrontPageView.extend({
    events: {
    },

    initialize: function () {
        girder.cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.html(jade.templates.frontPage({
            apiRoot: girder.apiRoot,
            staticRoot: girder.staticRoot,
            currentUser: girder.currentUser,
            versionInfo: girder.versionInfo
        }));

        return this;
    }
});

girder.router.route('', 'index', function () {
    girder.events.trigger('g:navigateTo', covalic.views.FrontPageView);
});
