import datetime
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response

# Create your views here.
from django.template import RequestContext
from django.template import loader
from django.template.defaulttags import register

from dwapi import datawiz

# dw = datawiz.DW("test1@mail.com", "test2@cbe47a5c9466fe6df05f04264349f32b")

dw = None


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def sign(request):
    global dw
    dw = None

    if request.method == 'GET':
        context = {
            'login': "test1@mail.com",
            'password': "test2@cbe47a5c9466fe6df05f04264349f32b"
        }
        template = loader.get_template('sign.html')
        return render_to_response("sign.html", context, context_instance=RequestContext(request))
    elif request.method == 'POST':
        dw = datawiz.DW(request.POST['login'], request.POST['password'])
        # if passed
        return HttpResponseRedirect("/user.html")


def user(request):
    template = loader.get_template('user.html')
    info = dw.get_client_info()
    shops = dw.get_shops()
    if request.method == 'GET':
        context = {
            'user': info,
            'shops': shops,
        }
    return HttpResponse(template.render(context, request))


def shop(request, key):
    template = loader.get_template('shop.html')
    shops = dw.get_shops()
    context = {'id': key,
               'shop': shops[int(key)]}
    return HttpResponse(template.render(context, request))


def turnover(request, key):
    template = loader.get_template('turnover.html')
    current = dw.get_shops()[int(key)]
    if request.method == 'POST':
        date_from = datetime.datetime.strptime(request.POST['date_from'], '%Y-%m-%d')
        date_to = datetime.datetime.strptime(request.POST['date_to'], '%Y-%m-%d')
    else:
        date_from = datetime.datetime.strptime(DEF_DATE_FROM, '%Y-%m-%d')
        date_to = datetime.datetime.strptime(DEF_DATE_TO, '%Y-%m-%d')

    turn = dw.get_categories_sale(categories=['sum'], shops=int(key), by='turnover',
                                  date_from=date_from, date_to=date_to, view_type="represent")
    product = dw.get_categories_sale(categories=['sum'], shops=int(key), by='qty',
                                     date_from=date_from, date_to=date_to, view_type="represent")
    receipts = dw.get_categories_sale(categories=['sum'], shops=int(key), by='receipts_qty',
                                      date_from=date_from, date_to=date_to, view_type="represent")
    # profit = dw.get_categories_sale(categories=['sum'], shops=int(key), by='profit', date_from=date_from, date_to=date_to, view_type="represent")

    data_from_str = date_from.strftime('%Y-%m-%d')
    data_to_str = date_to.strftime('%Y-%m-%d')
    data = {}
    data['from'] = {
        'turnover': turn.at[data_from_str, "sum"],
        'products': product.at[data_from_str, "sum"],
        'receipts': receipts.at[data_from_str, "sum"],
        'average_receipt': turn.at[data_from_str, "sum"] / receipts.at[data_from_str, "sum"],
    }
    data['to'] = {
        'turnover': turn.at[data_to_str, "sum"],
        'products': product.at[data_to_str, "sum"],
        'receipts': receipts.at[data_to_str, "sum"],
        'average_receipt': turn.at[data_to_str, "sum"] / receipts.at[data_to_str, "sum"],
    }
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

    context = {
        'name': current['name'],
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'data': data,
    }
    return HttpResponse(template.render(context, request))


DEF_DATE_FROM = "2015-11-17"
DEF_DATE_TO = "2015-11-18"


def sale(request, key):
    template = loader.get_template("sale.html")
    shop = dw.get_shops()[int(key)]
    if request.method == 'POST':
        date_from = datetime.datetime.strptime(request.POST['date_from'], '%Y-%m-%d')
        date_to = datetime.datetime.strptime(request.POST['date_to'], '%Y-%m-%d')
    else:
        date_from = datetime.datetime.strptime(DEF_DATE_FROM, '%Y-%m-%d')
        date_to = datetime.datetime.strptime(DEF_DATE_TO, '%Y-%m-%d')

    turnover = dw.get_products_sale(shops=int(key), by='turnover', date_from=date_from,
                                    date_to=date_to, view_type="represent")
    sale = dw.get_products_sale(shops=int(key), by='qty', date_from=date_from,
                                date_to=date_to, view_type="represent")
    tmp = list(sale.head())
    # products = dw.get_product(product=tmp)
    # name!!!
    data = {}
    for i in sale:
        data[i] = {
            'name': i,
            'turnover': turnover.at[date_to.strftime('%Y-%m-%d'), i] - turnover.at[date_from.strftime('%Y-%m-%d'), i],
            'sale': turnover.at[date_to.strftime('%Y-%m-%d'), i] - turnover.at[date_from.strftime('%Y-%m-%d'), i],
        }
    context = {
        'name': shop['name'],
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'data': data,
    }
    return HttpResponse(template.render(context, request))
