import $ from 'jquery';
import { AccessType } from 'girder/constants';

import View from '../view';
import ChallengePhaseCollection from '../../collections/ChallengePhaseCollection';
import template from '../../templates/widgets/challengePhases.pug';
import '../../stylesheets/body/challengePage.styl';
import '../../ext/html.sortable';

var ChallengePhasesWidget = View.extend({
    events: {
        'c:update-phase-ordinals .c-phase-list': function (event) {
            var collection = this.collection;
            $('li a.c-phase-link', $(event.currentTarget)).each(function (ordinal) {
                var cid = $(this).attr('c-phase-cid');
                var phase = collection.get(cid);
                if (phase.get('ordinal') !== ordinal) {
                    phase.set('ordinal', ordinal).save();
                }
            });
        }
    },

    initialize: function (settings) {
        this.collection = new ChallengePhaseCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch({
            challengeId: settings.challenge.id
        });
        this.challenge = settings.challenge;
    },

    render: function () {
        this.$el.html(template({
            phases: this.collection.toArray(),
            challenge: this.challenge,
            canCreate: this.challenge.getAccessLevel() >= AccessType.WRITE
        }));

        if (this.challenge.getAccessLevel() >= AccessType.ADMIN) {
            this.$('.c-phase-list').sortable({
                placeholder: '<li class="c-phase-list-entry"><a class="c-phase-link">&nbsp;</a></li>'
            }).bind('sortstart', function (e, ui) {
                $('.c-phase-reorder', ui.item).tooltip('hide');
            }).bind('sortupdate', function (e, ui) {
                ui.item.trigger('c:update-phase-ordinals');
            });
        }

        this.$('.c-phase-reorder').tooltip({
            placement: 'left',
            delay: 200,
            container: this.$el,
            trigger: 'hover'
        });
        this.$('.c-tooltip').tooltip({
            delay: 100,
            container: this.$el
        });

        return this;
    }
});

export default ChallengePhasesWidget;
