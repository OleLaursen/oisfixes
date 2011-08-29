$(function () {
    $(".map").each(function () {
        var id = "r" + Math.random();
        this.id = id;
        var map = new OpenLayers.Map(id);
        var fromProjection = new OpenLayers.Projection("EPSG:4326"); // transform from WGS 1984
        var toProjection = new OpenLayers.Projection("EPSG:900913"); // to Spherical Mercator Projection
        map.addLayer(new OpenLayers.Layer.OSM());
        map.setCenter(new OpenLayers.LonLat(+$(this).data("lon"), +$(this).data("lat")).transform(fromProjection, toProjection), 15);
    });
});
