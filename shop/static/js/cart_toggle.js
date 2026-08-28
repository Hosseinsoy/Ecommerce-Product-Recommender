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

function formatPrice(price) {
    return Number(price).toLocaleString('fa-IR');
}

$(document).on("click", ".cart-btn", function (e) {

    e.preventDefault();


    const btn = $(this);
    const productId = String(btn.data("product")).replace(/,/g, "");



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

$(document).on(
    "click",
    "#product-detail-cart-btn",
    function (e) {

        e.preventDefault();

        const btn = $(this);

        const productId = String(btn.data("product")).replace(/,/g, "");

        // پیدا کردن Variant انتخاب شده
        const variantId = getSelectedVariantId();

        if (!variantId) {

            alert("لطفاً رنگ و سایز محصول را انتخاب کنید.");

            return;
        }

        console.log(
            "ADD TO CART:",
            "Product:",
            productId,
            "Variant:",
            variantId
        );

        $.ajax({

            url: `/cart/toggle/${productId}/`,

            type: "POST",

            data: {
                variant_id: variantId
            },

            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },

            success: function (res) {

                console.log(
                    "ADD TO CART RESPONSE:",
                    res
                );

                if (!res.success) {

                    console.log(res.error);

                    return;
                }
                // ==========================================
                // آپدیت Variant های موجود در سبد
                // ==========================================

                if (res.status === "added" && res.variant_id) {

                    if (typeof cartVariantQuantities === "object") {

                        cartVariantQuantities[String(res.variant_id)] =
                            res.item_count;

                    }

                    console.log(
                        "CART VARIANT QUANTITIES UPDATED:",
                        cartVariantQuantities
                    );
                }
                // ------------------------------
                // Header
                // ------------------------------

                $("#cart_badge")
                    .text(res.cart_count);

                $("#cart_info")
                    .text(res.cart_count);


                // ------------------------------
                // Cart Dropdown
                // ------------------------------

                if (res.cart_body) {

                    $("#cart-dropdown-body")
                        .html(res.cart_body);

                }


                if (res.cart_footer) {

                    $(".shopping-cart-box .card-footer")
                        .replaceWith(res.cart_footer);

                }


                // ------------------------------
                // تبدیل دکمه به کنترل تعداد
                // ------------------------------

                if (res.status === "added") {

                    btn.replaceWith(`

                        <div
                            class="product-detail-cart-quantity"
                            id="product-detail-cart-control"
                            data-product="${productId}"
                            data-item-id="${res.variant_id}">

                            <span
                                class="decrease product-detail-decrease c-pointer">

                                <i class="far fa-trash-alt"></i>

                            </span>


                            <span
                                class="fs-5 quantity"
                                id="product-detail-quantity">

                                ${res.item_count}

                            </span>


                            <span
                                class="addition product-detail-add c-pointer">

                                <i class="fas fa-plus"></i>

                            </span>

                        </div>

                    `);

                }

            },

            error: function (xhr) {

                console.log(
                    "ADD TO CART ERROR:",
                    xhr.status
                );

                console.log(
                    xhr.responseText
                );

            }

        });

    }
);



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

        updateCartQuantity(
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

        updateCartQuantity(
            itemId,
    "decrease"
        );

    }
);

function sync_cart_detail(res) {

    if (!res || !res.success) {
        return;
    }

    const variantId = String(res.variant_id).replace(/,/g, "");

    console.log(
        "SYNC CART DETAIL:",
        variantId,
        "quantity:",
        res.item_count,
        "total:",
        res.total_price
    );

    $("#cart_items .shopping-cart-item").each(function () {

        const cartItem = $(this);

        const currentVariantId = String(
            cartItem.attr("data-variant-id") || ""
        ).replace(/,/g, "");

        if (currentVariantId !== variantId) {
            return;
        }

        console.log(
            "CART DETAIL ITEM FOUND:",
            currentVariantId
        );

        // تعداد
        cartItem
            .find(".item-quantity")
            .text(res.item_count);

        // مبلغ همان محصول
        cartItem
            .find(".item-total")
            .text(
                Number(res.total_price).toLocaleString("fa-IR") +
                " تومان"
            );

        // اگر تعداد صفر شد، حذفش کن
        if (Number(res.item_count) === 0) {

            cartItem.fadeOut(300, function () {

                $(this).remove();

                if (Number(res.cart_count) === 0) {

                    $("#cart_items").html(`
                        <div class="alert alert-info">
                            سبد خرید شما خالی است
                        </div>
                    `);

                }

            });

        }

        return false;
    });
}


// ==========================================
// افزایش تعداد از Cart Dropdown
// ==========================================

$(document).on(
    "click",
    "#cart-dropdown-body .add_product",
    function (e) {

        e.preventDefault();

        const item = $(this).closest(".shopping-cart-item");

        const itemId = String(item.attr("data-item-id")).replace(/,/g, "");

        console.log("DROPDOWN ADD - Variant ID:", itemId);

        if (!itemId) {
            console.log("ProductVariant ID پیدا نشد");
            return;
        }

        updateCartQuantity(
            itemId,
    "add"
        );
    }
);


// ==========================================
// کاهش تعداد از Cart Dropdown
// ==========================================

$(document).on(
    "click",
    "#cart-dropdown-body .decrease_product",
    function (e) {

        e.preventDefault();

        const item = $(this).closest(".shopping-cart-item");

        const itemId = String(item.attr("data-item-id")).replace(/,/g, "");

        console.log("DROPDOWN DECREASE - Variant ID:", itemId);

        if (!itemId) {
            console.log("ProductVariant ID پیدا نشد");
            return;
        }

        updateCartQuantity(
            itemId,
    "decrease"
        );
    }
);


// ==========================================
// تابع اصلی تغییر تعداد
// ==========================================

function updateCartQuantity(productId, action) {

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

            if (!res.success) {
                console.log(res.error);
                return;
            }
            // ==========================================
            // به‌روزرسانی تعداد Variant در حافظه JS
            // ==========================================

            // ==========================================
            // به‌روزرسانی تعداد Variant
            // ==========================================

            if (res.variant_id) {

                const variantKey = String(res.variant_id);

                if (Number(res.item_count) > 0) {

                    cartVariantQuantities[variantKey] =
                        Number(res.item_count);

                } else {

                    delete cartVariantQuantities[variantKey];

                }

                console.log(
                    "UPDATED QUANTITY:",
                    variantKey,
                    "=>",
                    cartVariantQuantities[variantKey] || 0
                );
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

            // ==========================================
            // Sync صفحه جزئیات سبد خرید
            // ==========================================

            sync_cart_detail(res);

            // ==================================
            // پیدا کردن کنترل محصول در Product Detail
            // ==================================

            const control = $("#product-detail-cart-control");


            // ==================================
            // اگر محصول حذف شده
            // ==================================

            if (res.item_count === 0) {
                if (typeof cartVariantQuantities === "object") {

                    delete cartVariantQuantities[
                        String(res.variant_id)
                    ];

                }

                console.log(
                    "CART VARIANT QUANTITIES AFTER REMOVE:",
                    cartVariantQuantities
                );

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