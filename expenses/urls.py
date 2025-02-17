from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
	path('', views.index, name='expenses'),
	path('add-expenses', views.add_expense, name="add-expenses"),
	path('filter-expenses', views.filter_expenses, name='filter_expenses'),
	path('edit-expenses/<int:id>', views.edit_expense, name="edit-expenses"),
	path('delete-expense/<int:id>', views.delete_expense, name="delete-expense"),
	path('search-expenses', csrf_exempt(views.search_expenses), name="search-expenses"),
	path('expense-category-summary', views.expense_category_sumary, name="expense-category-summary"),
	path('expense-summary', views.stastView, name='expense-summary'),

]