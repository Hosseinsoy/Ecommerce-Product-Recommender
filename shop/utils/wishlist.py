from shop.models import Product


def get_wishlist(session):
    return session.get("wishlist", [])


def save_wishlist(session, wishlist):
    session["wishlist"] = wishlist
    session.modified = True


def add_to_wishlist(session, product_id):
    wishlist = get_wishlist(session)

    if product_id not in wishlist:
        wishlist.append(product_id)

    save_wishlist(session, wishlist)


def remove_from_wishlist(session, product_id):
    wishlist = get_wishlist(session)

    if product_id in wishlist:
        wishlist.remove(product_id)

    save_wishlist(session, wishlist)


def wishlist_count(session):
    return len(get_wishlist(session))