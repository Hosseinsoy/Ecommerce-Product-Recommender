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





/* =====================================================
EDIT PRODUCT COMMENT
===================================================== */

$(document).on(
    "click",
    ".comment-edit-button",
    function (e) {

        e.preventDefault();

        const button = $(this);

        const commentId = button.data("comment-id");


        $.ajax({

            url: `/edit-product-comment/${commentId}/`,

            type: "GET",


            beforeSend:function(){

                button.prop(
                    "disabled",
                    true
                );

                button.css(
                    "opacity",
                    "0.5"
                );

            },


            success:function(response){


                if(!response.success){

                    alert(
                        response.message ||
                        "خطا در دریافت اطلاعات"
                    );

                    return;

                }


                const comment = response.comment;


                const modal = $("#insertCommentModal");

                const form = modal.find("form");



                /*
                    EDIT MODE
                */


                form.attr(
                    "action",
                    `/edit-product-comment/${commentId}/`
                );


                form.attr(
                    "data-edit-mode",
                    "true"
                );



                /*
                    اطلاعات فرم
                */


                form.find(
                    'input[name="title"]'
                ).val(
                    comment.title
                );


                form.find(
                    'textarea[name="body"]'
                ).val(
                    comment.body
                );


                form.find(
                    'input[name="positive_points"]'
                ).val(
                    comment.positive_points
                );


                form.find(
                    'input[name="negative_points"]'
                ).val(
                    comment.negative_points
                );




                /*
                    ستاره ها
                */


                const rating = form.find(".rating");


                rating.find(
                    'input[name="score"]'
                )
                .prop(
                    "checked",
                    false
                );


                rating.find(
                    `input[name="score"][value="${comment.score}"]`
                )
                .prop(
                    "checked",
                    true
                );





                /*
                    موضوعات دیدگاه
                */


                form.find(
                    'input[type="radio"][name^="point_type_"]'
                )
                .prop(
                    "checked",
                    false
                );


                $.each(
                    comment.points,
                    function(pointId, pointType){

                        form.find(
                            `input[name="point_type_${pointId}"][value="${pointType}"]`
                        )
                        .prop(
                            "checked",
                            true
                        );

                    }
                );




                /*
                    عنوان مودال
                */


                modal.find(
                    ".modal-title"
                )
                .contents()
                .first()
                .replaceWith(
                    "ویرایش دیدگاه"
                );


                modal.find(
                    ".modal-title span"
                )
                .text(
                    "در مورد " + comment.product_name
                );




                /*
                    دکمه ثبت
                */


                form.find(
                    'button[type="submit"]'
                )
                .text(
                    "ذخیره تغییرات"
                );




                /*
                    باز کردن مودال
                */


                bootstrap.Modal
                .getOrCreateInstance(
                    document.getElementById(
                        "insertCommentModal"
                    )
                )
                .show();


            },


            error:function(xhr){

                console.log(
                    xhr.responseText
                );


                alert(
                    "خطا در دریافت اطلاعات دیدگاه"
                );

            },


            complete:function(){

                button.prop(
                    "disabled",
                    false
                );


                button.css(
                    "opacity",
                    "1"
                );

            }


        });


    }
);

$(document).on(
    "submit",
    "#insertCommentModal form",
    function(e){

        const form = $(this);


        if(form.attr("data-edit-mode") === "true"){

            e.preventDefault();
            e.stopPropagation();


            $.ajax({

                url: form.attr("action"),

                type: "POST",

                data: form.serialize(),


                success:function(response){

                    if(response.success){

                        // بستن مودال
                        const modalElement =
                            document.getElementById(
                                "insertCommentModal"
                            );

                        const modal =
                            bootstrap.Modal.getInstance(
                                modalElement
                            );

                        if(modal){
                            modal.hide();
                        }


                        // رفرش صفحه برای نمایش پیام جنگو
                        window.location.reload();

                    }
                    else{

                        alert(
                            response.message ||
                            "خطا در ویرایش دیدگاه"
                        );

                    }

                },


                error:function(xhr){

                    console.log(
                        xhr.responseText
                    );


                    alert(
                        xhr.responseJSON?.message ||
                        "خطا در ویرایش دیدگاه"
                    );

                }

            });

        }

    }
);