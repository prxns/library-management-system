from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import StyledUserCreationForm
from .models import Book, BorrowRecord


def home(request):
    query = request.GET.get("q", "").strip()
    books = Book.objects.all().order_by("title")

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(category__icontains=query)
            | Q(isbn__icontains=query)
        )

    return render(
        request,
        "home.html",
        {
            "books": books,
            "query": query,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("home")
    else:
        form = StyledUserCreationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Logged out successfully.")
    return redirect("login")


@login_required
def dashboard(request):
    active_borrows = (
        BorrowRecord.objects.filter(user=request.user, is_returned=False)
        .select_related("book")
        .order_by("-issue_date")
    )

    history = (
        BorrowRecord.objects.filter(user=request.user, is_returned=True)
        .select_related("book")
        .order_by("-returned_at")
    )

    total_active = active_borrows.count()
    total_returned = history.count()
    total_fine_due = sum(b.current_fine for b in active_borrows)
    total_fine_paid = sum(b.fine_amount for b in history)

    return render(
        request,
        "dashboard.html",
        {
            "active_borrows": active_borrows,
            "history": history,
            "total_active": total_active,
            "total_returned": total_returned,
            "total_fine_due": total_fine_due,
            "total_fine_paid": total_fine_paid,
        },
    )


@login_required
def borrow_book(request, book_id):
    if request.method != "POST":
        return redirect("home")

    book = get_object_or_404(Book, pk=book_id)

    if book.available_copies <= 0:
        messages.error(request, "This book is currently unavailable.")
        return redirect("home")

    already_borrowed = BorrowRecord.objects.filter(
        user=request.user,
        book=book,
        is_returned=False,
    ).exists()

    if already_borrowed:
        messages.error(request, "You already borrowed this book and have not returned it yet.")
        return redirect("dashboard")

    BorrowRecord.objects.create(user=request.user, book=book)
    book.available_copies -= 1
    book.save(update_fields=["available_copies"])

    messages.success(request, f"You borrowed '{book.title}' successfully.")
    return redirect("dashboard")


@login_required
def return_book(request, borrow_id):
    if request.method != "POST":
        return redirect("dashboard")

    borrow = get_object_or_404(BorrowRecord, pk=borrow_id, user=request.user)

    if borrow.is_returned:
        messages.info(request, "This book has already been returned.")
        return redirect("dashboard")

    today = timezone.localdate()
    fine = borrow.calculate_fine(today)

    borrow.is_returned = True
    borrow.returned_at = today
    borrow.fine_amount = fine
    borrow.save(update_fields=["is_returned", "returned_at", "fine_amount"])

    book = borrow.book
    book.available_copies += 1
    book.save(update_fields=["available_copies"])

    if fine > 0:
        messages.warning(request, f"Book returned. Fine charged: ₹{fine}.")
    else:
        messages.success(request, "Book returned successfully. No fine charged.")

    return redirect("dashboard")