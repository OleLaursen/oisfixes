$(function () {
    var searchPanes = $(".searchPanes");
    var create = $(".create");
    
    function showPane(paneContainer, cssClass) {
        paneContainer.children().not(cssClass).hide();
        paneContainer.children(cssClass).show();
    }
    

    // searching
    function searchError(msg) {
        searchPanes.find(".error p").text(msg);
        showPane(searchPanes, ".error");
    }

    function searchResults(data) {
        if (data.error) {
            searchError(data.error);
            return;
        }
        
        var results = data.results;
        if (results.length == 0) {
            showPane(searchPanes, ".noResults");
            return;
        }
        
        var summary = format("Fundet {0} med adressepunkter.", results.length == 1 ? "1 vej" : results.length + " veje");
        searchPanes.find(".results .summary").text(summary);
        
        var html = [];
        var osmSrc = $("img#osm").attr("src");
        
        for (var i = 0; i < results.length; ++i) {
            var o = results[i];
            html.push("<tr>");
            html.push(format('<td>{0} ({1} {2})</td>', data.name, o.node_postcode, o.node_city));
            html.push("<td>" + o.municipality_no + "</td>");
            html.push("<td>" + o.street_no + "</td>");
            html.push(format('<td><a class="create" title="Ret navnet på denne vej" href="" data-street="{0}" data-municipality-no="{1}" data-street-no="{2}" data-node-id="{3}" data-lat="{4}" data-lon="{5}">ret</a></td>', data.name, o.municipality_no, o.street_no, o.node_id, o.node_lat, o.node_lon));
            html.push(format('<td><a title="Vis et af vejens adressepunkter på OpenStreetMap" href="http://www.openstreetmap.org/?node={0}"><img src="{1}"></a></td>', o.node_id, osmSrc));
            html.push("</tr>");
        }

        var tbody = searchPanes.find(".results table tbody");
        
        tbody.html(html.join(""));
        
        tbody.find("a.create").click(function (e) {
            e.preventDefault();

            startCreateReport($(this).data());
        });

        showPane(searchPanes, ".results");

        // check if we should try to click on one immediately
        if (autoselectMunicipalityNo != null && autoselectStreetNo != null) {
            tbody.find("a.create").each(function () {
                if ($(this).data("municipalityNo") == autoselectMunicipalityNo
                    && $(this).data("streetNo") == autoselectStreetNo)
                    $(this).click();
            });
        }
    }

    $("form.search").submit(function (e) {
        e.preventDefault();

        create.hide();
        
        var name = $(this).find(".name").val();
        if (!name) {
            searchError("Du skal indtaste noget at søge efter!");
            return;
        }

        showPane(searchPanes, ".loading");
        searchPanes.find(".loading .name").text(name);
        
        $.ajax({
            url: $(this).attr("action"),
            type: $(this).attr("method"),
            dataType: "json",
            data: { name: name },
            success: searchResults,
            error: function () { searchError("Serverfejl."); }
        });
    });

    // create report
    function startCreateReport(info) {
        searchPanes.children().hide();
        
        create.find("input[name=node_id]").val(info.nodeId);
        create.find("input[name=lat]").val(info.lat);
        create.find("input[name=lon]").val(info.lon);
        create.find("input[name=municipality_no]").val(info.municipalityNo);
        create.find("input[name=street_no]").val(info.streetNo);
        create.find("input[name=old_name]").val(info.street);
        create.find("input[name=new_name]").val(info.street).focus();
        create.find("input[name=comment]").val("");

        create.find(".result").html("");

        create.find("input[type=submit]").prop("disabled", "");
        create.find("form").show();
        
        create.show();
    }

    create.find("form .explanation a").click(function () {
        create.find("input[name=comment]").val($(this).text());
    });

    function createdReport(data) {
        if (data.error) {
            create.find("input[type=submit]").prop("disabled", "");
            create.find(".result").html(data.error);
            return;
        }

        create.find("form").hide(500);
        create.find(".result").html(data.result);
    }
    
    create.find("form").submit(function (e) {
        e.preventDefault();
        if ($.trim(create.find("input[name=new_name]").val()) == "" ||
            $.trim(create.find("input[name=comment]").val()) == "") {
            create.find(".result").html("Du <em>skal</em> udfylde feltet med rettet navn og feltet med forklaring.");
            return;
        }

        create.find("input[type=submit]").prop("disabled", "disabled");

        $.ajax({
            url: $(this).attr("action"),
            type: $(this).attr("method"),
            dataType: "json",
            data: $(this).serialize(),
            success: createdReport,
            error: function () {
                create.find(".result").text("Serverfejl.");
                create.find("input[type=submit]").prop("disabled", "");
            }
        });
    });

    // check if we should fire search right away
    var val = $("form.search input[name=name]").val();
    if (val)
        $("form.search").submit();
});
