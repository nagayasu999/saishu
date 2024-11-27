from django.db import models

class Node(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Title"  # 管理画面でのラベル名
    )
    weight = models.DecimalField(
        max_digits=4,  # 最大桁数（例: 10.00）
        decimal_places=1,  # 小数点以下1桁
        default=1.0,  # デフォルト値
        verbose_name="Weight"
    )
    parent = models.ForeignKey(
        'self',  # 自己参照
        null=True,  # 親ノードが設定されていない場合を許容
        blank=True,  # 空白を許容
        on_delete=models.SET_NULL,  # 親ノード削除時にNULLに設定
        related_name="children",  # 子ノードへの逆参照名
        verbose_name="Parent Node"
    )
    cost = models.FloatField(
        default=0.0,  # デフォルト値
        verbose_name="Cost"
    )
    quantity = models.PositiveIntegerField(
        default=1,  # デフォルト値
        verbose_name="Quantity"  # 管理画面での表示名
    )

    def __str__(self):
        return self.title  # オブジェクトの文字列表現
