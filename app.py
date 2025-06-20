from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
import aiohttp
import ssl
from typing import Optional, List, Dict, Any
import certifi
from datetime import datetime
import asyncio
app = FastAPI()


class AuthData(BaseModel):
    """
    1) Parameters:
       - cookies [dict]: Dictionary of cookies with {name: value} format.
       - bearer_token [str]: Bearer token string for authorization.
    2) Returns:
       - None (This is a data model class)
    3) Working:
       - Defines the expected structure for authentication data input.
    """
    cookies: dict  # Expecting cookie dict {name: value}
    bearer_token: str


class UsersPayload(BaseModel):
    """
    1) Parameters:
       - users [Dict[str, Dict[str, Any]]]: Raw users dictionary from Twitter API response.
    2) Returns:
       - None (This is a data model class)
    3) Working:
       - Defines expected structure for users data payload from API.
    """
    users: Dict[str, Dict[str, Any]]  # Raw users dict from Twitter API


def FormatCookieHeader(cookies: dict) -> str:
    """
    1) Parameters:
       - cookies [dict]: Dictionary of cookie names and values.
    2) Returns:
       - cookie_header [str]: Formatted cookie header string for HTTP requests.
    3) Working:
       - Iterates through the cookie dictionary.
       - Joins cookie key-value pairs as "key=value" separated by semicolons.
       - Returns the formatted string suitable for the "Cookie" header.
    """
    return '; '.join([f'{name}={value}' for name, value in cookies.items()])


def ExtractConversationIds(payload: dict) -> List[str]:
    """
    1) Parameters:
       - payload [dict]: JSON payload from Twitter's inbox initial state endpoint.
    2) Returns:
       - conversation_ids [List[str]]: List of conversation IDs extracted from payload.
    3) Working:
       - Extracts 'inbox_initial_state' key from payload.
       - Iterates through 'entries' list inside inbox state.
       - For each entry, extracts the 'conversation_id' from message if present.
       - Returns all found conversation IDs as a list.
    """
    conversation_ids = []
    inbox_state = payload.get('inbox_initial_state', {})
    entries = inbox_state.get('entries', [])
    for entry in entries:
        message = entry.get('message')
        if message:
            conv_id = message.get('conversation_id')
            if conv_id:
                conversation_ids.append(conv_id)
    return conversation_ids


