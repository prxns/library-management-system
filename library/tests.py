from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Book, BorrowRecord


class LibraryFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="demo",
            password="demo12345",
            email="demo@example.com",
        )
        self.book = Book.objects.create(
            title="Django Basics",
            author="John Doe",
            category="Technology",
            isbn="1234567890",
            total_copies=2,
            available_copies=2,
        )

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_search_works(self):
        response = self.client.get(reverse("home"), {"q": "Django"})
        self.assertContains(response, "Django Basics")

    def test_borrow_and_return_flow(self):
        self.client.login(username="demo", password="demo12345")

        borrow_response = self.client.post(reverse("borrow_book", args=[self.book.id]))
        self.assertEqual(borrow_response.status_code, 302)

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)
        self.assertEqual(BorrowRecord.objects.count(), 1)

        borrow = BorrowRecord.objects.first()
        return_response = self.client.post(reverse("return_book", args=[borrow.id]))
        self.assertEqual(return_response.status_code, 302)

        self.book.refresh_from_db()
        borrow.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)
        self.assertTrue(borrow.is_returned)