$(document).on("click", ".cart-btn", function (e) {

    e.preventDefault();

    const btn = $(this);
    const productId = btn.data("product");

    $.ajax({

        url: `/cart/toggle/${productId}/`,
        type: "POST",

        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },

        success: function (res) {
            console.log(res.status);
            console.log(btn.hasClass("active"));
            if (!res.success) return;

            // تغییر وضعیت آیکون
            if (res.status === "added") {
                btn.addClass("active");
            } else {
                btn.removeClass("active");
            }

            console.log(btn.attr("class"));

            // تعداد
            $("#cart_badge").text(res.cart_count);
            $("#cart_info").text(res.cart_count);

            // مبلغ
            if (typeof formatPrice === "function") {
                $("#products_price").text(formatPrice(res.products_price));
            } else {
                $("#products_price").text(res.products_price);
            }

            // بدنه سبد
            if (res.cart_body) {
                $("#cart-dropdown-body").html(res.cart_body);
            }

            // فوتر
            if (res.cart_footer) {
                $(".shopping-cart-box .card-footer").replaceWith(res.cart_footer);
            }

        },

        error: function (xhr) {
            console.log(xhr.responseText);
        }

    });

});