# Twitter DM Scraper API

This FastAPI service provides endpoints to fetch Twitter Direct Message (DM) conversations and user metadata by leveraging Twitter’s private API endpoints. The service requires user authentication via cookies and bearer token.

---

## Authentication

Each endpoint requires passing:

- **cookies**: A dictionary of cookies `{name: value}` from the authenticated Twitter session.  
- **bearer_token**: Twitter OAuth2 Bearer token string.  

These credentials are used internally to authenticate API calls to Twitter.

---

## Endpoints

### `/fetch_initial_state`  
**Method:** POST  
**Description:**  
Fetches the initial DM inbox state from Twitter and returns a deduplicated list of conversation IDs available for the authenticated user. This endpoint handles the first step in retrieving DM conversations by providing conversation identifiers.

**Request Body:**  
Requires authentication data: cookies and bearer token.

**Response:**  
Returns a JSON object containing a list of unique conversation IDs.

---

### `/fetch_users_metadata`  
**Method:** POST  
**Description:**  
Fetches all user metadata related to the authenticated user’s DM inbox. The endpoint paginates through the inbox state pages and aggregates all user details. Returned data contains a dictionary keyed by user ID with user name and screen name as values.

**Request Body:**  
Requires authentication data: cookies and bearer token.

**Response:**  
Returns a JSON object containing user metadata: user IDs mapped to names and screen names.

---

### `/fetch_all_conversations`  
**Method:** POST  
**Description:**  
Retrieves the full DM conversations for the authenticated user. It first fetches all conversation IDs using the initial state endpoint, then concurrently fetches message data for each conversation. The result includes conversation IDs along with their respective messages, sender and recipient IDs, text content, and timestamps.

**Request Body:**  
Requires authentication data: cookies and bearer token.

**Response:**  
Returns a JSON object containing a list of conversations, each with its ID and an array of messages.

---

## Notes

- All endpoints require valid Twitter authentication cookies and bearer token for authorization.  
- The service uses a secure SSL context with `certifi` to ensure HTTPS request integrity.  
- Pagination is supported where applicable to retrieve comprehensive datasets.  
- Users should be aware of Twitter's rate limits and API restrictions to avoid blocking or throttling.

---

## Screenshots

Screenshots documenting success cases, error responses, and edge cases for each endpoint should be added manually here.
