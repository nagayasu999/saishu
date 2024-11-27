from django.urls import path
from . import views

urlpatterns = [
    path('', views.node_cost, name='nodecost'),  # メインページ (Node Registration)
    path('manage_organization/', views.manage_organization, name='manage_organization'),  # 組織構造ページ
    path('edit_node/', views.edit_node, name='edit_node'),  # ノード編集
    path('calculate_costs/', views.calculate_costs, name='calculate_costs'),  # コスト計算 (AJAX対応)
    path('delete_node/', views.delete_node, name='delete_node'),  # ノード削除
]