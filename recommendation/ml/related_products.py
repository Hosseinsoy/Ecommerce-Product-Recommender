from shop.models import Product


class RelatedProductService:


    def __init__(self, content_model):

        self.content_model = content_model



    def get_related_products(
        self,
        product,
        limit=5
    ):


        similar_products = self.content_model.get_similar_products(
            product,
            top_k=limit + 10
        )


        result = []


        for item, score in similar_products:

            if item.id == product.id:
                continue


            result.append(item)


            if len(result) >= limit:
                break


        return result