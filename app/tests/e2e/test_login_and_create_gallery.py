"""
E2E test: login and create gallery (Playwright + pytest-django live server).

Run:
  pytest app/tests/e2e/test_login_and_create_gallery.py -m e2e -v
  playwright install chromium   # once, to install browser
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db
def test_login_and_create_gallery(
    page: Page,
    live_server,
    e2e_login_credentials,
):
    """
    Log in via the login page, go to create gallery, submit form,
    and assert the new gallery appears on the gallery list.
    """
    base_url = live_server.url
    email, password = e2e_login_credentials

    # --- Login ---
    page.goto(f"{base_url}/accounts/login/")
    expect(page.get_by_role("heading", name="Sign In")).to_be_visible()
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in").click()

    # After login we should land on gallery list (or redirect to next)
    page.wait_for_url(f"{base_url}/**", wait_until="networkidle")
    expect(page).not_to_have_url(f"{base_url}/accounts/login/")

    # --- Create gallery page ---
    page.goto(f"{base_url}/galleries/create/")
    expect(page.get_by_role("heading", name="Create New Gallery")).to_be_visible()

    # --- Fill and submit create gallery form ---
    gallery_name = "E2E Test Gallery"
    gallery_description = "Created by Playwright e2e test"
    page.get_by_label("Gallery Name *").fill(gallery_name)
    page.get_by_label("Description").fill(gallery_description)
    page.get_by_label("Gallery Type").select_option("private")
    page.get_by_role("button", name="Create Gallery").click()

    # --- Assert redirect to list and gallery visible ---
    page.wait_for_url(f"{base_url}/**", wait_until="networkidle")
    expect(page).to_have_url(f"{base_url}/galleries/1/")
    expect(page.get_by_role("link", name="My Galleries")).to_be_visible()
    expect(page.get_by_role("heading", name=gallery_name)).to_be_visible()
