# Income and Expense Tracker API

This is a Django-based REST API for an **Income and Expense Tracker**. It allows users to manage their income, expenses, and categories while also providing functionalities for user authentication and profile management.

## Features

- **User Management**: Users can sign up, log in, log out, update their profile, and change their password.
- **Transactions**: Users can add, update, delete, and view income and expense transactions.
- **Categories**: Users can create, update, and delete categories for transactions.
- **Authentication**: The app uses **JWT (JSON Web Tokens)** for user authentication, allowing secure login and token-based access.

## API Endpoints

### User-related Endpoints

- **POST /api/users/signup/**: Create a new user account.
- **POST /api/users/login/**: Log in to the system and receive a JWT token.
- **POST /api/users/logout/**: Log out the user by invalidating the JWT token.
- **GET /api/users/**: Get details of the currently authenticated user.
- **PUT /api/users/**: Update the profile of the currently authenticated user.
- **POST /api/users/change-password/**: Change the user's password.
- **GET /api/users/monthly-report/**: Retrieve the monthly income and expense report.
- **POST /api/users/refresh/**: Refresh JWT token.

### Transaction-related Endpoints

- **GET /api/transactions/**: Get a list of all transactions for the currently authenticated user.
- **POST /api/transactions/**: Create a new transaction (income or expense).
- **PUT /api/transactions/{uuid}/**: Update a specific transaction by UUID.
- **DELETE /api/transactions/{uuid}/**: Delete a specific transaction by UUID.

### Category-related Endpoints

- **GET /api/categories/**: Get a list of all categories.
- **POST /api/categories/**: Create a new category for transactions.
- **PUT /api/categories/{uuid}/**: Update a specific category by UUID.
- **DELETE /api/categories/{uuid}/**: Delete a specific category by UUID.

## Installation

### Prerequisites

- Python 3.11
- Django 5.1 or higher
- Django REST Framework
- PostgreSQL (or any other database, but PostgreSQL is recommended)

### Steps to Set Up the Project

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/income-expense-tracker-api.git
   cd income-expense-tracker-api
