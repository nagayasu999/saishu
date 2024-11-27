from django import forms
from .models import Node

class NodeForm(forms.ModelForm):
    # 重みのフィールド設定
    weight = forms.DecimalField(
        min_value=1.0,  # 最小値
        max_value=10.0,  # 最大値
        decimal_places=1,  # 小数点以下1桁
        max_digits=4,  # 最大桁数
        label="Weight",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',  # Bootstrap用のクラス
            'step': 0.1,  # ステップを指定
            'placeholder': 'Enter weight (1.0 - 10.0)'  # プレースホルダー
        })
    )

    # 数量のフィールド設定
    quantity = forms.IntegerField(
        required=False,  # 必須ではない
        initial=1,  # デフォルト値
        min_value=1,  # 最小値
        max_value=100,  # 最大値
        label="Quantity",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',  # Bootstrap用のクラス
            'placeholder': 'Enter quantity (default: 1)'  # プレースホルダー
        })
    )

    class Meta:
        model = Node
        fields = ['title', 'weight', 'quantity', 'parent']  # 必要なフィールドを指定
        labels = {
            'title': 'Node Title',  # タイトルフィールドのラベル
            'parent': 'Parent Node'  # 親ノードのラベル
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',  # Bootstrap用のクラス
                'placeholder': 'Enter node title'  # プレースホルダー
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control'  # Bootstrap用のクラス
            }),
        }
