from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from ..models import Reward, RewardRedeem

@login_required
def redeem_rewards(request):
    rewards = Reward.objects.all()

    if request.method == "POST":
        reward = get_object_or_404(Reward, id=request.POST['reward_id'])
        qty = int(request.POST.get('quantity', 1))
        total = reward.required_points * qty

        with transaction.atomic():
            reward = Reward.objects.select_for_update().get(id=reward.id)
            user = request.user

            if user.points < total or reward.stock < qty:
                messages.error(request, "Không đủ điểm hoặc quà.")
                return redirect("redeem_rewards")

            user.points -= total
            reward.stock -= qty
            user.save()
            reward.save()

            RewardRedeem.objects.create(
                user=user,
                reward=reward,
                quantity=qty,
                points_spent=total,
                status='approved'
            )

        messages.success(request, "Đổi quà thành công.")
        return redirect("redeem_rewards")

    return render(request, "app/redeem_rewards.html", {"rewards": rewards})
