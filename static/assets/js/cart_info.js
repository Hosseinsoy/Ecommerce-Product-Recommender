$(document).ready(function () {

    function formatPrice(price) {
        return Number(price).toLocaleString("fa-IR");
    }

    $(document).on("click", ".add_product", function () {
        const itemId = $(this).closest(".item").data("item-id");
        update_quantity(itemId, "add");
    });

    $(document).on("click", ".decrease_product", function () {
        const itemId = $(this).closest(".item").data("item-id");
        update_quantity(itemId, "decrease");
    });

    function update_quantity(item_id, action) {

        $.ajax({

            type: "POST",
            url: updateCartUrl,

            data: {
                item_id: item_id,
                action: action,
                csrfmiddlewaretoken: csrfToken
            },

            success: function (data) {

                // =========================
                // بروزرسانی دراپ‌داون
                // =========================

                if (data.cart_body) {
                    $("#cart-dropdown-body").html(data.cart_body);
                }

                if (data.cart_footer) {
                    $(".shopping-cart-box .card-footer").replaceWith(data.cart_footer);
                }

                // =========================
                // تعداد سبد
                // =========================

                $("#cart_badge").text(data.cart_count);
                $("#cart_info").text(data.cart_count);
                // اگر محصول حذف شد، آیکون سبد در لیست محصولات خاموش شود
                if (data.item_count === 0) {

                    $(`.cart-btn[data-product="${data.product_id}"]`)
                        .removeClass("active");

                }
                // اگر داخل صفحه cart نیستیم
                if ($("#quantity-" + item_id).length === 0) {
                    return;
                }

                // =========================
                // حذف کامل محصول
                // =========================

                if (data.item_count === 0) {

                    const currentItem = $(`.item[data-item-id="${item_id}"]`);

                    currentItem.fadeOut(250, function () {

                        $(this).remove();

                        $("#products_price").text(formatPrice(data.products_price));
                        $("#post_price").text(formatPrice(data.post_price));
                        $("#final_price").text(formatPrice(data.final_price));

                        if (data.cart_count === 0) {

                            $(".cartParent").html(`
                                <p class="noProductInCart text-center fs-6">
                                    محصولی در سبد خرید وجود ندارد!
                                </p>
                            `);

                            $(".card-footer").hide();

                        }

                    });

                    return;
                }

                // =========================
                // تعداد
                // =========================

                $("#quantity-" + item_id).text(data.item_count);

                const btn = $(`.item[data-item-id="${item_id}"] .decrease_product`);

                if (data.item_count === 1) {
                    btn.html('<i class="far fa-trash-alt"></i>');
                } else {
                    btn.html('<i class="fas fa-minus"></i>');
                }

                // =========================
                // قیمت همان محصول
                // =========================

                $("#total-price-" + item_id)
                    .text(formatPrice(data.total_price) + " تومان");

                if (data.off > 0) {

                    $("#old-price-" + item_id)
                        .text(formatPrice(data.old_total_price) + " تومان");

                    $("#old-price-wrapper-" + item_id).show();

                } else {

                    $("#old-price-wrapper-" + item_id).hide();

                }

                // =========================
                // مبلغ کل صفحه cart
                // =========================

                $("#products_price").text(formatPrice(data.products_price));
                $("#post_price").text(formatPrice(data.post_price));
                $("#final_price").text(formatPrice(data.final_price));

            },

            error: function (xhr) {
                console.log(xhr.responseText);
            }

        });

    }

});