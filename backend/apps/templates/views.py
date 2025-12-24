from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Template, TemplateStatus, TemplateSource
from .serializers import TemplateSerializer, TemplateCreateSerializer
from .services import (
    MetaWhatsAppError,
    refresh_one_template_status_from_meta,
    submit_local_template_to_meta,
)


def ping(request):
    return JsonResponse({"status": "ok", "app": "templates"})


class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all().order_by("-updated_at")
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "external_id", "group_key"]
    ordering_fields = ["updated_at", "created_at", "name", "status"]

    def get_serializer_class(self):
        if self.action == "create":
            return TemplateCreateSerializer
        return TemplateSerializer

    def create(self, request, *args, **kwargs):
        """
        Create LOCAL draft.
        """
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # ✅ IMPORTANT: Your code uses DRAFT status, not PENDING
        obj = ser.save(status=TemplateStatus.DRAFT, source=TemplateSource.LOCAL)
        return Response(TemplateSerializer(obj).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        Draft-only delete rule (safe):
          - Only LOCAL templates
          - Only DRAFT status
          - Must NOT be linked to Meta yet (external_id is null)
        """
        tpl: Template = self.get_object()

        if tpl.source != TemplateSource.LOCAL:
            return Response(
                {"detail": "Only LOCAL templates can be deleted.", "source": tpl.source},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if tpl.status != TemplateStatus.DRAFT:
            return Response(
                {"detail": "Only DRAFT templates can be deleted.", "status": tpl.status},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if tpl.external_id:
            return Response(
                {"detail": "This template is already linked to Meta and cannot be deleted.", "external_id": tpl.external_id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tpl.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """
        Submit a local draft to Meta.
        """
        tpl: Template = self.get_object()

        if tpl.status != TemplateStatus.DRAFT:
            return Response(
                {"detail": "Only DRAFT templates can be submitted.", "status": tpl.status},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tpl = submit_local_template_to_meta(tpl)
        except MetaWhatsAppError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(TemplateSerializer(tpl).data, status=200)

    @action(detail=True, methods=["post"])
    def sync_status(self, request, pk=None):
        """
        Refresh status from Meta (by name+language).
        """
        tpl: Template = self.get_object()

        try:
            tpl = refresh_one_template_status_from_meta(tpl)
        except MetaWhatsAppError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(TemplateSerializer(tpl).data, status=200)
