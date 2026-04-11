from django.shortcuts import render, get_object_or_404
from .models import Account


def account_dashboard(request, order_id):
    account = get_object_or_404(Account, order_id=order_id)
    transactions = account.transactions.all().order_by('-created_at')

    return render(request, 'accounts/dashboard.html', {
        'account': account,
        'transactions': transactions
    })

from django.shortcuts import redirect
from .models import Account, Transaction


def add_transaction(request, order_id):
    account = Account.objects.get(order_id=order_id)

    if request.method == "POST":
        Transaction.objects.create(
            account=account,
            amount=request.POST.get("amount"),
            transaction_type=request.POST.get("type"),
            description=request.POST.get("desc"),
            created_by=request.user
        )

        account.save()  # 🔥 recalc
        return redirect('account_dashboard', order_id=order_id)
    
def accounts_list(request):
    from .models import Account
    accounts = Account.objects.select_related('order').all().order_by('-id')

    return render(request, 'accounts/list.html', {'accounts': accounts})
