// ==========================================
// انتخاب رنگ
// ==========================================

$(document).on("change", "input[name='color']", function () {

    const color = $(this).data("color");

    $("#selectedColor").text(color);

});


// ==========================================
// انتخاب سایز
// ==========================================

$(document).on("change", "input[name='size']", function () {

    const size = $(this).data("size");

    $("#selectedSize").text(size);
    updateCartButtonForSelectedVariant();

});
$(document).ready(function () {

    $(".color-label").each(function () {

        const color = $(this).data("color");

        $(this).css(
            "background-color",
            getColorValue(color)
        );

    });

});
function getSelectedVariant() {

    const colorId = $("input[name='color']:checked").val();
    const sizeId = $("input[name='size']:checked").val();

    return {
        color_id: colorId || null,
        size_id: sizeId || null
    };
}

//


function getSelectedVariantId() {

    const colorId = $("input[name='color']:checked").val() || null;
    const sizeId = $("input[name='size']:checked").val() || null;

    const variant = productVariants.find(function (item) {

        return String(item.color_id) === String(colorId)
            && String(item.size_id) === String(sizeId);

    });

    if (!variant) {

        console.log(
            "VARIANT NOT FOUND",
            "color:",
            colorId,
            "size:",
            sizeId
        );

        return null;
    }

    console.log(
        "SELECTED VARIANT:",
        variant.id
    );

    return variant.id;
}

// ==========================================
// گرفتن تعداد Variant از سبد خرید
// ==========================================

function getCartVariantQuantity(variantId) {

    const key = String(variantId);

    return Number(
        cartVariantQuantities[key] || 0
    );
}


// ==========================================
// بررسی وجود Variant انتخاب شده در سبد خرید
// ==========================================

function isSelectedVariantInCart() {

    const variantId = getSelectedVariantId();

    if (!variantId) {
        return false;
    }

    const quantities = cartVariantQuantities || {};

    return Object.prototype.hasOwnProperty.call(
        quantities,
        String(variantId)
    );
}

// ==========================================
// آپدیت وضعیت دکمه سبد خرید بر اساس Variant
// ==========================================

function updateCartButtonForSelectedVariant() {

    const variantId = getSelectedVariantId();

    if (!variantId) {
        return;
    }

    const quantity = Number(
        cartVariantQuantities[String(variantId)] || 0
    );

    const control = $("#product-detail-cart-control");
    const btn = $("#product-detail-cart-btn");

    console.log(
        "UPDATE VARIANT UI:",
        variantId,
        "QUANTITY:",
        quantity
    );

    // Variant داخل سبد نیست
    if (quantity === 0) {

        if (control.length) {

            const productId = control.data("product");

            control.replaceWith(`
                <a
                    href="javascript:void(0);"
                    id="product-detail-cart-btn"
                    class="btn-auth text-center fs-6"
                    data-product="${productId}">

                    افزودن به سبد خرید

                </a>
            `);
        }

        return;
    }

    // Variant داخل سبد است
    if (btn.length) {

        const productId = btn.data("product");

        btn.replaceWith(`
            <div
                id="product-detail-cart-control"
                class="product-detail-cart-quantity"
                data-product="${productId}"
                data-item-id="${variantId}">

                <span class="decrease product-detail-decrease c-pointer">

                    ${
                        quantity > 1
                        ? '<i class="fas fa-minus"></i>'
                        : '<i class="far fa-trash-alt"></i>'
                    }

                </span>

                <span class="fs-5 quantity">
                    ${quantity}
                </span>

                <span class="addition product-detail-add c-pointer">
                    <i class="fas fa-plus"></i>
                </span>

            </div>
        `);

        return;
    }

    // کنترل از قبل وجود دارد؛ فقط Variant و تعداد را عوض کن
    if (control.length) {

        control.attr(
            "data-item-id",
            variantId
        );

        control.find(".quantity").text(quantity);

        if (quantity > 1) {

            control
                .find(".product-detail-decrease")
                .html('<i class="fas fa-minus"></i>');

        } else {

            control
                .find(".product-detail-decrease")
                .html(
                    '<i class="far fa-trash-alt"></i>'
                );
        }
    }
}

$(document).on("change", 'input[name="color"]', function () {

    const colorName = $(this).data("color");

    $("#selectedColor").text(colorName);

    updateCartButtonForSelectedVariant();

});
// ==========================================
// انتخاب رنگ محصول
// ==========================================

$(document).on("click", ".color-option", function (e) {

    e.preventDefault();

    const colorName = $(this).data("color");
    const colorId = $(this).data("color-id");

    console.log("COLOR CLICKED:", colorName);
    console.log("COLOR ID:", colorId);

    // انتخاب واقعی radio
    const input = $(
        `input[name="color"][value="${colorId}"]`
    );

    input.prop("checked", true);

    // آپدیت نام رنگ
    $("#selectedColor").text(colorName);

    console.log(
        "CHECKED COLOR:",
        $("input[name='color']:checked").val()
    );
    updateCartButtonForSelectedVariant();

});

$(document).ready(function () {

    const firstColor = $('input[name="color"]:checked')
        .attr("data-color");

    if (firstColor) {
        $("#selectedColor").text(firstColor);
    }

});
$(document).on("change", 'input[name="color"]', function () {

    alert($(this).attr("data-color"));

});

$(document).on("change", "input[name='color']", function () {

    // حذف حالت انتخاب از همه رنگ‌ها
    $("input[name='color']").each(function () {

        const label = $(
            "label[for='" + this.id + "']"
        );

        label.removeClass("selected-color");

    });

    // اضافه کردن حالت انتخاب به رنگ فعلی
    const selectedLabel = $(
        "label[for='" + this.id + "']"
    );

    selectedLabel.addClass("selected-color");

});

$(document).ready(function () {

    // صبر می‌کنیم تا DOM و انتخاب‌های پیش‌فرض کامل شوند
    setTimeout(function () {

        updateCartButtonForSelectedVariant();

    }, 0);

});