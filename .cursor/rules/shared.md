---
description: 
globs: 
alwaysApply: true
---
# AI Rules for {app-name}

{project-description}

## Tech Stack

- htmx
- tailwind
- Django
- PostgreSQL
- nginx

## Project Structure

When introducing changes to the project, always follow the Django preferred directory structure 

## Coding practices

### Guidelines for clean code

- Use feedback from linters to improve the code when making changes.
- Prioritize error handling and edge cases.
- Handle errors and edge cases at the beginning of functions.
- Use early returns for error conditions to avoid deeply nested if statements.
- Place the happy path last in the function for improved readability.
- Avoid unnecessary else statements; use if-return pattern instead.
- Use guard clauses to handle preconditions and invalid states early.
- Implement proper error logging and user-friendly error messages.
- Consider using custom error types or error factories for consistent error handling.