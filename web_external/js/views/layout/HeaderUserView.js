covalic.views.LayoutHeaderUserView = covalic.View.extend({


    events: {
        'clicka.g-login':function(){
            girder.events.trigger('g:loginUi');
        },

        'clicka.g-register':function(){
            girder.events.trigger('g:registerUi');
        },

        'clicka.g-logout':function(){
            girder.restRequest({
                path:'user/authentication',
                type:'DELETE'
            }).done(_.bind(function(){
                girder.currentUser=null;
                girder.events.trigger('g:login');
            },this));
        },

        'clicka.g-my-folders':function(){
            girder.router.navigate('user/'+girder.currentUser.get('_id'),{trigger:true});
        },

        'clicka.g-my-settings':function(){
            girder.router.navigate('useraccount/'+girder.currentUser.get('_id')+
                                    '/info',{trigger:true});
        }
    },


    initialize: function () {
        girder.events.on('g:login', this.render, this);
    },

    render: function () {
        this.$el.html(jade.templates.layoutHeaderUser({
            user: girder.currentUser
        }));
        return this;
    }


});
