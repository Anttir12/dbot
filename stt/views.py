from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.shortcuts import render
from django.views import View


class SttFeed(LoginRequiredMixin, View):

    def get(self, request: HttpRequest, stt_token: str):
        return render(request, "stt_feed.html", {
            'stt_token': stt_token
        })
