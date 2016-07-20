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


});
