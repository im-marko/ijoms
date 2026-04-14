from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Job, JobCategory, JobStatusHistory


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'sla_hours', 'description', 'is_active']


class JobStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_detail = UserSerializer(source='changed_by', read_only=True)

    class Meta:
        model = JobStatusHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'changed_by_detail', 'notes', 'created_at']


class JobListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    is_sla_breached = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'reference_number', 'title', 'category', 'category_name',
            'priority', 'status', 'assigned_to', 'assigned_to_name',
            'created_by', 'created_by_name', 'customer_name',
            'sla_deadline', 'is_sla_breached', 'created_at', 'updated_at',
        ]

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_is_sla_breached(self, obj):
        if obj.sla_deadline and obj.status != Job.Status.CLOSED:
            from django.utils import timezone
            return timezone.now() > obj.sla_deadline
        return False


class JobDetailSerializer(serializers.ModelSerializer):
    category_detail = JobCategorySerializer(source='category', read_only=True)
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    status_history = JobStatusHistorySerializer(many=True, read_only=True)
    is_sla_breached = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'reference_number', 'title', 'description',
            'category', 'category_detail', 'priority', 'status',
            'assigned_to', 'assigned_to_detail',
            'created_by', 'created_by_detail',
            'customer_name', 'customer_contact', 'customer_email',
            'sla_deadline', 'is_sla_breached', 'resolution_notes',
            'created_at', 'updated_at', 'closed_at', 'status_history',
        ]
        read_only_fields = ['reference_number', 'created_by', 'closed_at']

    def get_is_sla_breached(self, obj):
        if obj.sla_deadline and obj.status != Job.Status.CLOSED:
            from django.utils import timezone
            return timezone.now() > obj.sla_deadline
        return False


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'category', 'priority',
            'assigned_to', 'customer_name', 'customer_contact', 'customer_email',
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        job = Job.objects.create(**validated_data)
        if job.assigned_to:
            job.status = Job.Status.ASSIGNED
            job.save()
            JobStatusHistory.objects.create(
                job=job, from_status=Job.Status.OPEN, to_status=Job.Status.ASSIGNED,
                changed_by=self.context['request'].user, notes='Initial assignment',
            )
        return job


class JobStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Job.Status.choices)
    notes = serializers.CharField(required=False, default='')
    assigned_to = serializers.IntegerField(required=False, allow_null=True)
