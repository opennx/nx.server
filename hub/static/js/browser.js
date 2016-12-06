$(document).ready(function() {

    console.log("Browser ready!");

    $('.table tr[data-href]').each(function(){
        $(this).css('cursor','pointer').click(function(){
                alert( $(this).attr('data-href'));
            }
        );
    });

});

