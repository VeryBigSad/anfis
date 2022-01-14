from __future__ import annotations

from django.db import models
from django.utils import timezone
from typing import List

from tgbot.models import User
from utils.models import CreateTracker, CreateUpdateTracker


class Proxy(CreateTracker):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_public = models.BooleanField(default=False)

    operation_count = models.IntegerField(default=0)

    proxy_scheme = models.CharField(max_length=10)
    proxy_url = models.CharField(max_length=200)
    last_checked_at = models.DateTimeField(default=timezone.now())
    does_work = models.BooleanField(default=True)
    request_count_from_last_check = models.IntegerField(default=0)

    @classmethod
    def get_valid_proxy_list(cls, user_id: int) -> List[Proxy]:
        user_proxies = cls.objects.filter(
            does_work=True,
            owner=User.get_user_by_username_or_user_id(user_id),
        )
        if user_proxies.exists():
            return list(user_proxies)
        return list(cls.objects.filter(does_work=True, owner=None))



