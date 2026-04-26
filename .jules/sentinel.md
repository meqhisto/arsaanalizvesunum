## 2024-04-23 - [Information Leakage in Error Handler]
**Vulnerability:** The application is vulnerable to information leakage via its 500 error handler in `app.py`. It directly embeds `str(e)` in the response sent to the user (`return f"Bir sunucu hatası oluştu: {str(e)}. Detaylar loglandı.", 500`).
**Learning:** Returning exception details to the user can expose sensitive system information, such as database queries, internal paths, or logic details, which attackers can leverage.
**Prevention:** In production environments, never return raw exception messages or stack traces to the user. Log the error internally and return a generic, user-friendly error message.
