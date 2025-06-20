# Twitter DM Scraper API  
Clone & run `uvicorn app:app --reload`

## Table of Contents

1. [Authentication Requirements](#authentication-requirements)  
2. [API Endpoints](#api-endpoints)  
   2.1 [POST /fetch_initial_state](#21-post-fetch_initial_state)  
   2.2 [POST /fetch_users_metadata](#22-post-fetch_users_metadata)  
   2.3 [POST /fetch_dm/{conversation_id}](#23-post-fetch_dm)<br>
   2.4 [POST /fetch_all_conversations](#24-post-fetch_all_conversations)
4. [Important Notes](#important-notes)  

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

**Example**
<img width="1435" alt="Screenshot 2025-06-19 at 8 36 59 PM" src="https://github.com/user-attachments/assets/d78d0afb-a5f7-45e4-a1d9-48014bae7c8e" />
![endpoint1](https://github.com/user-attachments/assets/18e545a3-cc68-4cef-8db5-48c0d3d9706b)


---

### 2.2 POST /fetch_users_metadata  
**Description:**  
Fetches metadata for all users involved in the authenticated user’s DM conversations. The endpoint handles pagination internally to gather complete user data across inbox pages.

**Request Body:**  
- Authentication data containing `cookies` and `bearer_token`.

**Response:**  
- JSON object containing a dictionary keyed by user IDs, with values including user `name` and `screen_name`.

**Example**
<img width="1427" alt="image" src="https://github.com/user-attachments/assets/79061467-753c-4c31-b24f-ea1125954d24" />
![endpoint2](https://github.com/user-attachments/assets/1fbdf29f-d453-4546-a687-d19a2ccb820a)

---

### 2.3 POST /fetch_dm/{conversation_id}  
**Description:**  
Retrieves the detailed message history for a specific DM conversation identified by the `conversation_id`. This endpoint fetches all messages within the conversation, including sender and recipient IDs, message text, and timestamps, handling pagination internally if needed.

**Path Parameters:**  
- `conversation_id` [string]: The unique identifier of the DM conversation to fetch messages from.

**Request Headers:**  
- Requires authentication headers including valid `cookies` and `bearer_token`.

**Response:**  
- JSON object containing:  
  - `conversation_id`: The requested conversation's ID.  
  - `messages`: A list of message objects, each including:  
    - `sender_id` [string]: ID of the message sender.  
    - `recipient_id` [string]: ID of the message recipient.  
    - `text` [string]: The text content of the message.  
    - `timestamp` [string, ISO8601]: The message's sent time in ISO 8601 format.

**Example**
<img width="1442" alt="image" src="https://github.com/user-attachments/assets/877169a4-c013-4065-a18d-fca0515a6058" />

![image](https://github.com/user-attachments/assets/12cbd5a4-2942-4956-bce6-121dec6d08fb)

---
   
### 2.4 POST /fetch_all_conversations        
**Description:**  
Retrieves detailed message history for all DM conversations of the authenticated user. It first obtains all conversation IDs via the initial state, then concurrently fetches messages for each conversation. Returned data includes conversation IDs alongside arrays of message objects, each containing sender/recipient IDs, text, and timestamps.

**Request Body:**  
- Authentication data containing `cookies` and `bearer_token`.

**Response:**  
- JSON object containing a list of conversations, where each conversation includes:
  - `conversation_id`
  - `messages` (list of message objects with sender, recipient, text, timestamp)
**Example**
<img width="1432" alt="image" src="https://github.com/user-attachments/assets/6e342f48-923b-42cc-b0dd-ea2e3536c0f0" />

![image](https://github.com/user-attachments/assets/093ce396-fdfd-4d87-9387-10a5109d4b35)

---

## 3. Important Notes

- **Authentication:** Valid cookies and bearer token are mandatory for all requests.  
- **Security:** Uses SSL context with certificate verification via `certifi` for secure communication.  
- **Pagination:** Supported in user metadata retrieval to ensure complete data collection.  
- **Concurrency:** Message fetching is performed asynchronously to speed up retrieval of multiple conversations.  
- **API Limits:** No rate limiting logic

---
## Future Work:
- Implement Logging
- Implement rate limits/ proxy rotation.
