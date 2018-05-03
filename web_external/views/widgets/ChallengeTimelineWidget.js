import _ from 'underscore';
import moment from 'moment';
import TimelineWidget from 'girder/views/widgets/TimelineWidget';

import View from '../view';
import ChallengePhaseCollection from '../../collections/ChallengePhaseCollection';
import '../../stylesheets/widgets/challengeTimeline.styl';

var ChallengeTimelineWidget = View.extend({
    initialize: function (settings) {
        this.collection = new ChallengePhaseCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch({
            challengeId: settings.challenge.id
        });
        this.challenge = settings.challenge;

        this.pointCompletedClass = 'c-challenge-timeline-point-completed';
        this.pointUpcomingClass = 'c-challenge-timeline-point-upcoming';
        this.segmentCompletedClass = 'c-challenge-timeline-segment-completed';
        this.segmentUpcomingClass = 'c-challenge-timeline-segment-upcoming';
    },

    render: function () {
        // Moment.js formatting strings
        var labelFormat = 'ddd, D MMM YYYY';
        var tooltipFormat = 'dddd, D MMMM YYYY, h:mm:ss a';

        // Render timeline only when both start and end dates are specified
        var startDateStr = this.challenge.get('startDate');
        var endDateStr = this.challenge.get('endDate');
        var startDate = !_.isEmpty(startDateStr) ? moment(startDateStr) : null;
        var endDate = !_.isEmpty(endDateStr) ? moment(endDateStr) : null;
        if (startDate && startDate.isValid() &&
            endDate && endDate.isValid()) {
            // Add points at challenge start and end dates
            // May be hidden by phase points
            var now = moment();
            var points = [];
            var point;

            point = this._createPoint(startDate, now);
            point.tooltip = startDate.format(tooltipFormat);
            points.push(point);

            point = this._createPoint(endDate, now);
            point.tooltip = endDate.format(tooltipFormat);
            points.push(point);

            // Add points at phase start and end dates
            var tooltip;
            _.each(this.collection.toArray(), function (phase) {
                var phaseStartDateStr = phase.get('startDate');
                var phaseEndDateStr = phase.get('endDate');
                var phaseStartDate = !_.isEmpty(phaseStartDateStr)
                    ? moment(phaseStartDateStr)
                    : null;
                var phaseEndDate = !_.isEmpty(phaseEndDateStr)
                    ? moment(phaseEndDateStr)
                    : null;

                if (phaseStartDate && phaseStartDate.isValid()) {
                    point = this._createPoint(phaseStartDate, now);
                    tooltip = phase.get('name') + ' starts ';
                    tooltip += ' (' + phaseStartDate.format(tooltipFormat) + ')';
                    point.tooltip = tooltip;
                    points.push(point);
                }

                if (phaseEndDate && phaseEndDate.isValid()) {
                    point = this._createPoint(phaseEndDate, now);
                    tooltip = phase.get('name') + ' ends ';
                    tooltip += ' (' + phaseEndDate.format(tooltipFormat) + ')';
                    point.tooltip = tooltip;
                    points.push(point);
                }
            }, this);

            // Add segments to represent progress
            var segments = this._createSegments(startDate, endDate, now);

            // Set labels
            // Show time remaining for active challenges
            var startLabel = moment(startDate).format(labelFormat);
            var endLabel = moment(endDate).format(labelFormat);
            if (now.isBefore(endDate) && now.isAfter(startDate)) {
                endLabel += ' (' + moment(now).from(endDate, true) + ' remaining)';
            }

            new TimelineWidget({
                el: this.$el,
                parentView: this,
                points: points,
                segments: segments,
                startTime: startDate,
                endTime: endDate,
                startLabel: startLabel,
                endLabel: endLabel,
                numeric: false
            }).render();
        }

        return this;
    },

    _createSegments: function (startDate, endDate, now) {
        if (!moment.isMoment(startDate) ||
            !moment.isMoment(endDate) ||
            !moment.isMoment(now)) {
            throw new Error('Invalid date(s) specified when creating timeline segments');
        }

        var segments = [];

        if (now.isBefore(startDate)) {
            // upcoming
            segments.push({
                start: startDate.toDate(),
                end: endDate.toDate(),
                class: this.segmentUpcomingClass
            });
        } else if (now.isAfter(endDate)) {
            // completed
            segments.push({
                start: startDate.toDate(),
                end: endDate.toDate(),
                class: this.segmentCompletedClass
            });
        } else {
            // active
            segments.push({
                start: startDate.toDate(),
                end: now.toDate(),
                class: this.segmentCompletedClass
            });
            segments.push({
                start: now.toDate(),
                end: endDate.toDate(),
                class: this.segmentUpcomingClass
            });
        }

        return segments;
    },

    _createPoint: function (date, now) {
        if (!moment.isMoment(date) ||
            !moment.isMoment(now)) {
            throw new Error('Invalid date(s) specified when creating timeline points');
        }

        var className = now.isAfter(date)
            ? this.pointCompletedClass
            : this.pointUpcomingClass;
        return {
            time: date.toDate(),
            class: className
        };
    }
});

export default ChallengeTimelineWidget;
