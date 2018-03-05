from rest_framework import serializers

from baseapi import models



class CouponRecordSerializers(serializers.Serializer):
    coupon = serializers.CharField()
    number = serializers.IntegerField()
    status = serializers.CharField()
    object_id = serializers.IntegerField(source="coupon.object_id")

    class Meta:
        models = models.CouponRecord

