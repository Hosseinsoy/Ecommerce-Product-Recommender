$(document).ready(function () {

    const isWishlist = window.location.pathname.includes("/wishlist");

    const isSearchPage =
        typeof pageType !== "undefined"
        && pageType === "search";

    if(isSearchPage){

        $("#flexSwitchCheckDefault")
            .prop("checked", false);

    }

    const isBrandPage =
        typeof pageType !== "undefined"
        && pageType === "brand";


    const isCategoryPage =
        typeof pageType !== "undefined"
        && pageType === "category";


    const isProductsPage =
        typeof pageType !== "undefined"
        && pageType === "products";


    let ajaxUrl = "";


    if (isWishlist) {

        ajaxUrl = "/wishlist/ajax/";

    }
    else if (isProductsPage) {

        ajaxUrl = "/products/ajax/";

    }
    else if (isSearchPage) {

        ajaxUrl = "/search-result/ajax/";

    }
    else {

        ajaxUrl = window.location.pathname + "ajax/";

    }




    let currentSort = "newest";

    let searchQuery = new URLSearchParams(window.location.search).get("q") || "";

    // let searchQuery = "";

    if (isSearchPage) {

        searchQuery = new URLSearchParams(
            window.location.search
        ).get("q") || "";

    }

    console.log("INITIAL SEARCH QUERY:", searchQuery);

    function updateUrl(page = 1) {

        const params = new URLSearchParams();

        if(isSearchPage && searchQuery){

            params.set(
                "q",
                searchQuery
            );

        }


        $(".checkbox-category:checked").each(function () {
            params.append("categories", $(this).val());
        });


        $(".checkbox-brand:checked").each(function () {
            params.append("brands", $(this).val());
        });



        if ($(".input-from").val()) {

            params.set(
                "min_price",
                $(".input-from").val()
            );

        }



        if ($(".input-to").val()) {

            params.set(
                "max_price",
                $(".input-to").val()
            );

        }



        if ($("#flexSwitchCheckDefault").is(":checked")) {

            params.set(
                "only_available",
                1
            );

        }



        params.set(
            "sort",
            currentSort
        );



        params.set(
            "page",
            page
        );



        history.replaceState(
            {},
            "",
            window.location.pathname + "?" + params.toString()
        );

    }





    function loadProducts(page = 1) {


        const categories = [];

        $(".checkbox-category:checked").each(function () {

            categories.push(
                $(this).val()
            );

        });



        const brands = [];

        $(".checkbox-brand:checked").each(function () {

            brands.push(
                $(this).val()
            );

        });



        const min_price =
            $(".input-from").val();


        const max_price =
            $(".input-to").val();



            let only_available =
            $("#flexSwitchCheckDefault").is(":checked")
            ? 1
            : 0;
            console.log("ONLY AVAILABLE:", only_available);
            console.log("CURRENT SEARCH:", searchQuery);


        updateUrl(page);



        console.log("LOAD PRODUCTS START");
        console.log("URL:", ajaxUrl);

        console.log(
            "SEARCH QUERY:",
            new URLSearchParams(window.location.search).get("q")
        );

        $.ajax({

            url: ajaxUrl,

            type: "GET",


            data: {

                q: searchQuery,

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


                console.log(
                    "AJAX RESPONSE COUNT:",
                    response.count
                );


                $("#products-container")
                    .html(response.html);



                $("#product-count")
                    .text(
                        response.count + " کالا"
                    );


            },


            error: function(xhr){

                console.log(
                    xhr.responseText
                );

            }


        });


    }






    // ==========================
    // تغییر دسته بندی
    // ==========================


    $(document).on(
    "change",
    ".checkbox-category",
    function () {


        if (isWishlist) {

            loadProducts(1);

            return;

        }


        if (isBrandPage) {

            loadProducts(1);

            return;

        }



            // ==========================
            // Category page فقط برندها را آپدیت کند
            // ==========================

            if (isCategoryPage || isProductsPage){


                const categories = [];


                $(".checkbox-category:checked")
                    .each(function(){

                        categories.push(
                            $(this).val()
                        );

                    });



                $.ajax({

                    url: "/ajax/category-brands/",


                    data: {
                        categories: categories
                    },


                    traditional:true,


                    success:function(brands){


                        let html = "";


                        brands.forEach(function(brand){


                            html += `
            
                            <li class="item-brand">
            
                                <label>
            
                                    <input
            
                                    type="checkbox"
            
                                    class="form-check-input checkbox-brand"
            
                                    value="${brand.id}">
            
                                    ${brand.name}
            
                                </label>
            
                            </li>
            
                            `;


                        });



                        $("#brand-list")
                            .html(html);



                        loadProducts(1);


                    }


                });


            }
            else {


                // products page و brand page
                // فقط محصولات تغییر کنند

                loadProducts(1);


            }


        }
    );







    // ==========================
    // تغییر برند
    // ==========================


    $(document).on(
        "change",
        ".checkbox-brand",
        function(){

            console.log("BRAND CHANGED");

            console.log(
                "BRAND ID:",
                $(this).val()
            );


            loadProducts(1);


        }
    );






    // ==========================
    // فقط موجود
    // ==========================


    $(document).on(
        "change",
        "#flexSwitchCheckDefault",
        function(){

            loadProducts(1);

        }
    );







    // ==========================
    // قیمت
    // ==========================


    $(document).on(
        "click",
        ".btn-filter",
        function(e){

            e.preventDefault();

            loadProducts(1);

        }
    );







    // ==========================
    // مرتب سازی
    // ==========================


    $(document).on(
        "click",
        ".ordering .option",
        function(e){


            e.preventDefault();


            $(".ordering .option")
                .removeClass("active");



            $(this)
                .addClass("active");



            currentSort =
                $(this)
                .data("sort");



            loadProducts(1);


        }
    );








    // ==========================
    // pagination
    // ==========================


    $(document).on(
        "click",
        ".page-link-ajax",
        function(e){


            e.preventDefault();



            loadProducts(
                $(this).data("page")
            );


        }
    );



});








// ==========================
// Wishlist
// ==========================


$(document).on(
    "click",
    ".wishlist-btn",
    function(e){


        e.preventDefault();



        const btn = $(this);


        const productId =
            btn.data("product");



        $.ajax({


            url:
            `/wishlist/toggle/${productId}/`,



            type:"POST",



            headers:{


                "X-CSRFToken":
                getCookie("csrftoken")


            },



            success:function(response){



                if(response.status === "added"){


                    btn.addClass("active");


                }
                else{


                    btn.removeClass("active");



                    if(
                        window.location.pathname === "/wishlist/"
                    ){


                        const item =
                        $("#wishlist-product-"+productId);



                        item.fadeOut(
                            250,
                            function(){

                                $(this).remove();


                            }
                        );


                    }


                }



                $(".wishlist-count")
                    .text(
                        response.wishlist_count
                    );



                if(response.wishlist_html){


                    $("#wishlist-dropdown-body")
                    .html(
                        response.wishlist_html
                    );


                }



            }



        });



    }
);







function getCookie(name) {


    let cookieValue = null;



    if(document.cookie && document.cookie !== ""){


        const cookies =
        document.cookie.split(";");



        for(let i=0;i<cookies.length;i++){


            const cookie =
            cookies[i].trim();



            if(
                cookie.substring(
                    0,
                    name.length+1
                )
                ===
                (name+"=")
            ){


                cookieValue =
                decodeURIComponent(
                    cookie.substring(
                        name.length+1
                    )
                );


                break;


            }


        }


    }


    return cookieValue;


}