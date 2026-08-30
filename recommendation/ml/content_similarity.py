from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ContentSimilarity:


    def __init__(self, products):

        self.products = products

        self.product_index = {}

        for index, product in enumerate(products):
            self.product_index[product.id] = index


        texts = []

        for product in products:

            texts.append(
                self.build_product_text(product)
            )


        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1,3),
            min_df=1
        )


        self.matrix = (
            self.vectorizer
            .fit_transform(texts)
        )


    # ==================================

    def build_product_text(
        self,
        product
    ):

        text_parts = []


        # نام محصول
        if product.name:
            text_parts.append(product.name)
            text_parts.append(product.name)
            text_parts.append(product.name)


        # توضیحات
        if product.description:

            text_parts.append(
                product.description
            )


        # دسته بندی
        if product.category:

            text_parts.append(
                product.category.name
            )


        # برند
        if product.brand:

            text_parts.append(
                product.brand.name
            )


        # ویژگی ها
        for feature in product.features.all():

            text_parts.append(
                feature.name
            )

            text_parts.append(
                feature.value
            )


        # رنگ
        for color in product.color_variants.all():

            if color.color:

                text_parts.append(
                    color.color
                )


        # سایز
        for size in product.size_variants.all():

            if size.size:

                text_parts.append(
                    size.size
                )


        return " ".join(
            text_parts
        )



    # ==================================

    def similarity(
        self,
        product_id,
        liked_product_ids
    ):


        if not liked_product_ids:

            return 0.0


        if product_id not in self.product_index:

            return 0.0


        product_index = (
            self.product_index[
                product_id
            ]
        )


        liked_indexes = []


        for pid in liked_product_ids:

            if pid in self.product_index:

                liked_indexes.append(
                    self.product_index[pid]
                )


        if not liked_indexes:

            return 0.0



        scores = cosine_similarity(

            self.matrix[
                product_index
            ],

            self.matrix[
                liked_indexes
            ]

        )


        return float(
            scores.max()
        )

    # ==================================
    # Similar products for a product
    # ==================================

    def get_similar_products(
            self,
            product_id,
            top_k=20
    ):


        if product_id not in self.product_index:
            return []


        product_index = self.product_index[product_id]


        scores = cosine_similarity(

            self.matrix[product_index],

            self.matrix

        )[0]


        similar_indexes = scores.argsort()[::-1]


        results = []


        for index in similar_indexes:


            # خود محصول را حذف کن
            if index == product_index:
                continue


            product = self.products[index]


            results.append(
                (
                    product,
                    float(scores[index])
                )
            )


            if len(results) >= top_k:
                break


        return results