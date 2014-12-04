covalic.views.LayoutGlobalNavView = girder.views.LayoutGlobalNavView.extend({

    render: function () {
        var navItems = [{
            name: 'Challenges',
            icon: 'icon-sitemap',
            target: 'challenges'
        }, {
            name: 'Users',
            icon: 'icon-user',
            target: 'users'
        }];

        this.$el.html(jade.templates.layoutGlobalNav({
            navItems: navItems
        }));

        if (Backbone.history.fragment) {
            this.$('[g-target="' + Backbone.history.fragment + '"]')
                .parent().addClass('g-active');
        }

        return this;
    }

});
