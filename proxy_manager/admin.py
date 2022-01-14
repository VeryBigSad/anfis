from django.contrib import admin

from proxy_manager.models import Proxy


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    # TODO: todo
    pass


