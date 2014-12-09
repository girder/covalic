covalic.views.LayoutGlobalNavView = girder.views.LayoutGlobalNavView.extend({

        navItems: function () {
            var navItems = [{
                name: 'Challenges',
                icon: 'icon-sitemap',
            target: 'challenges'
        }, {
            name: 'Users',
            icon: 'icon-user',
            target: 'users'
        }];
       return navItems;
    },

});
