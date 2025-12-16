from django.urls import path
from app.views.events import (
    event_list, my_events, event_detail,
    toggle_event_registration, generate_event_otp,
    checkin_via_otp
)
from app.views.admin import quick_register_event

urlpatterns = [
    path("events/", event_list, name="cart"),
    path("my-events/", my_events, name="checkout"),

    path("event/<int:event_id>/", event_detail, name="event_detail"),
    path("event/<int:event_id>/toggle/", toggle_event_registration, name="toggle_event_registration"),
    path("event/<int:event_id>/quick-toggle/", quick_register_event, name="quick_register"),

    path("event/<int:event_id>/generate-otp/", generate_event_otp, name="generate_event_otp"),
    path("checkin/", checkin_via_otp, name="checkin_via_otp"),
]
