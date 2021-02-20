from django.http import HttpRequest
from django.shortcuts import redirect
from django.views.generic.base import View


class Home(View):

    def get(self, request: HttpRequest):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return redirect("login")
