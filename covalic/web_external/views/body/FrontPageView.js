import { cancelRestRequests } from 'girder/rest';
import GirderFrontPageView from 'girder/views/body/FrontPageView';

import template from '../../templates/body/frontPage.pug';
import '../../stylesheets/body/frontPage.styl';

var FrontPageView = GirderFrontPageView.extend({
    initialize: function () {
        cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.addClass('c-body-nopad').html(template());
        return this;
    }
});

export default FrontPageView;
