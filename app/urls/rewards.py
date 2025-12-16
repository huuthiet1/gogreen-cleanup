from django.urls import path
from app.views.rewards import redeem_rewards, my_reward_history

urlpatterns = [
    path("rewards/", redeem_rewards, name="redeem_rewards"),
    path("rewards/history/", my_reward_history, name="reward_history"),
]
