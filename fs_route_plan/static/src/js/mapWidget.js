odoo.define('fs_route_plan.mapWidget', function (require) {
    'use strict';

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var MapWidget = AbstractField.extend({
        template: 'fs_route_plan.google_map',
        xmlDependencies: ['/fs_route_plan/static/src/xml/mapWidget.xml'],
        custom_events: {
            field_changed: 'on_ready',
        },

        init: function (parent, data, options) {
            this._super.apply(this, arguments);
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if(typeof google !== 'object'){
                    var google_url = 'https://maps.googleapis.com/maps/api/js?key=AIzaSyBFameKH86YtFRO1prBdQKPycD1YTJRxp0';
                    window.apiCallback = self.on_ready;
                    $.getScript(google_url + '&callback=apiCallback');
                }
            });
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                if(typeof google == 'object') {
                    self.on_ready();
                }
            });
        },

        on_ready: function () {
            var mapContainer = this.$el[0];
            var formData = this.record.data;
            var state = formData.state;
            if (state !== 'confirm'){
                return
            }
            var planType = formData.plan_type;
            var beginLat = formData.begin_partner_lat;
            var beginLng = formData.begin_partner_lng;
            var endLat = formData.end_partner_lat;
            var endLng = formData.end_partner_lng;
            console.log('FORM DATA', formData)
            if (planType === 'trip'){
                var center = new google.maps.LatLng(beginLat, beginLng);
                var mapOptions = {
                    zoom: 15,
                    center: center,
                };
                var map = new google.maps.Map(mapContainer, mapOptions);
                var beginPointMarker = new google.maps.Marker({
                    position: { lat: beginLat, lng: beginLng },
                    title: 'Begin Point',
                    map: map,
                });
                var endPointMarker = new google.maps.Marker({
                    position: { lat: endLat, lng: endLng },
                    title: 'End Point',
                    map: map,
                });
                var saleRoute = new google.maps.Polyline({
                    path: [{ lat: beginLat, lng: beginLng }, { lat: endLat, lng: endLng }],
                    geodesic: true,
                    strokeColor: '#FF0000',
                    strokeOpacity: 1.0,
                    strokeWeight: 2,
                });
                saleRoute.setMap(map);
            }

            else if (planType === 'day' || planType === 'week'){
                if (formData.partner_ids.data.length > 0){
                    var firstLine = formData.partner_ids.data[0];
                    var center = new google.maps.LatLng(firstLine.data.latitude, firstLine.data.longitude);
                    var mapOptions = {
                        zoom: 15,
                        center: center,
                    };
                    var map = new google.maps.Map(mapContainer, mapOptions);
                    // First Point
                    var firstPoint = new google.maps.Marker({
                        position: { lat: firstLine.data.latitude, lng: firstLine.data.longitude },
                        title: firstLine.data.name,
                        map: map,
                    });
                    var points = [];
                    for(let [key, line] of Object.entries(formData.partner_ids.data)){
                        var point = new google.maps.Marker({
                            position: { lat: line.data.latitude, lng: line.data.longitude },
                            title: line.data.name,
                            map: map,
                        });
                        points.push({ lat:  line.data.latitude, lng: line.data.longitude });
                    }
                    if (points.length > 1){
                        var polyLine = new google.maps.Polyline({
                            path: points,
                            geodesic: true,
                            strokeColor: "#FF0000",
                            strokeOpacity: 1.0,
                            strokeWeight: 2,
                            map: map,
                        });
                    }
                }
            }
        },
    });

    fieldRegistry.add('route_map', MapWidget);

    return MapWidget;
});
