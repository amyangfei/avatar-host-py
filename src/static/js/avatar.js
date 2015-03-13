$(function() {
    $(".j_set_avatar").click(function(evt) {
        evt.preventDefault();

        image_id = $(this).attr("rel");

        $.ajax({
            type: "POST",
            contentType: "application/x-www-form-urlencoded",
            url: "/image/setavatar",
            data: "image_id=" + image_id,
            dataType: "json",

            success: function(data) {
                alert(data.msg);
                if (data.status == "ok") {
                    $("#nav_avatar").attr("src", data.new_avatar);
                }
            },
            // Degbug
            error: function(xhr, desc, err) {
                console.log(xhr);
                console.log("Details: " + desc + "\nError:" + err);
            },
        });
        return false;
    });
});

