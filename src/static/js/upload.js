$(function() {
    function PreviewImage(input) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
                $("#preview-img").attr("src", e.target.result);
                $("#preview-div").show();
            }

            reader.readAsDataURL(input.files[0]);
        } else {
            $("#preview-img").attr("src", "");
            $("#preview-div").hide();
        }
    };

    $("#upload-input").change(function(){
        PreviewImage(this);
    });
});
