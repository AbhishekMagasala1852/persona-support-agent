# API Troubleshooting Guide

## Article: Understanding the 401 Unauthorized Error

A `401 Unauthorized` error means the API server has rejected your request because it could not verify your identity. This is almost always related to your authentication credentials, not a bug in your code logic.

Common causes and fixes:

1. **Expired API Key**: API keys automatically expire after 90 days of inactivity. Generate a new key from the Developer Dashboard under API Keys > Generate New Key.
2. **Missing Authorization Header**: Every request must include the header `Authorization: Bearer YOUR_API_KEY`. Double-check there are no extra spaces or missing the word "Bearer" before the key.
3. **Using a Test Key in Production**: Keys prefixed with `sk_test_` only work on our sandbox environment (`https://sandbox-api.example.com`). Production requests require a key prefixed with `sk_live_`.
4. **Revoked Key**: If a key was manually revoked from the dashboard (for example, after a security rotation), it will return 401 even if it has not technically expired.

To verify which scenario applies, check the response body of the 401 error. Our API always returns a JSON object with an `error_code` field, such as `key_expired`, `key_invalid`, or `key_revoked`, which tells you exactly which case you are facing.

## Article: Bearer Token Authentication — Header Parameter Requirements

Our API uses Bearer Token authentication for all endpoints under `/v2/`. Here are the exact header requirements:

| Header Name | Required | Example Value |
|---|---|---|
| Authorization | Yes | `Bearer sk_live_4f9a2b...` |
| Content-Type | Yes (for POST/PUT) | `application/json` |
| X-Request-ID | Optional | A UUID for tracing the request in logs |
| X-API-Version | Optional | `2024-01-15` (defaults to latest if omitted) |

Example of a correctly formatted request using `curl`:

```
curl -X GET https://api.example.com/v2/users/me \
  -H "Authorization: Bearer sk_live_4f9a2b8c1d" \
  -H "Content-Type: application/json"
```

Rate limits: Each API key is limited to 100 requests per minute. Exceeding this returns a `429 Too Many Requests` status code, along with a `Retry-After` header indicating how many seconds to wait before retrying.

## Article: Webhook Signature Verification Failing

If your webhook endpoint is rejecting incoming events due to signature mismatch, verify the following:

1. Ensure you are using the raw, unparsed request body to compute the signature, NOT a JSON-parsed-and-re-stringified version, since re-serialization can change whitespace and break the signature hash.
2. Confirm you are using the correct webhook signing secret, found under Developer Dashboard > Webhooks > Signing Secret. This is different from your regular API key.
3. Our signature header is named `X-Webhook-Signature` and uses the HMAC-SHA256 algorithm.
4. Clock skew: signatures include a timestamp and are rejected if more than 5 minutes old, relative to your server's clock. Ensure your server's system time is properly synced via NTP.

## Article: Database Connection / Integration Internal Errors

If your integration is experiencing internal errors related to database connectivity (often shown as a `500 Internal Server Error` or `503 Service Unavailable`), follow this step-by-step diagnostic pathway:

1. Check our public Status Page at status.example.com to rule out a known ongoing outage on our end.
2. Verify your connection pool settings. Our recommended configuration for production integrations is a maximum pool size of 20 connections with a 30-second idle timeout.
3. If you are using our SDK, ensure you are on version 4.2.0 or higher, as versions below 4.0 contained a known connection-leak bug that was patched in March 2024.
4. Review your integration logs for the specific error code returned in the `error.code` field of the response body, such as `db_timeout`, `db_pool_exhausted`, or `db_connection_refused`.
5. If the issue persists after the above checks, gather your `X-Request-ID` values from the failed requests and include them when escalating to support, as this allows our engineering team to trace the exact failure point on our servers.

## Article: API Versioning and Deprecation Policy

We maintain backward compatibility for all API versions for a minimum of 12 months after a new version is released. Deprecated endpoints return a `Deprecation` header along with a `Sunset` header indicating the exact date the endpoint will stop functioning. We recommend monitoring response headers programmatically in your integration to catch deprecation notices early, rather than relying solely on email announcements.
