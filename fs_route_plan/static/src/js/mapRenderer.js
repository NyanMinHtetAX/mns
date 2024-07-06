odoo.define('fs_route_plan.mapRenderer', function(require){

var mapRenderer = require('web_map.MapRenderer');

mapRenderer.prototype._addRoutes = function(){
    this._removeRoutes();
    if (!this.props.mapBoxToken || !this.props.routeInfo.routes.length) {
        return;
    }

    for (const leg of this.props.routeInfo.routes[0].legs) {
        const latLngs = [];
        for (const step of leg.steps) {
            for (const coordinate of step.geometry.coordinates) {
                latLngs.push(L.latLng(coordinate[1], coordinate[0]));
            }
        }

        const polyline = L.polyline(latLngs, {
            color: 'red',
            weight: 5,
            opacity: 0.7,
        }).addTo(this.leafletMap);

        const polylines = this.polylines;
        polyline.on('click', function () {
            for (const polyline of polylines) {
                polyline.setStyle({ color: 'blue', opacity: 0.3 });
            }
            this.setStyle({ color: 'red', opacity: 1.0 });
        });
        this.polylines.push(polyline);
    }
};

return mapRenderer;
});