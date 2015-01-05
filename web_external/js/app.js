covalic.App = girder.App.extend({

    render: function() {
        this.$el.html(girder.templates.layout());

        new covalic.views.LayoutHeaderView({
            el: this.$('#g-app-header-container'),
            parentView: this
        }).render();

        new covalic.views.ChallengesView({
            el: this.$('#g-app-body-container'),
            parentView: this
        }).render();

        this.globalNavView = new girder.views.LayoutGlobalNavView({
            navItems: [{
                name: 'Challenges',
                icon: 'icon-sitemap',
                target: 'challenges'
            }, {
                name: 'Users',
                icon: 'icon-user',
                target: 'users'
            }],
            el: this.$('#g-global-nav-container'),
            parentView: this
        }).render();

        return this;
    },

});
