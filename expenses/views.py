from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Category, Expense
from userpreferences.models import UserPreference
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
import datetime


def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')

        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user)
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def filter_expenses(request):
    today = datetime.date.today()
    filter_type = request.GET.get('filter', 'daily')

    if filter_type == 'daily':
        start_date = today
    elif filter_type == 'monthly':
        start_date = today.replace(day=1)
    elif filter_type == 'yearly':
        start_date = today.replace(month=1, day=1)
    else:
        start_date = today

    expenses = Expense.objects.filter(owner=request.user, date__gte=start_date).order_by('-date')
    context = {
        'expenses': expenses,
        'filter_type': filter_type,
    }

    return render(request, 'expenses/filter_expenses.html', context)


@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=request.user).order_by('-date')

    exists = UserPreference.objects.filter(user=request.user).exists()
    preferences = {}
    if exists:
        preferences = UserPreference.objects.get(user=request.user)
    else:
        preferences = {'currency': 'None'}

    paginator = Paginator(expenses, 6)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)

    context = {
        'expenses': expenses,
        'preferences': preferences,
        'page_obj': page_obj,
    }

    return render(request, 'expenses/index.html', context)


def add_expense(request):
    categories = Category.objects.all()

    if request.method == 'GET':
        context = {
            'categories': categories
        }
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        expense_date = request.POST['expense_date']
        context = {
            'categories': categories,
            'values': request.POST
        }
        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)
        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/add_expense.html', context)
        if not expense_date:
            messages.error(request, 'Date is required')
            return render(request, 'expenses/add_expense.html', context)

        category = request.POST['category']

        Expense.objects.create(amount=amount, date=expense_date, description=description, owner=request.user,
                               category=category)
        messages.success(request, 'Expense added successfully')
        return redirect('expenses')


def edit_expense(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'categories': categories
    }
    if request.method == 'GET':
        return render(request, 'expenses/edit_expense.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        expense_date = request.POST['expense_date']

        context = {
            'categories': categories,
            'expense': expense,
            'values': request.POST
        }
        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit_expense.html', context)
        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/edit_expense.html', context)
        if not expense_date:
            messages.error(request, 'Date is required')
            return render(request, 'expenses/add_expense', context)
        category = request.POST['category']
        expense.owner = request.user
        expense.amount = amount
        expense.date = expense_date
        expense.description = description
        expense.category = category
        expense.save()

        messages.success(request, 'Expense edited successfully')
        return redirect('expenses')


def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense deleted successfully')
    return redirect('expenses')


def expense_category_sumary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date - datetime.timedelta(days=150)
    expenses = Expense.objects.filter(
        owner=request.user,
        date__gte=six_months_ago,
        date__lte=todays_date)

    finalrep = {

    }

    def get_category(expense):
        return expense.category

    category_list = list(set(map(get_category, expenses)))

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category=category)
        for item in filtered_by_category:
            amount += item.amount
        return amount

    for y in category_list:
        finalrep[y] = get_expense_category_amount(y)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)


def stastView(request):
    return render(request, 'expenses/stats.html')

