from django.contrib.auth.models import User
from django.db.models import QuerySet, Count, Q
from django.utils import timezone


def add_sound_effect_count_annotation(user: User, qs: QuerySet):
    month_ago = timezone.now() - timezone.timedelta(days=30)
    my_total_play_count = Count("play_history", filter=Q(play_history__played_by=user), distinct=False)
    my_30d_play_count = Count("play_history", filter=Q(play_history__played_by=user), distinct=False)
    total_play_count = Count("play_history", distinct=False)
    play_count_month = Count("play_history", filter=Q(play_history__played_at__gte=month_ago), distinct=False)
    return qs.annotate(my_total_play_count=my_total_play_count, my_30d_play_count=my_30d_play_count,
                       total_play_count=total_play_count, play_count_month=play_count_month)
