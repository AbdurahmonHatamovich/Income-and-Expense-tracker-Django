from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from expenses.models import Expense
from .models import Source, UserIncome
from userpreferences.models import UserPreference
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator
import json
import datetime
from django.http import JsonResponse


def search_incomes(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')

        incomes = UserIncome.objects.filter(
            amount__istartswith=search_str, owner=request.user) | UserIncome.objects.filter(
            date__istartswith=search_str, owner=request.user) | UserIncome.objects.filter(
            description__icontains=search_str, owner=request.user) | UserIncome.objects.filter(
            source__icontains=search_str, owner=request.user)
        data = incomes.values()
        return JsonResponse(list(data), safe=False)


def balance_view(request):
    total_incomes = UserIncome.objects.filter(owner=request.user).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    total_expenses = Expense.objects.filter(owner=request.user).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    remaining_balance = total_incomes - total_expenses

    context = {
        'total_incomes': total_incomes,
        'total_expenses': total_expenses,
        'remaining_balance': remaining_balance
    }

    return render(request, 'income/balance.html', context)


@login_required(login_url='/authentication/login')
def index(request):
    sources = Source.objects.all()
    incomes = UserIncome.objects.filter(owner=request.user).order_by('-date')

    exists = UserPreference.objects.filter(user=request.user).exists()
    preferences = {}
    if exists:
        preferences = UserPreference.objects.get(user=request.user)
    else:
        preferences = {'currency': 'None'}

    paginator = Paginator(incomes, 6)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)

    context = {
        'userincomes': incomes,
        'preferences': preferences,
        'page_obj': page_obj,
    }

    return render(request, 'income/index.html', context)


@login_required(login_url='/authentication/login')
def add_income(request):
    sources = Source.objects.all()

    if request.method == 'GET':
        context = {
            'sources': sources
        }
        return render(request, 'income/add_income.html', context)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        income_date = request.POST.get('income_date')
        source = request.POST.get('source')

        context = {
            'sources': sources,
            'values': request.POST
        }

        # Ensure all required fields are present
        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/add_income.html', context)
        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'income/add_income.html', context)
        if not income_date:
            messages.error(request, 'Date is required')
            return render(request, 'income/add_income.html', context)
        if not source:
            messages.error(request, 'Source is required')
            return render(request, 'income/add_income.html', context)

        # Create the UserIncome object
        UserIncome.objects.create(
            amount=amount,
            date=income_date,
            description=description,
            owner=request.user,
            source=source
        )
        messages.success(request, 'Income added successfully')
        return redirect('incomes')



def edit_income(request, id):
    income = UserIncome.objects.get(pk=id)
    sources = Source.objects.all()
    context = {
        'income': income,
        'sources': sources
    }
    if request.method == 'GET':
        return render(request, 'income/edit_income.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        income_date = request.POST['income_date']
        context = {
            'sources': sources,
            'income': income,
            'values': request.POST
        }
        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/edit_income.html', context)
        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'income/edit_income.html', context)
        if not income_date:
            messages.error(request, 'Date is required')
            return render(request, 'income/edit_income.html', context)
        source = request.POST['source']
        income.owner = request.user
        income.amount = amount
        income.date = income_date
        income.description = description
        income.source = source
        income.save()

        messages.success(request, 'Income edited successfully')
        return redirect('incomes')


def delete_income(request, id):
    income = UserIncome.objects.get(pk=id)
    income.delete()
    messages.success(request, 'Income deleted successfully')
    return redirect('incomes')


def income_source_sumary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date - datetime.timedelta(days=150)
    incomes = UserIncome.objects.filter(
        owner=request.user,
        date__gte=six_months_ago,
        date__lte=todays_date)

    finalrep = {
    }

    def get_source(income):
        return income.source

    source_list = list(set(map(get_source, incomes)))

    def get_income_source_amount(source):
        amount = 0
        filtered_by_category = incomes.filter(source=source)
        for item in filtered_by_category:
            amount += item.amount
        return amount

    for y in source_list:
        finalrep[y] = get_income_source_amount(y)

    return JsonResponse({'income_source_data': finalrep}, safe=False)


def stastView(request):
    return render(request, 'income/stats.html')