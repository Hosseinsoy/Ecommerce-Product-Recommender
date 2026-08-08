function getCookie(name) {

    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {

        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {

                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );

                break;
            }
        }
    }

    return cookieValue;
}

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

// ==========================================
// افزودن محصول به سبد خرید - Product Detail
// ==========================================

$(document).on("click", "#product-detail-cart-btn", function (e) {

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

            if (!res.success) {
                return;
            }


            // ==========================================
            // آپدیت هدر سبد خرید
            // ==========================================

            $("#cart_badge").text(res.cart_count);
            $("#cart_info").text(res.cart_count);


            // ==========================================
            // آپدیت مبلغ سبد
            // ==========================================

            if (typeof formatPrice === "function") {

                $("#products_price").text(
                    formatPrice(res.products_price)
                );

            } else {

                $("#products_price").text(
                    res.products_price
                );

            }


            // ==========================================
            // آپدیت بدنه سبد
            // ==========================================

            if (res.cart_body) {

                $("#cart-dropdown-body").html(
                    res.cart_body
                );

            }


            // ==========================================
            // آپدیت فوتر سبد
            // ==========================================

            if (res.cart_footer) {

                $(".shopping-cart-box .card-footer")
                    .replaceWith(res.cart_footer);

            }


            // ==========================================
            // تبدیل دکمه افزودن به کنترل تعداد
            // ==========================================

            if (res.status === "added") {

                btn.replaceWith(`
            
                    <div
                        class="product-detail-cart-quantity"
                        id="product-detail-cart-control"
                        data-product="${productId}"
                        data-item-id="${res.item_id}">
            
                        <!-- کاهش / حذف - سمت چپ -->
                        <span
                            class="product-detail-decrease decrease_product c-pointer">
            
                            <i class="far fa-trash-alt"></i>
            
                        </span>
            
                        <!-- تعداد -->
                        <span
                            class="fs-5 quantity"
                            id="product-detail-quantity">
            
                            1
            
                        </span>
            
                        <!-- افزایش - سمت راست -->
                        <span
                            class="product-detail-add add_product c-pointer">
            
                            <i class="fas fa-plus"></i>
            
                        </span>
            
                    </div>
            
                `);

            }
        },

        error: function (xhr) {

            console.log("AJAX ERROR:", xhr.status);
            console.log(xhr.responseText);

        }

    });

});



// ==========================================
// افزایش تعداد - Product Detail
// ==========================================

$(document).on(
    "click",
    "#product-detail-cart-control .product-detail-add",
    function (e) {

        e.preventDefault();

        const control = $(this).closest(
            "#product-detail-cart-control"
        );

        const itemId = control.data("item-id");

        if (!itemId) {
            console.log("ProductVariant ID پیدا نشد");
            return;
        }

        update_quantity(
            itemId,
            "add"
        );

    }
);



// ==========================================
// کاهش تعداد / حذف - Product Detail
// ==========================================

$(document).on(
    "click",
    "#product-detail-cart-control .product-detail-decrease",
    function (e) {

        e.preventDefault();

        const control = $(this).closest(
            "#product-detail-cart-control"
        );

        const itemId = control.data("item-id");

        if (!itemId) {
            console.log("ProductVariant ID پیدا نشد");
            return;
        }

        update_quantity(
            itemId,
            "decrease"
        );

    }
);

// ==========================================
// تابع اصلی تغییر تعداد
// ==========================================

function update_quantity(productId, action) {

    $.ajax({

        url: "/cart/update-quantity/",

        type: "POST",

        data: {
            item_id: productId,
            action: action
        },

        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },

        success: function (res) {

            console.log("UPDATE CART:", res);

            if (res.error) {
                console.log(res.error);
                return;
            }


            // ==================================
            // آپدیت تعداد کلی سبد در هدر
            // ==================================

            $("#cart_badge").text(res.cart_count);

            $("#cart_info").text(res.cart_count);


            // ==================================
            // آپدیت مبلغ محصولات
            // ==================================

            if (typeof formatPrice === "function") {

                $("#products_price").text(
                    formatPrice(res.products_price)
                );

            } else {

                $("#products_price").text(
                    res.products_price
                );
            }


            // ==================================
            // آپدیت بدنه Dropdown سبد
            // ==================================

            if (res.cart_body) {

                $("#cart-dropdown-body").html(
                    res.cart_body
                );
            }


            // ==================================
            // آپدیت Footer سبد
            // ==================================

            if (res.cart_footer) {

                $(".shopping-cart-box .card-footer")
                    .replaceWith(res.cart_footer);
            }


            // ==================================
            // پیدا کردن کنترل محصول در Product Detail
            // ==================================

            const control = $("#product-detail-cart-control");


            // ==================================
            // اگر محصول حذف شده
            // ==================================

            if (res.item_count === 0) {

                control.replaceWith(`

                    <a href="javascript:void(0);"
                       id="product-detail-cart-btn"
                       class="btn-auth text-center fs-6"
                       data-product="${res.product_id}">

                        افزودن به سبد خرید

                    </a>

                `);

                return;
            }


            // ==================================
            // آپدیت تعداد
            // ==================================

            control.find(".quantity").text(
                res.item_count
            );


            // ==================================
            // تغییر آیکون کاهش / حذف
            // ==================================

            const decreaseButton =
                control.find(".product-detail-decrease");


            if (res.item_count > 1) {

                decreaseButton.html(
                    '<i class="fas fa-minus"></i>'
                );

            } else {

                decreaseButton.html(
                    '<i class="far fa-trash-alt"></i>'
                );
            }

        },

        error: function (xhr) {

            console.log(
                "UPDATE QUANTITY ERROR:",
                xhr.status
            );

            console.log(
                xhr.responseText
            );
        }

    });
}