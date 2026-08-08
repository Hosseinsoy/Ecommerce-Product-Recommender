$(document).on("click", ".comment-sort-link", function (e) {

    e.preventDefault();

    const button = $(this);
    const sort = button.data("sort");

    $.ajax({

        url: window.location.pathname,

        type: "GET",

        data: {
            comment_sort: sort,
            ajax: "1"
        },

        beforeSend: function () {

            $("#comments-container").css(
                "opacity",
                "0.5"
            );

        },

        success: function (response) {

            $("#comments-container").html(
                response.html
            );

            $(".comment-sort-link")
                .removeClass("text-danger");

            button.addClass("text-danger");

        },

        error: function () {

            console.log(
                "خطا در دریافت دیدگاه‌ها"
            );

        },

        complete: function () {

            $("#comments-container").css(
                "opacity",
                "1"
            );

        }

    });

});
