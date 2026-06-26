import os
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Video, CourseCategory, VideoPurchase
from .services import make_video_token, verify_video_token
from apps.users.models import Wallet, WalletTransaction


class CourseListView(ListView):
    model = Video
    template_name = 'videos/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        return Video.objects.published().filter(product_type='VIDEO').select_related('seller', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = CourseCategory.objects.filter(parent__isnull=True)
        return context


class CourseDetailView(DetailView):
    model = Video
    template_name = 'videos/course_detail.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.is_published or self.request.user.is_staff or obj.seller == self.request.user:
            return obj
        raise Http404('Mahsulot topilmadi yoki ko‘rish huquqiga ega emassiz.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.get_object()
        context['is_purchased'] = False
        context['in_wishlist'] = False
        if self.request.user.is_authenticated:
            context['is_purchased'] = VideoPurchase.objects.filter(
                user=self.request.user, product=video
            ).exists()
            from apps.marketplace.models import VideoWishlist
            context['in_wishlist'] = VideoWishlist.objects.filter(
                user=self.request.user, video=video
            ).exists()
        context['reviews'] = video.reviews.all()
        # In this project, lessons are represented by DigitalFile model
        context['lessons'] = video.files.all() 
        return context


class CourseWatchView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'videos/course_watch.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        has_access = (
            VideoPurchase.objects.filter(user=request.user, product=self.object).exists()
            or self.object.seller == request.user
            or request.user.is_staff
        )
        if not has_access:
            return redirect('videos:course_detail', slug=self.object.slug)

        token = make_video_token(request.user.id, str(self.object.id))
        context = self.get_context_data(object=self.object)
        context['stream_token'] = token
        context['hls_url'] = None
        if self.object.hls_root:
            context['hls_url'] = f"/courses/{self.object.slug}/stream/?token={token}"
        return self.render_to_response(context)


class MyCoursesView(LoginRequiredMixin, ListView):
    template_name = 'videos/my_courses.html'
    context_object_name = 'purchases'
    paginate_by = 12

    def get_queryset(self):
        return VideoPurchase.objects.filter(
            user=self.request.user
        ).select_related('product', 'product__seller').order_by('-purchased_at')


@login_required
def serve_hls_playlist(request, slug):
    video = get_object_or_404(Video, slug=slug)
    token = request.GET.get('token', '')
    data = verify_video_token(token)
    if not data or str(data.get('video_id')) != str(video.id):
        return HttpResponseForbidden("Token yaroqsiz yoki muddati tugagan.")

    has_access = (
        VideoPurchase.objects.filter(user=request.user, product=video).exists()
        or video.seller == request.user
        or request.user.is_staff
    )
    if not has_access:
        return HttpResponseForbidden("Kirish rad etildi.")

    if not video.hls_root:
        if video.preview_video:
            return FileResponse(video.preview_video.open('rb'), content_type='video/mp4')
        return HttpResponseForbidden("Video hali tayyor emas.")

    m3u8_path = os.path.join(settings.MEDIA_ROOT, video.hls_root, 'master.m3u8')
    if not os.path.exists(m3u8_path):
        return HttpResponseForbidden("Stream fayli topilmadi.")
    return FileResponse(open(m3u8_path, 'rb'), content_type='application/vnd.apple.mpegurl')


@login_required
def serve_hls_segment(request, slug, segment):
    video = get_object_or_404(Video, slug=slug)
    token = request.GET.get('token', '')
    data = verify_video_token(token)
    if not data:
        return HttpResponseForbidden("Token yaroqsiz.")

    segment_path = os.path.join(settings.MEDIA_ROOT, video.hls_root, segment)
    if not os.path.exists(segment_path):
        return HttpResponseForbidden("Segment topilmadi.")
    return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')


@login_required
@require_POST
def course_purchase(request, slug):
    video = get_object_or_404(Video, slug=slug)
    if not video.is_published and video.seller != request.user and not request.user.is_staff:
        messages.error(request, "Mahsulot hozirda sotuvga chiqmagan.")
        return redirect('core:dashboard')

    if VideoPurchase.objects.filter(user=request.user, product=video).exists():
        messages.info(request, "Siz ushbu kursni allaqachon sotib olgansiz.")
        return redirect('videos:course_watch', slug=video.slug)

    from apps.payments.wallet_services import WalletPurchaseService

    wants_json = (
        'application/json' in request.headers.get('Accept', '')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )

    def deliver():
        VideoPurchase.objects.create(
            user=request.user,
            product=video,
            amount=video.price,
            payment_status=VideoPurchase.PaymentStatus.PAID,
        )

    result = WalletPurchaseService.purchase(
        request.user,
        video.price,
        deliver,
        description=f"Kurs xaridi: {video.title}",
        reference=video.slug,
    )

    if wants_json:
        if result.get('success'):
            result['redirect_url'] = f'/videos/course/{video.slug}/watch/'
        return JsonResponse(result, status=200 if result.get('success') else 402)

    if result.get('success'):
        messages.success(request, f"Tabriklaymiz! {video.title} kursi muvaffaqiyatli sotib olindi.")
        return redirect('videos:course_watch', slug=video.slug)

    messages.error(request, result.get('message', "Balansingizda mablag' yetarli emas."))
    return redirect('payments:wallet')

