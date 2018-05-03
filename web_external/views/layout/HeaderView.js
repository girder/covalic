import View from '../view';
import HeaderUserView from './HeaderUserView';
import template from '../../templates/layout/layoutHeader.pug';
import '../../stylesheets/layout.styl';

var HeaderView = View.extend({
    render: function () {
        this.$el.html(template());

        this.$('a[title]').tooltip({
            placement: 'bottom',
            delay: {show: 300}
        });

        new HeaderUserView({
            el: this.$('.c-current-user-wrapper'),
            parentView: this
        }).render();
        return this;
    }
});

export default HeaderView;
