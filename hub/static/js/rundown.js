$( document ).ready(function() {

    $.ajax({
        type: "POST",
        url: "/api/rundown",
        contentType : "application/json",
        data: '{"start_time" : 1468825200, "id_channel" : 1}',
        dataType: "json",
        processData: false,
        success: function(data){

            $("#rundown").html(data.message);
        } //success
    });



    // tohle je browser.... melo by to bejt nekde v commons a davat se tam vzdycky, kdyz tam browser ma bejt
    $.ajax({
        type: "POST",
        url: "/api/get",
        contentType : "application/json",
        data: '{"fulltext" : "vlozte", "result" : ["title", "genre", "_duration@" ,"id"]}',
        dataType: "json",
        processData: false,
        success: function(data){
            assets = data["data"];
            for (i = 0; i < assets.length; i++) {
                asset = assets[i];
                $('#browser-table').append('<tr><td>'+ asset[0] +'</td><td>'+asset[1]+'</td><td>'+asset[2]+'</td></tr>\n');
            }

        } //success
    });


});
