from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.utils import timezone

from .models import (
    WhatsappBusinessAccount,
    WhatsappPhoneNumber,
    WhatsappContact,
    WhatsappConversation,
    WhatsappQrCode,
    WhatsappConnection,
)
from .serializers import (
    WhatsappBusinessAccountSerializer,
    WhatsappPhoneNumberSerializer,
    WhatsappContactSerializer,
    WhatsappConversationSerializer,
    WhatsappQrCodeSerializer,
    WhatsappConnectionSerializer,
)
from .services import WhatsappNumberService, WhatsappQrService
from .services_meta import MetaGraph


def get_workspace_id(request):
    ws = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace_id")
    if not ws:
        return None
    return ws


class WhatsappBusinessAccountViewSet(viewsets.ModelViewSet):
    queryset = WhatsappBusinessAccount.objects.all()
    serializer_class = WhatsappBusinessAccountSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def sync_from_meta(self, request):
        """
        Sync WABAs from Meta into local DB (admin operation).
        NOTE: This uses global META_ACCESS_TOKEN in settings (services_meta.py).
        Later, replace with workspace connection token.
        """
        ws = request.headers.get("X-Workspace-Id")
        items = MetaGraph.list_wabas(workspace_id=ws)


        saved = []
        now = timezone.now()

        for it in items:
            obj, _ = WhatsappBusinessAccount.objects.update_or_create(
                id=it["id"],  # ✅ model pk is 'id'
                defaults={
                    "name": it.get("name", "") or "",
                    "is_connected": True,
                    "last_synced_at": now,
                    "meta_raw": it,
                },
            )
            saved.append(obj)

        return Response(WhatsappBusinessAccountSerializer(saved, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def sync_phone_numbers(self, request, pk=None):
        """
        Sync phone numbers for THIS WABA from Meta into local DB.
        """
        waba = self.get_object()
        ws = request.headers.get("X-Workspace-Id")
        items = MetaGraph.list_phone_numbers(waba.id, workspace_id=ws)
  # ✅ waba pk is id

        saved = []
        now = timezone.now()

        for it in items:
            obj, _ = WhatsappPhoneNumber.objects.update_or_create(
                id=it["id"],  # ✅ model pk is 'id'
                defaults={
                    "waba": waba,
                    "display_name": it.get("verified_name") or it.get("display_phone_number") or "",
                    "e164_number": it.get("display_phone_number") or "",
                    "last_synced_at": now,
                    "meta_raw": it,
                },
            )
            saved.append(obj)

        return Response(WhatsappPhoneNumberSerializer(saved, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def sync_qr_codes(self, request, pk=None):
        waba = self.get_object()
        WhatsappQrService.sync_qrs(waba)
        qrs = waba.qr_codes.all()
        return Response(WhatsappQrCodeSerializer(qrs, many=True).data)


class WhatsappConnectionViewSet(viewsets.ModelViewSet):
    """
    Workspace-scoped connection: token + chosen WABA + phone number.
    This is the actual "integration" object.
    """
    serializer_class = WhatsappConnectionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        ws = get_workspace_id(self.request)
        qs = WhatsappConnection.objects.select_related("waba", "phone_number", "workspace").all()
        if ws:
            qs = qs.filter(workspace_id=ws)
        return qs

    def create(self, request, *args, **kwargs):
        ws = get_workspace_id(request)
        if not ws:
            return Response({"detail": "X-Workspace-Id header is required"}, status=status.HTTP_400_BAD_REQUEST)

        waba_id = request.data.get("waba_id")
        phone_number_id = request.data.get("phone_number_id")
        access_token = request.data.get("access_token")
        verify_token = request.data.get("verify_token")

        if not all([waba_id, phone_number_id, access_token, verify_token]):
            return Response(
                {"detail": "waba_id, phone_number_id, access_token, verify_token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        waba = WhatsappBusinessAccount.objects.filter(id=waba_id).first()
        phone = WhatsappPhoneNumber.objects.filter(id=phone_number_id).first()

        if not waba:
            return Response({"detail": "Invalid waba_id"}, status=status.HTTP_400_BAD_REQUEST)
        if not phone:
            return Response({"detail": "Invalid phone_number_id"}, status=status.HTTP_400_BAD_REQUEST)
        if phone.waba_id != waba.id:
            return Response({"detail": "phone_number_id does not belong to waba_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Deactivate existing active connection for workspace (MVP rule)
        WhatsappConnection.objects.filter(workspace_id=ws, is_active=True).update(is_active=False)

        conn = WhatsappConnection.objects.create(
            workspace_id=ws,
            waba=waba,
            phone_number=phone,
            access_token=access_token,
            verify_token=verify_token,
            token_expires_at=request.data.get("token_expires_at"),
            meta_user_id=request.data.get("meta_user_id", "") or "",
            scopes=request.data.get("scopes", []) or [],
            is_active=True,
        )

        return Response(WhatsappConnectionSerializer(conn).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def active(self, request):
        ws = get_workspace_id(request)
        if not ws:
            return Response({"detail": "X-Workspace-Id header is required"}, status=status.HTTP_400_BAD_REQUEST)

        conn = (
            WhatsappConnection.objects.select_related("waba", "phone_number")
            .filter(workspace_id=ws, is_active=True)
            .first()
        )
        if not conn:
            return Response({"connected": False, "connection": None})

        return Response({"connected": True, "connection": WhatsappConnectionSerializer(conn).data})

    @action(detail=False, methods=["post"])
    def disconnect(self, request):
        ws = get_workspace_id(request)
        if not ws:
            return Response({"detail": "X-Workspace-Id header is required"}, status=status.HTTP_400_BAD_REQUEST)

        WhatsappConnection.objects.filter(workspace_id=ws, is_active=True).update(is_active=False)
        return Response({"ok": True})


class WhatsappPhoneNumberViewSet(viewsets.ModelViewSet):
    queryset = WhatsappPhoneNumber.objects.select_related("waba")
    serializer_class = WhatsappPhoneNumberSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        phone = self.get_object()
        pin = request.data.get("pin")
        if not pin:
            return Response({"detail": "PIN required"}, status=status.HTTP_400_BAD_REQUEST)
        ws = request.headers.get("X-Workspace-Id")
        data = WhatsappNumberService.register_number(phone, pin, workspace_id=ws)

        return Response(data)

    @action(detail=True, methods=["post"])
    def enable_two_step(self, request, pk=None):
        phone = self.get_object()
        pin = request.data.get("pin")
        if not pin:
            return Response({"detail": "PIN required"}, status=status.HTTP_400_BAD_REQUEST)
        ws = request.headers.get("X-Workspace-Id")
        data = WhatsappNumberService.enable_two_step(phone, pin, workspace_id=ws)
        return Response(data)

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        phone = self.get_object()
        ws = request.headers.get("X-Workspace-Id")
        data = WhatsappNumberService.get_profile(phone, workspace_id=ws)
        return Response(data)

    @action(detail=True, methods=["post"])
    def update_profile(self, request, pk=None):
        phone = self.get_object()
        fields = request.data
        ws = request.headers.get("X-Workspace-Id")
        data = WhatsappNumberService.update_profile(phone, fields, workspace_id=ws)
        return Response(data)


class WhatsappContactViewSet(viewsets.ModelViewSet):
    serializer_class = WhatsappContactSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        ws = get_workspace_id(self.request)
        qs = WhatsappContact.objects.all()
        if ws:
            qs = qs.filter(workspace_id=ws)
        return qs

    def perform_create(self, serializer):
        ws = get_workspace_id(self.request)
        if not ws:
            raise ValueError("X-Workspace-Id header is required")
        serializer.save(workspace_id=ws)


class WhatsappConversationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WhatsappConversationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        ws = get_workspace_id(self.request)
        qs = WhatsappConversation.objects.select_related("contact", "phone_number")
        if ws:
            qs = qs.filter(workspace_id=ws)
        return qs


class WhatsappQrCodeViewSet(viewsets.ModelViewSet):
    serializer_class = WhatsappQrCodeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        ws = get_workspace_id(self.request)
        qs = WhatsappQrCode.objects.select_related("waba", "phone_number")
        if ws:
            qs = qs.filter(workspace_id=ws)
        return qs

    @action(detail=False, methods=["post"])
    def create_for_number(self, request):
        ws = get_workspace_id(request)

        waba_id = request.data.get("waba_id")
        phone_id = request.data.get("phone_number_id")
        name = request.data.get("name")
        message = request.data.get("message", "")

        if not all([waba_id, phone_id, name]):
            return Response(
                {"detail": "waba_id, phone_number_id, name required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        waba = WhatsappBusinessAccount.objects.get(pk=waba_id)
        phone = WhatsappPhoneNumber.objects.get(pk=phone_id)

        qr = WhatsappQrService.create_qr(waba, phone, name, message)

        # If your model has workspace FK (I recommended nullable), set it:
        if ws:
            qr.workspace_id = ws
            qr.save(update_fields=["workspace"])

        return Response(WhatsappQrCodeSerializer(qr).data, status=201)
