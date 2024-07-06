odoo.define('fs_visit_report.mapWidget', function (require) {
    'use strict';

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var MapWidget = AbstractField.extend({
        template: 'fs_visit_report.visit_google_map',
        xmlDependencies: ['/fs_visit_report/static/src/xml/visitmapWidget.xml'],
        custom_events: {
            field_changed: 'on_ready',
        },

        init: function (parent, data, options) {
            this._super.apply(this, arguments);
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(async function () {
                if(typeof mapboxgl !== 'object'){
                    window.apiCallback = self.on_ready;
                    await $.getScript('https://api.mapbox.com/mapbox-gl-js/v2.6.1/mapbox-gl.js');
                    mapboxgl.accessToken = 'pk.eyJ1IjoibWlua2hhbnRreWF3LWFzaWFtYXRyaXgiLCJhIjoiY2t4OHF6cHd2MzB1YjJ0cHoxeGt6NDR5ZCJ9.gWPNbzbWH2Ls_n1IADmkLQ';
                    /*var cssLink = $("https://api.mapbox.com/mapbox-gl-js/v2.6.1/mapbox-gl.css");
                    $("head").append(cssLink); //IE hack: append before setting href

                    cssLink.attr({
                      rel:  "stylesheet",
                      type: "text/css",
                      href: href
                    });*/
//                    var google_url = 'https://maps.googleapis.com/maps/api/js?key=AIzaSyBFameKH86YtFRO1prBdQKPycD1YTJRxp0';
//                    window.apiCallback = self.on_ready;
//                    $.getScript(google_url + '&callback=apiCallback');
                }
            });
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                if(typeof mapboxgl == 'object') {
                    self.on_ready();
                }
            });
        },

        on_ready: async function () {
            var mapContainer = this.$el[0];
            var formData = this.record.data;
            
            var latitude = formData.latitude;
            var longitude = formData.longitude;
            var center = [longitude,latitude];
             const map = new mapboxgl.Map({
                  container: this.$el[0],
                  style: 'mapbox://styles/mapbox/streets-v11',
                  center: center,
                  zoom: 13,
                });
            map.on('load', function () {
                map.resize();
            });

          const beginMarker = new mapboxgl.Marker()
                    .setLngLat([longitude, latitude])
                    .addTo(map);
                    setTimeout(() => {map.resize()}, 1500);
  
//            const beginMarker = new mapboxgl.Marker()
//                    .setLngLat([longitude, latitude])
//                    .addTo(map);
            // console.log('FORM DATA latitude', latitude)
            // console.log('FORM DATA longitude', longitude)
            /*var center = new google.maps.LatLng(latitude,longitude);
            var mapOptions = {
                zoom: 15,
                center: center,
            };
            var visitmap = new google.maps.Map(mapContainer, mapOptions);
            // console.log('FORM DATA visit map', visitmap)
            var MainPoint = new google.maps.Marker({
                position: { lat: latitude, lng: longitude },
                title: formData.name,
                map: visitmap,
            });*/
            // console.log('FORM DATA MainPoint', MainPoint)
        },
    });

    fieldRegistry.add('visit_route_map', MapWidget);

    return MapWidget;
});
