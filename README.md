# Twitter DM Scraper API  
Clone & run `uvicorn app:app --reload`

## Table of Contents

1. [Authentication Requirements](#authentication-requirements)  
2. [API Endpoints](#api-endpoints)  
   2.1 [POST /fetch_initial_state](#21-post-fetch_initial_state)  
   2.2 [POST /fetch_users_metadata](#22-post-fetch_users_metadata)  
   2.3 [POST /fetch_all_conversations](#23-post-fetch_all_conversations)  
3. [Important Notes](#important-notes)  

---

## 1. Authentication Requirements

Each endpoint requires the following authentication information:

- **cookies**: A dictionary of cookie name-value pairs from the user’s Twitter session.  
- **bearer_token**: The OAuth2 bearer token string associated with the session.  

These credentials authenticate requests made to Twitter on behalf of the user.

---

## 2. API Endpoints

### 2.1 POST /fetch_initial_state  
**Description:**  
Retrieves the initial state of the user’s DM inbox. This endpoint extracts and returns a unique list of conversation IDs that represent all active DM threads available to the authenticated user.

**Request Body:**  
- Authentication data containing `cookies` and `bearer_token`.

**Response:**  
- JSON object with a deduplicated list of conversation IDs.

---

### 2.2 POST /fetch_users_metadata  
**Description:**  
Fetches metadata for all users involved in the authenticated user’s DM conversations. The endpoint handles pagination internally to gather complete user data across inbox pages.

**Request Body:**  
- Authentication data containing `cookies` and `bearer_token`.

**Response:**  
- JSON object containing a dictionary keyed by user IDs, with values including user `name` and `screen_name`.

---

### 2.3 POST /fetch_all_conversations  
**Description:**  
Retrieves detailed message history for all DM conversations of the authenticated user. It first obtains all conversation IDs via the initial state, then concurrently fetches messages for each conversation. Returned data includes conversation IDs alongside arrays of message objects, each containing sender/recipient IDs, text, and timestamps.

**Request Body:**  
- Authentication data containing `cookies` and `bearer_token`.

**Response:**  
- JSON object containing a list of conversations, where each conversation includes:
  - `conversation_id`
  - `messages` (list of message objects with sender, recipient, text, timestamp)

---

## 3. Important Notes

- **Authentication:** Valid cookies and bearer token are mandatory for all requests.  
- **Security:** Uses SSL context with certificate verification via `certifi` for secure communication.  
- **Pagination:** Supported in user metadata retrieval to ensure complete data collection.  
- **Concurrency:** Message fetching is performed asynchronously to speed up retrieval of multiple conversations.  
- **API Limits:** Users should respect Twitter's API rate limits to avoid temporary blocks or throttling.  

---

## Documentation

Screenshots illustrating successful responses, error messages, and edge cases should be included separately to aid debugging and understanding of endpoint behaviors.

---

Feel free to extend this documentation with examples or detailed descriptions as needed.
