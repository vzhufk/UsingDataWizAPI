import datetime

from django.core.cache import cache
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import loader

from dwapi import datawiz

# dw = datawiz.DW("test1@mail.com", "test2@cbe47a5c9466fe6df05f04264349f32b")

dw = None

DEF_DATE_FROM = "2015-11-17"
DEF_DATE_TO = "2015-11-18"

CACHE_TIMEOUT = 60 * 5


# Because of Heroku cache specifics
def client_info():
    if dw is not None:
        if cache.get('client_info') is None:
            cache.set('client_info', dw.get_client_info())
        if cache.get('shops') is None:
            cache.set('shops', dw.get_shops())
    else:
        return HttpResponseRedirect("/sign.html")


def sign(request):
    """
    :param request: HTTP Request
    :return:
    GET: Same page
    POST: Login user and redirect to User page
    """
    global dw
    dw = None

    if request.method == 'GET':
        context = {
            'login': "test1@mail.com",
            'password': "test2@cbe47a5c9466fe6df05f04264349f32b"
        }
        return render(request, "sign.html", context)
    elif request.method == 'POST':
        dw = datawiz.DW(request.POST['login'], request.POST['password'])
        # if signed
        client_info()
        return HttpResponseRedirect("/user.html")


def user(request):
    """
    :param request:
    :return:
    GET: Client info and client shops
    """
    client_info()

    template = loader.get_template('user.html')
    if request.method == 'GET':
        context = {
            'user': cache.get('client_info'),
            'shops': cache.get('shops'),
        }
    return HttpResponse(template.render(context, request))


def shop(request, key):
    """
    :param request: HTTP Request
    :param key: Shop ID
    :return:
    GET: Shop info
    """
    client_info()

    template = loader.get_template('shop.html')
    context = {'id': key,
               'shop': cache.get('shops')[int(key)]}
    return HttpResponse(template.render(context, request))


def turnover(request, key):
    """
    :param request: HTTP Request
    :param key: Shop ID
    :return: Shop Turnover Data
    """
    client_info()

    template = loader.get_template('turnover.html')
    current = cache.get('shops')[int(key)]
    if request.method == 'POST':
        date_from = datetime.datetime.strptime(request.POST['date_from'], '%Y-%m-%d')
        date_to = datetime.datetime.strptime(request.POST['date_to'], '%Y-%m-%d')
    else:
        date_from = datetime.datetime.strptime(DEF_DATE_FROM, '%Y-%m-%d')
        date_to = datetime.datetime.strptime(DEF_DATE_TO, '%Y-%m-%d')

    date_from_str = date_from.strftime('%Y-%m-%d')
    date_to_str = date_to.strftime('%Y-%m-%d')
    data = cache.get('turnover:' + date_from_str + "/" + date_to_str)

    if data is None:
        turn = dw.get_categories_sale(categories=['sum'], shops=int(key), by='turnover',
                                      date_from=date_from, date_to=date_to, view_type="represent")
        product = dw.get_categories_sale(categories=['sum'], shops=int(key), by='qty',
                                         date_from=date_from, date_to=date_to, view_type="represent")
        receipts = dw.get_categories_sale(categories=['sum'], shops=int(key), by='receipts_qty',
                                          date_from=date_from, date_to=date_to, view_type="represent")
        data = {'from': {
            'turnover': turn.at[date_from_str, "sum"],
            'products': product.at[date_from_str, "sum"],
            'receipts': receipts.at[date_from_str, "sum"],
            'average_receipt': turn.at[date_from_str, "sum"] / receipts.at[date_from_str, "sum"],
        }, 'to': {
            'turnover': turn.at[date_to_str, "sum"],
            'products': product.at[date_to_str, "sum"],
            'receipts': receipts.at[date_to_str, "sum"],
            'average_receipt': turn.at[date_to_str, "sum"] / receipts.at[date_to_str, "sum"],
        }}
        data['difference'] = {
            'turnover': data['to']['turnover'] - data['from']['turnover'],
            'products': data['to']['products'] - data['from']['products'],
            'receipts': data['to']['receipts'] - data['from']['receipts'],
            'average_receipt': data['to']['average_receipt'] - data['from']['average_receipt'],
        }
        data['percent'] = {
            'turnover': data['difference']['turnover'] / data['from']['turnover'] * 100,
            'products': data['difference']['products'] / data['from']['products'] * 100,
            'receipts': float(data['difference']['receipts']) / data['from']['receipts'] * 100,
            'average_receipt': data['difference']['average_receipt'] / data['from']['average_receipt'] * 100,
        }

        cache.set('turnover:' + date_from_str + "/" + date_to_str, data)

    context = {
        'name': current['name'],
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'data': data,
    }

    return HttpResponse(template.render(context, request))


def sale(request, key):
    """
    :param request: HTTP Request
    :param key: Shop ID
    :return: Shop Sale Data
    """
    client_info()

    template = loader.get_template("sale.html")
    current = cache.get('shops')[int(key)]
    if request.method == 'POST':
        date_from = datetime.datetime.strptime(request.POST['date_from'], '%Y-%m-%d')
        date_to = datetime.datetime.strptime(request.POST['date_to'], '%Y-%m-%d')
    elif request.method == 'GET':
        date_from = datetime.datetime.strptime(DEF_DATE_FROM, '%Y-%m-%d')
        date_to = datetime.datetime.strptime(DEF_DATE_TO, '%Y-%m-%d')

    date_from_str = date_from.strftime('%Y-%m-%d')
    date_to_str = date_to.strftime('%Y-%m-%d')
    data = cache.get('sale:' + date_from_str + "/" + date_to_str)
    if data is None:
        turnover = dw.get_products_sale(shops=int(key), by='turnover', date_from=date_from,
                                        date_to=date_to, view_type="represent")
        qty = dw.get_products_sale(shops=int(key), by='qty', date_from=date_from,
                                   date_to=date_to, view_type="represent")
        # Because numpy.int64 "is not JSON serializable"
        # And Sorry :(
        products_numpy = list(qty.head())
        products_int = []
        for i in products_numpy:
            products_int.append(i.item())
        products_list = dw.get_product(products=products_int)['results']
        products = {}
        for i in products_list:
            products[i['product_id']] = i
        data = {}
        for i in products:
            data[i] = {
                'product': products[i],
                'turnover': turnover.at[date_to.strftime('%Y-%m-%d'), i] - turnover.at[
                    date_from.strftime('%Y-%m-%d'), i],
                'sale': qty.at[date_to.strftime('%Y-%m-%d'), i] - qty.at[date_from.strftime('%Y-%m-%d'), i],
            }
        cache.set('sale:' + date_from_str + "/" + date_to_str, data)

    context = {
        'name': current['name'],
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'data': data,
    }
    return HttpResponse(template.render(context, request))
