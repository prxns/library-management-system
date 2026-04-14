from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True)
    cover_url = models.URLField(blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.available_copies > 0


class BorrowRecord(models.Model):
    FINE_PER_DAY = 10

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrow_records",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrow_records",
    )
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    returned_at = models.DateField(blank=True, null=True)
    fine_amount = models.PositiveIntegerField(default=0)
    is_returned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

    def save(self, *args, **kwargs):
        if self._state.adding and not self.due_date:
            self.due_date = timezone.localdate() + timedelta(days=7)
        super().save(*args, **kwargs)

    def calculate_fine(self, current_date=None):
        if self.is_returned:
            return self.fine_amount

        if current_date is None:
            current_date = timezone.localdate()

        if self.due_date and current_date > self.due_date:
            days_late = (current_date - self.due_date).days
            return days_late * self.FINE_PER_DAY

        return 0

    @property
    def current_fine(self):
        return self.calculate_fine()

    @property
    def status_label(self):
        if self.is_returned:
            return "Returned"
        if self.current_fine > 0:
            return "Overdue"
        return "Issued"