$(function() {
    $(".j_set_avatar").click(function(evt) {
        evt.preventDefault();

        var image_id = $(this).attr("rel");
        var _xsrf = $('input[name="_xsrf"]').get(0).value;

        $.ajax({
            type: "POST",
            contentType: "application/x-www-form-urlencoded",
            url: "/image/setavatar",
            data: "image_id=" + image_id + "&_xsrf=" + _xsrf,
            dataType: "json",

            success: function(data) {
                if (data.status == "ok") {
                    $("#nav_avatar").attr("src", data.new_avatar);
                    $("#sidebar-avatar").attr("src", data.new_avatar);
                    $("#manage-success-li").html(data.msg);
                    $("#manage-success-div").show();
                    setTimeout(function() {
                        $("#manage-success-div").fadeOut(1000);
                    }, 1500);
                } else {
                    $("#manage-error-li").html(data.msg);
                    $("#manage-error-li").html(data.msg);
                    $("#manage-error-div").show();
                    setTimeout(function() {
                        $("#manage-error-div").fadeOut(1000);
                    }, 1000);
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
