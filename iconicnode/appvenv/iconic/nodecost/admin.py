from django.contrib import admin
from .models import Node

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'weight', 'parent')  # 一覧で表示するフィールド
    search_fields = ('title',)  # 検索可能なフィールド
    list_filter = ('parent',)  # フィルタリングオプション
