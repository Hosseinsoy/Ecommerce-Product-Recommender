$(document).ready(function () {

    let currentSort = "newest";

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

        $.ajax({

            url: window.location.pathname + "ajax/",

            type: "GET",

            data: {
                page: page,
                sort: currentSort,

                categories: categories,
                brands: brands,

                min_price: min_price,
                max_price: max_price,

                only_available: only_available,
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