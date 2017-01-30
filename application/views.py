from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response

# Create your views here.
from django.template import RequestContext
from django.template import loader
from django.template.defaulttags import register


from dwapi import datawiz

#dw = datawiz.DW("test1@mail.com", "test2@cbe47a5c9466fe6df05f04264349f32b")

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

    if request.method == 'GET':
        context = {
            'user': dw.get_client_info()
        }
    return HttpResponse(template.render(context, request))


def shop(request, key):
    template = loader.get_template('shop.html')
    context = {'id': key,
               'shop': dw.get_shops()[int(key)]}
    return HttpResponse(template.render(context, request))


def turnover(request):
    template = loader.get_template('turnover.html')
    context = {

    }
    return HttpResponse(template.render(context, request))


def sale(request):
    template = loader.get_template("sale.html")
    context = {

    }

    return HttpResponse(template.render(context, request))