def ExtractUsersMetadata(users_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """
    1) Parameters:
       - users_dict [Dict[str, Dict[str, Any]]]: Raw user dictionary from Twitter API.
    2) Returns:
       - result [Dict[str, Dict[str, str]]]: Simplified user info keyed by user ID, 
         containing only 'name' and 'screen_name'.
    3) Working:
       - Iterates over each user in the raw users dictionary.
       - Extracts 'name' and 'screen_name' fields, defaulting to empty strings if missing.
       - Constructs a simplified dictionary with user_id as key and a dictionary of
         the two fields as value.
       - Returns the simplified users dictionary.
    """
    result = {}
    for user_id_str, user_info in users_dict.items():
        result[user_id_str] = {
            "name": user_info.get("name", ""),
            "screen_name": user_info.get("screen_name", "")
        }
    return result

@app.post("/fetch-initial-state")
async def fetch_initial_state(auth_data: AuthData):
    """
    1) Parameters:
       - auth_data [AuthData]: Pydantic model containing:
           * cookies [dict]: Cookie dictionary {name: value}.
           * bearer_token [str]: Bearer token string for authorization.

    2) Returns:
       - dict: A dictionary containing:
           * conversation_ids [List[str]]: List of unique conversation IDs fetched.
           * total [int]: Total count of unique conversation IDs.

    3) Working:
       - Extract cookies and bearer token from the request payload.
       - Build HTTP headers including authorization, user agent, CSRF token, cookie header, and Twitter-specific headers.
       - Create SSL context with proper certificate validation using certifi.
       - Define base URL for Twitter's inbox initial state endpoint.
       - Initialize an empty set to store unique conversation IDs and set cursor to None.
       - Create an asynchronous HTTP session with the prepared headers.
       - Enter a loop to paginate through inbox data:
          * Append the cursor parameter to the URL if available.
          * Perform GET request to the endpoint with SSL context.
          * Check HTTP response status; raise HTTPException if non-200.
          * Parse JSON response.
          * Extract conversation IDs from the payload using ExtractConversationIds function and add to the set.
          * Access pagination info from 'trusted' timeline in response.
          * If status is 'AT_END', break loop (no more pages).
          * Otherwise, update cursor with 'min_entry_id' for next page; break if cursor is missing.
       - Return the list of unique conversation IDs and their total count.
    """

    cookies = auth_data.cookies
    bearer_token = auth_data.bearer_token

    headers = {
        "Authorization": bearer_token,
        "User-Agent": "Mozilla/5.0",
        "x-csrf-token": cookies.get("ct0", ""),
        "Cookie": FormatCookieHeader(cookies),
        'x-twitter-active-user':'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-client-language': 'en',
        'accept': 'application/json, text/plain, */*',
        'origin':'https://x.com',
        'referer':'https://x.com.messages',
        'connection':'keep-active'
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    base_url = "https://twitter.com/i/api/1.1/dm/inbox_initial_state"
    conversation_ids = set()
    cursor = None

    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            url = base_url
            if cursor:
                url += f"?cursor={cursor}"

            async with session.get(url, ssl=ssl_context) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail=await response.text())

                data = await response.json()

                # Extract conversation IDs
                new_ids = ExtractConversationIds(data)
                conversation_ids.update(new_ids)

                # Handle pagination
                trusted_timeline = data.get("inbox_timelines", {}).get("trusted", {})
                status = trusted_timeline.get("status")
                if status == "AT_END":
                    break

                cursor = trusted_timeline.get("min_entry_id")
                if not cursor:
                    break

    return {
        "conversation_ids": list(conversation_ids),
        "total": len(conversation_ids)
    }


def ExtractUsersMetadata(users: Dict) -> Dict[str, Dict[str, str]]:
    """
    1) Parameters:
       - users [Dict]: Raw users dictionary from Twitter API, keyed by user ID strings,
         where each value is a dict with user details.

    2) Returns:
       - result [Dict[str, Dict[str, str]]]: Simplified dictionary keyed by user ID strings,
         with each value containing only:
           * "name" [str]: User's display name (empty string if missing).
           * "screen_name" [str]: User's screen name (empty string if missing).

    3) Working:
       - Initialize an empty result dictionary.
       - Iterate over each user_id and user_info in the input users dictionary.
       - For each user, extract the "name" and "screen_name" fields safely (defaulting to "").
       - Store these two fields in the result dict with user_id as the key.
       - Return the simplified result dictionary.
    """
    result = {}
    for user_id_str, user_info in users.items():
        result[user_id_str] = {
            "name": user_info.get("name", ""),
            "screen_name": user_info.get("screen_name", "")
        }
    return result


@app.post("/fetch_users_metadata")
async def fetch_users_metadata(auth_data: AuthData):
    """
    1) Parameters:
       - auth_data [AuthData]: Pydantic model containing:
           * cookies [dict]: Cookie dictionary {name: value}.
           * bearer_token [str]: Bearer token string for authorization.

    2) Returns:
       - dict: A dictionary containing:
           * user_count [int]: Number of unique users fetched.
           * users [Dict[str, Dict[str, str]]]: Simplified user metadata keyed by user ID strings,
             each containing:
               - "name" [str]: User's display name.
               - "screen_name" [str]: User's screen name.

    3) Working:
       - Extract cookies and bearer token from the request payload.
       - Construct HTTP headers including authorization, user-agent, CSRF token, cookie header,
         and other Twitter-specific headers.
       - Create SSL context with proper cert validation using certifi.
       - Define base URL for Twitter's inbox initial state endpoint.
       - Initialize empty dictionary to hold all user data and cursor as None for pagination.
       - Start async HTTP session with headers.
       - Loop to paginate through the inbox:
          * Build URL, appending cursor query parameter if cursor is present.
          * Make GET request with SSL context.
          * If response status is not 200, raise HTTPException with error details.
          * Parse JSON response.
          * Extract users dictionary from "inbox_initial_state" or fallback to root response.
          * Merge the newly fetched users into the cumulative dictionary.
          * Check pagination status from "trusted" inbox timeline.
          * Break loop if status is "AT_END" or no cursor is available.
       - After pagination completes, simplify users metadata using ExtractUsersMetadata.
       - Return the count of unique users and the simplified users dictionary.
    """
    cookies = auth_data.cookies
    bearer_token = auth_data.bearer_token

    headers = {
        "Authorization": bearer_token,
        "User-Agent": "Mozilla/5.0 ...",
        "x-csrf-token": cookies.get("ct0", ""),
        "Cookie": FormatCookieHeader(cookies),
        'x-twitter-active-user': 'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-client-language': 'en',
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://x.com',
        'referer': 'https://x.com.messages',
        'connection': 'keep-alive',
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    base_url = "https://twitter.com/i/api/1.1/dm/inbox_initial_state"

    all_users = {}
    cursor = None

    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            url = base_url
            if cursor:
                url += f"?cursor={cursor}"

            async with session.get(url, ssl=ssl_context) as resp:
                if resp.status != 200:
                    detail = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=detail)
                data = await resp.json()

                initial_state = data.get("inbox_initial_state", data)
                users = initial_state.get("users", {})
                all_users.update(users)

                # Pagination check
                trusted = data.get("inbox_timelines", {}).get("trusted", {})
                status = trusted.get("status")
                if status == "AT_END":
                    break
                cursor = trusted.get("min_entry_id")
                if not cursor:
                    break

    simplified_users = ExtractUsersMetadata(all_users)
    return {
        "user_count": len(simplified_users),
        "users": simplified_users
    }


async def FetchDMConversations(conversation_id: str, headers: dict, ssl_context) -> List[Dict[str, Any]]:
    """
    1) Parameters:
       - conversation_id [str]: The unique ID of the direct message conversation to fetch.
       - headers [dict]: HTTP headers including authorization and cookies to authenticate the request.
       - ssl_context: SSL context object for secure HTTPS requests.

    2) Returns:
       - simplified_messages [List[Dict[str, Any]]]: A list of simplified message dictionaries, each containing:
           * sender_id [str]: ID of the sender.
           * recipient_id [str]: ID of the recipient.
           * text [str]: The text content of the message.
           * timestamp [str | None]: ISO-formatted timestamp of the message, or None if unavailable.

    3) Working:
       - Construct the base URL for the conversation endpoint using the conversation ID.
       - Initialize an empty list to accumulate simplified messages.
       - Initialize a set to track seen 'min_entry_id' values for pagination.
       - Set flags and counters to manage pagination.
       - Start an aiohttp ClientSession with given headers.
       - Enter a loop that continues while more pages exist:
           * Build query params, including max_id for pagination if available.
           * Make an async GET request to fetch conversation data.
           * Raise an HTTPException if the response status is not 200.
           * Parse JSON response.
           * Extract the conversation timeline and its entries.
           * For each entry, extract the message data if present.
           * Convert message timestamps from milliseconds to ISO format.
           * Append simplified message dicts to the list.
           * Check the timeline status and 'min_entry_id' to control pagination:
               - Stop if status is "AT_END", no new min_entry_id, or if min_entry_id already seen.
               - Otherwise, add new min_entry_id to seen set and update max_id to paginate.
           * Increment the page count.
       - Return the accumulated list of simplified messages.
    """
    base_url = f"https://x.com/i/api/1.1/dm/conversation/{conversation_id}.json"
    simplified_messages = []
    seen_min_entry_ids = set()
    has_more = True
    max_id = None
    page_count = 0

    async with aiohttp.ClientSession(headers=headers) as session:
        while has_more:
            params = {}
            if max_id:
                params['max_id'] = max_id

            async with session.get(base_url, params=params, ssl=ssl_context) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail=f"Error fetching page {page_count}")

                data = await resp.json()
                timeline = data.get("conversation_timeline", {})
                entries = timeline.get("entries", [])

                for entry in entries:
                    message = entry.get("message", {})
                    msg_data = message.get("message_data", {})

                    if msg_data:
                        timestamp_ms = msg_data.get("time")
                        timestamp_dt = datetime.fromtimestamp(int(timestamp_ms) / 1000) if timestamp_ms else None

                        simplified_messages.append({
                            "sender_id": msg_data.get("sender_id"),
                            "recipient_id": msg_data.get("recipient_id"),
                            "text": msg_data.get("text"),
                            "timestamp": timestamp_dt.isoformat() if timestamp_dt else None
                        })

                status = timeline.get("status")
                new_min_entry_id = timeline.get("min_entry_id")

                if status == "AT_END":
                    has_more = False
                elif not new_min_entry_id:
                    has_more = False
                elif new_min_entry_id in seen_min_entry_ids:
                    has_more = False
                else:
                    seen_min_entry_ids.add(new_min_entry_id)
                    max_id = new_min_entry_id

                page_count += 1

    return simplified_messages


