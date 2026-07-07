/**
 * Extract the Django CSRF token from the browser cookie.
 * Used by SPA forms that POST to Django endpoints.
 */
export function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}
