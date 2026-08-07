$(document).ready(function () {

    let timer;

    const searchBox = $(".search-results");

    const defaultSearchHTML = searchBox.html();


    // جلوگیری از باز شدن با کلیک روی input
    $("#mainSearchInput").on("focus click", function () {

        if ($(this).val().trim().length < 2) {

            searchBox.hide();

        }

    });


    $("#mainSearchInput").on("input", function () {


        clearTimeout(timer);


        const query = $(this).val().trim();



        // اگر کمتر از ۲ کاراکتر بود
        if (query.length < 2) {


            searchBox.html(defaultSearchHTML);

            searchBox.hide();


            return;

        }



        timer = setTimeout(function () {


            $.ajax({

                url: "/search/ajax/",

                type: "GET",

                data: {
                    q: query
                },


                success: function (response) {


                    searchBox.html(
                        `
                        <span class="py-2 px-3 d-block fs-7">
                            نتایج جست و جو :
                        </span>

                        ${response.html}


                        <div class="search-result-item position-relative border-bottom p-3">

                            <div class="d-flex justify-content-between align-items-center ms-2 text-center">

                                <span class="d-inline-block fw-bold ms-1">
                                    مشاهده همه نتایج
                                </span>

                                <i class="fa fa-arrow-left"></i>

                            </div>


                            <a href="/search-result/?q=${query}" 
                               class="stretched-link">
                            </a>

                        </div>
                        `
                    );


                    searchBox.show();


                },


                error: function (xhr) {

                    console.log(xhr.responseText);

                }


            });



        }, 300);



    });



    // بستن وقتی بیرون کلیک شد
    $(document).on("click", function (e) {


        if (!$(e.target).closest(".main-search").length) {


            searchBox.hide();


        }


    });


});