@app.post("/fetch_dm/{conversation_id}")
async def fetch_dm_conversation(
    conversation_id: str = Path(..., description="The conversation ID to fetch"),
    auth_data: AuthData = ...
):
    """
    1) Parameters:
       - conversation_id [str]: The ID of the DM conversation to fetch, provided as a path parameter.
       - auth_data [AuthData]: Pydantic model containing:
           * cookies [dict]: Cookie dictionary {name: value}.
           * bearer_token [str]: Bearer token string for authorization.

    2) Returns:
       - dict: A dictionary containing:
           * conversation_id [str]: The requested conversation ID.
           * messages [List[dict]]: List of simplified messages returned by FetchDMConversations.

    3) Working:
       - Extract cookies and bearer token from the request body.
       - Construct HTTP headers including authorization, user-agent, CSRF token, cookie header,
         and other Twitter-specific headers needed for the API call.
       - Create SSL context with certifi CA certificates for secure connection.
       - Call the async helper function `FetchDMConversations` with conversation_id, headers, and ssl_context.
       - Await the result which returns the list of simplified messages in that conversation.
       - Return a JSON response containing the conversation ID and the fetched messages.
    """
    cookies = auth_data.cookies
    bearer_token = auth_data.bearer_token

    headers = {
        "Authorization": bearer_token,
        "User-Agent": "Mozilla/5.0 ...",
        "x-csrf-token": cookies.get("ct0", ""),
        "Cookie": FormatCookieHeader(cookies),
        'x-twitter-active-user': 'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-client-language': 'en',
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://x.com',
        'referer': 'https://x.com.messages',
        'connection': 'keep-alive',
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    messages = await FetchDMConversations(conversation_id, headers, ssl_context)
    return {"conversation_id": conversation_id, "messages": messages}

async def FetchAllDMConversations(conversation_ids: List[str], headers: dict, ssl_context) -> List[Dict[str, Any]]:
    """
    1) Parameters:
       - conversation_ids [List[str]]: List of conversation IDs to fetch messages for.
       - headers [dict]: HTTP headers for authorization and cookies.
       - ssl_context: SSL context for secure HTTPS requests.

    2) Returns:
       - all_conversations [List[Dict[str, Any]]]: List of dictionaries, each representing a conversation with:
           * conversation_id [str]: The conversation ID.
           * messages [List[Dict]]: List of simplified message dicts for that conversation.
           * error [str] (optional): Error message if fetching failed for that conversation.

    3) Working:
       - Calculate the total number of conversations to fetch.
       - Create a list of async tasks to fetch each conversation concurrently using `FetchDMConversations`.
       - Await completion of all tasks using `asyncio.gather`, allowing exceptions to be returned as results.
       - Iterate through each conversation ID and its corresponding result:
           * If the result is an Exception, log the failure and append a dict with empty messages and error.
           * Otherwise, count the number of messages fetched, log success, and append the conversation data.
       - Log the final count of successful scrapes.
       - Return the list of all conversations with their messages or errors.
    """
    total_convos = len(conversation_ids)

    tasks = [FetchDMConversations(convo_id, headers, ssl_context) for convo_id in conversation_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_conversations = []
    success_count = 0

    for convo_id, res in zip(conversation_ids, results):
        if isinstance(res, Exception):
            all_conversations.append({
                "conversation_id": convo_id,
                "messages": [],
                "error": str(res)
            })
        else:
            msg_count = len(res)
            success_count += 1
            all_conversations.append({
                "conversation_id": convo_id,
                "messages": res
            })

    return all_conversations

@app.post("/fetch_all_conversations")
async def fetch_all_conversations(auth_data: AuthData):
    """
    1) Parameters:
       - auth_data [AuthData]: Pydantic model containing:
          * cookies [dict]: Dictionary of cookies {name: value}.
          * bearer_token [str]: Bearer token string for authorization.

    2) Returns:
       - dict: JSON response containing:
          * conversations [List[Dict]]: List of conversations with messages and metadata.
          * message [str] (optional): Informational message if no conversations found.

    3) Working:
       - Extract cookies and bearer token from the request body.
       - Construct HTTP headers including Authorization, User-Agent, CSRF token, Cookie header,
         and other Twitter-specific headers required by the API.
       - Create an SSL context with certifi CA certificates for secure HTTPS requests.
       - Define an inner async helper function `fetch_conversation_ids` that:
          * Calls the Twitter inbox_initial_state API endpoint.
          * Raises HTTPException if response status is not 200.
          * Parses JSON response to extract unique conversation IDs using `ExtractConversationIds`.
       - Call `fetch_conversation_ids` to retrieve a list of conversation IDs.
       - If no conversation IDs are found, return early with an empty list and a message.
       - Otherwise, call the async `FetchAllDMConversations` function with conversation IDs, headers, and ssl context,
         which concurrently fetches all messages from each conversation.
       - Return the aggregated conversations list in JSON response.
    """
    cookies = auth_data.cookies
    bearer_token = auth_data.bearer_token

    headers = {
        "Authorization": bearer_token,
        "User-Agent": "Mozilla/5.0 ...",
        "x-csrf-token": cookies.get("ct0", ""),
        "Cookie": FormatCookieHeader(cookies),
        'x-twitter-active-user': 'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-client-language': 'en',
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://x.com',
        'referer': 'https://x.com.messages',
        'connection': 'keep-alive',
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def fetch_conversation_ids(headers, ssl_context):
        url = "https://twitter.com/i/api/1.1/dm/inbox_initial_state"
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, ssl=ssl_context) as resp:
                if resp.status != 200:
                    detail = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=detail)
                data = await resp.json()

        conversation_ids = ExtractConversationIds(data)
        return list(set(conversation_ids))

    conversation_ids = await fetch_conversation_ids(headers, ssl_context)

    if not conversation_ids:
        return {"conversations": [], "message": "No conversations found"}

    all_conversations = await FetchAllDMConversations(conversation_ids, headers, ssl_context)

    return {"conversations": all_conversations}
