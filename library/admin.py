from django.contrib import admin
from .models import Book, BorrowRecord


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "total_copies", "available_copies", "created_at")
    search_fields = ("title", "author", "category", "isbn")
    list_filter = ("category",)
    ordering = ("title",)


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "issue_date", "due_date", "returned_at", "is_returned", "fine_amount")
    search_fields = ("book__title", "user__username")
    list_filter = ("is_returned", "issue_date", "due_date")
    ordering = ("-issue_date",)
    date_hierarchy = "issue_date"