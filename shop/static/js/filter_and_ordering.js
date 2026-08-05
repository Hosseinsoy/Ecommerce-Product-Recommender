$(document).ready(function () {
    const isWishlist = window.location.pathname.includes("/wishlist");
    const ajaxUrl = isWishlist
        ? "/wishlist/ajax/"
        : window.location.pathname + "ajax/";
    let currentSort = "newest";
    function updateUrl(page = 1) {

        const params = new URLSearchParams();

        // دسته بندی ها
        $(".checkbox-category:checked").each(function () {
            params.append("categories", $(this).val());
        });

        // برندها
        $(".checkbox-brand:checked").each(function () {
            params.append("brands", $(this).val());
        });

        // قیمت
        if ($(".input-from").val()) {
            params.set("min_price", $(".input-from").val());
        }

        if ($(".input-to").val()) {
            params.set("max_price", $(".input-to").val());
        }

        // فقط موجود
        if ($("#flexSwitchCheckDefault").is(":checked")) {
            params.set("only_available", 1);
        }

        // مرتب سازی
        params.set("sort", currentSort);

        // صفحه
        params.set("page", page);

        history.replaceState(
            {},
            "",
            window.location.pathname + "?" + params.toString()
        );

    }

    function loadProducts(page = 1) {

        const categories = [];
        $(".checkbox-category:checked").each(function () {
            categories.push($(this).val());
        });

        const brands = [];
        $(".checkbox-brand:checked").each(function () {
            brands.push($(this).val());
        });

        const min_price = $(".input-from").val();
        const max_price = $(".input-to").val();
        const only_available = $("#flexSwitchCheckDefault").is(":checked") ? 1 : 0;
        updateUrl(page);
        $.ajax({

             url: ajaxUrl,

            type: "GET",

            data: {
                page: page,
                sort: currentSort,

                categories: categories,
                brands: brands,

                min_price: min_price,
                max_price: max_price,

                ...(only_available ? { only_available: 1 } : {}),
            },

            traditional: true,

            success: function (response) {

                $("#products-container").html(response.html);
                $("#product-count").text(response.count + " کالا");

            }

        });

    }


    // ----------------------------
    // تغییر دسته بندی
    // ----------------------------
    $(document).on("change", ".checkbox-category", function () {
        if (isWishlist) {
                loadProducts(1);
                return;
            }
        const categories = [];

        $(".checkbox-category:checked").each(function () {
            categories.push($(this).val());
        });

        $.ajax({

            url: "/ajax/category-brands/",

            data: {
                categories: categories
            },

            traditional: true,

            success: function (brands) {

                let html = "";

                brands.forEach(function (brand) {

                    html += `
                        <li class="item-brand">
                            <a href="#">
                                ${brand.name}
                            </a>

                            <label>
                                <input
                                    type="checkbox"
                                    class="form-check-input checkbox-brand"
                                    name="brand"
                                    value="${brand.id}">
                            </label>
                        </li>
                    `;

                });

                $("#brand-list").html(html);

                loadProducts(1);

            }

        });

    });


    // ----------------------------
    // تغییر برند
    // ----------------------------
    $(document).on("change", ".checkbox-brand", function () {

        loadProducts(1);

    });


    // ----------------------------
    // فقط کالاهای موجود
    // ----------------------------
    $(document).on("change", "#flexSwitchCheckDefault", function () {

        loadProducts(1);

    });


    // ----------------------------
    // فیلتر قیمت
    // ----------------------------
    $(document).on("click", ".btn-filter", function (e) {

        e.preventDefault();

        loadProducts(1);

    });


    // ----------------------------
    // مرتب سازی
    // ----------------------------
    $(document).on("click", ".ordering .option", function (e) {

        e.preventDefault();

        $(".ordering .option").removeClass("active");

        $(this).addClass("active");

        currentSort = $(this).data("sort");

        loadProducts(1);

    });


    // ----------------------------
    // صفحه بندی
    // ----------------------------
    $(document).on("click", ".page-link-ajax", function (e) {

        e.preventDefault();

        loadProducts($(this).data("page"));

    });

});

// ================= Wishlist =================

$(document).on("click", ".wishlist-btn", function (e) {

    e.preventDefault();

    const btn = $(this);
    const productId = btn.data("product");

    $.ajax({

        url: `/wishlist/toggle/${productId}/`,
        type: "POST",

        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },

        success: function (response) {

            if (response.status === "added") {

                btn.addClass("active");

            } else {

                btn.removeClass("active");

                // فقط اگر داخل صفحه علاقه‌مندی هستیم آیتم حذف شود
                if (window.location.pathname === "/wishlist/") {

                    const item = $("#wishlist-product-" + productId);

                    item.fadeOut(250, function () {

                        $(this).remove();

                        if ($("#wishlist-product-list .product-item").length === 0) {

                            $("#wishlist-product-list").html(`
                                <h5 class="text-center text-muted py-5">
                                    محصولی یافت نشد.
                                </h5>
                            `);

                        }

                    });

                }

            }

            // بروزرسانی تعداد علاقه‌مندی
            $(".wishlist-count").text(response.wishlist_count);

            // بروزرسانی دراپ‌داون هدر
            if (response.wishlist_html) {

                $("#wishlist-dropdown-body").html(response.wishlist_html);

            }

        },

        error: function (xhr) {

            console.log(xhr.responseText);

        }

    });

});
function getCookie(name) {

    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {

        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i++) {

            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + "=")) {

                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));

                break;

            }

        }

    }

    return cookieValue;

}