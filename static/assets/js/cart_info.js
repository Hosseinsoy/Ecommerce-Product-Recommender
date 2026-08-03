        $(document).ready(function (){
            function formatPrice(price) {
                return Number(price).toLocaleString('fa-IR');
            }

            $('.add_product').on('click', function (){
                var itemId = $(this).closest('.item').data('item-id');
                update_quantity(itemId, 'add');
            });

            $('.decrease_product').on('click', function () {
                var itemId = $(this).closest('.item').data('item-id');
                var quantity = parseInt($('#quantity-' + itemId).text());
                update_quantity(itemId, 'decrease');

            });
            // $('.remove_product').on('click', function (){
            //     var itemId = $(this).closest('.item').data('item-id');
            //     remove_item(itemId);
            // });
            function update_quantity(item_id, action) {
                $.ajax({
                    type: 'POST',
                    url: updateCartUrl,
                    data: {
                        item_id: item_id,
                        action: action,
                        csrfmiddlewaretoken: csrfToken
                    },
                    success: function (data) {
                    if (data.item_count == 0) {
                        $(`.item[data-item-id="${item_id}"]`).remove();
                        $('#cart_badge').text(data.cart_count);
                        $('#cart_info').text(data.cart_count);
                        $('#products_price').text(formatPrice(data.products_price));

                        if (data.cart_count == 0) {
                            $('.cartParent').html(`
                                <p class="noProductInCart text-center fs-6">
                                    محصولی در سبد خرید وجود ندارد!
                                </p>
                            `);

                            $('.card-footer').hide();
                        }
                        return;
                    }
                        // تعداد کالاها
                        $('#cart_info').text(data.cart_count);
                        $('#cart_badge').text(data.cart_count);

                        // تعداد همین محصول
                        $('#quantity-' + item_id).text(data.item_count);

                        let btn = $('.item[data-item-id="' + item_id + '"] .decrease_product');

                        if (data.item_count == 1) {
                            btn.html('<i class="far fa-trash-alt"></i>');
                        } else {
                            btn.html('<i class="fas fa-minus"></i>');
                        }

                        // قیمت بعد از تخفیف
                        $('#total-price-' + item_id).text(formatPrice(data.total_price) + ' تومان');

                        // اگر تخفیف داشت
                        if (data.off > 0) {

                            $('#old-price-' + item_id).text(formatPrice(data.old_total_price) + ' تومان');
                            $('#off-' + item_id).text(data.off + '٪ تخفیف');
                            $('#old-price-wrapper-' + item_id).show();

                        } else {

                            $('#old-price-wrapper-' + item_id).hide();

                        }

                        // مبلغ کل سبد
                        $('#products_price').text(formatPrice(data.products_price));

                        // اگر سبد خالی شد
                        if (data.cart_count == 0) {

                            $('.cartParent').html(`
                                <p class="noProductInCart text-center fs-6">
                                    محصولی در سبد خرید وجود ندارد!
                                </p>
                            `);

                            $('.card-footer').hide();

                        } else {

                            $('.card-footer').show();

                        }

                    },
                    error: function (xhr) {
                        console.log(xhr.responseText);
                    }
                });
            }
            // function remove_item(item_id){
            //     $.ajax({
            //         type: 'POST',
            //         url: removeCartUrl,
            //         data: {
            //             'item_id': item_id,
            //             csrfmiddlewaretoken: csrfToken
            //         },
            //         success: function (data) {
            //
            //             let item = $(`.item[data-item-id="${item_id}"]`);
            //
            //             item.fadeOut(300, function () {
            //
            //                 $(this).remove();
            //
            //                 $('#cart_badge').text(data.cart_count);
            //                 $('#cart_info').text(data.cart_count);
            //                 $('#products_price').text(data.products_price);
            //
            //                 if (data.cart_count == 0) {
            //                     $('.cartParent').html(`
            //                         <p class="noProductInCart text-center fs-6">
            //                             محصولی در سبد خرید وجود ندارد!
            //                         </p>
            //                     `);
            //
            //                     $('.card-footer').hide();
            //                 }
            //
            //             });
            //
            //         }                })
            // }
        })
