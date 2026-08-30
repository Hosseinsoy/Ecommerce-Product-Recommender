from shop.models import Product


class CartRecommender:


    def __init__(
            self,
            content_model
    ):

        self.content_model = content_model



    # =====================================
    # Recommend products from cart context
    # =====================================

    def recommend_from_cart(
            self,
            cart_products,
            limit=5
    ):

        """
        پیشنهاد محصول بر اساس محصولات موجود در سبد خرید

        روش:
        - برای هر محصول داخل سبد، محصولات مشابه پیدا می‌شود
        - امتیاز similarity محصولات مشابه جمع می‌شود
        - محصولاتی که خودشان داخل سبد هستند حذف می‌شوند
        - بهترین‌ها برگردانده می‌شوند

        """

        if not cart_products:

            return []



        # محصولات فعلی سبد
        cart_product_ids = {
            product.id
            for product in cart_products
        }



        # امتیاز نهایی هر محصول
        product_scores = {}


        # نگهداری object محصول برای جلوگیری از query اضافه
        product_objects = {}



        # =====================================
        # Similarity برای هر محصول سبد
        # =====================================

        for cart_product in cart_products:



            similar_products = (
                self.content_model
                .get_similar_products(
                    cart_product.id,
                    top_k=20
                )
            )



            for product, similarity_score in similar_products:



                # حذف محصولات داخل سبد
                if product.id in cart_product_ids:

                    continue



                # ذخیره object محصول
                product_objects[
                    product.id
                ] = product



                # تجمیع امتیاز similarity
                product_scores[
                    product.id
                ] = (

                    product_scores.get(
                        product.id,
                        0.0
                    )

                    +

                    similarity_score

                )



        # اگر چیزی پیدا نشد
        if not product_scores:

            return []



        # =====================================
        # Ranking نهایی
        # =====================================

        ranked_products = sorted(

            product_scores.items(),

            key=lambda item: item[1],

            reverse=True

        )



        # =====================================
        # خروجی نهایی
        # =====================================

        recommendations = []


        for product_id, score in ranked_products[:limit]:


            product = product_objects.get(
                product_id
            )


            if product:

                recommendations.append(
                    product
                )



        return recommendations