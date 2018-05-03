import { cancelRestRequests, staticRoot } from 'girder/rest';

import View from '../view';
import template from '../../templates/body/challengeLearn.pug';
import '../../stylesheets/body/challengeLearn.styl';

var ChallengeLearnView = View.extend({
    initialize: function () {
        cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.html(template({
            imgRoot: `${staticRoot}/built/plugins/covalic/extra/img`
        }));
        var jumboHeight = $('.jumbotron').outerHeight();
        var parallax = function () {
            var scrolled = $(window).scrollTop();
            $('.bg').css('height', (jumboHeight - scrolled) + 'px');
        };

        // TODO this breaks modularity.
        $(window).scroll(function () {
            parallax();
        });
        return this;
    }
});

export default ChallengeLearnView;
