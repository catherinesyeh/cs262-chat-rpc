package edu.harvard.Data;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Data.MessageResponse;

/*
 * Implements the JSON request/response protocol (JSON.md).
 */
public class JSONProtocol implements Protocol {
  // The operation_code parameter is just the first byte, and is ignored here.
  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException {
    try {
      // Read a single line off the input stream
      BufferedReader in = new BufferedReader(
          new InputStreamReader(
              inputStream));
      String inputLine = "{".concat(in.readLine());
      JSONObject obj = null;
      Operation operation;
      // Attempt to parse the line as JSON, and determine the operation code
      try {
        obj = new JSONObject(inputLine);
        operation = Operation.valueOf(obj.getString("operation"));
        if (operation == null || operation.equals(Operation.UNKNOWN)) {
          throw new ParseException("Invalid operation code.");
        }
      } catch (JSONException ex) {
        throw new ParseException("Could not parse operation code.");
      }
      // Pull the `payload` property off the JSON request, if needed.
      JSONObject payload = null;
      try {
        // All other operations require some payload.
        if (!operation.equals(Operation.DELETE_ACCOUNT)) {
          payload = obj.getJSONObject("payload");
        }
      } catch (JSONException ex) {
        throw new ParseException("JSON requests must include a payload field.");
      }
      // Remaining parse steps are operation dependent.
      try {
        Request parsedRequest = new Request();
        parsedRequest.operation = operation;
        switch (operation) {
          case LOOKUP_USER:
            parsedRequest.payload = payload.getString("username");
            return parsedRequest;
          case LOGIN:
          case CREATE_ACCOUNT:
            // These two requests use the same format.
            Data.LoginCreateRequest loginCreatePayload = new Data.LoginCreateRequest();
            loginCreatePayload.username = payload.getString("username");
            loginCreatePayload.password_hash = payload.getString("password_hash");
            parsedRequest.payload = loginCreatePayload;
            return parsedRequest;
          case LIST_ACCOUNTS:
            Data.ListAccountsRequest listPayload = new Data.ListAccountsRequest();
            listPayload.maximum_number = payload.getInt("maximum_number");
            listPayload.offset_account_id = payload.getInt("offset_account_id");
            // Filter text is optional, treat it as empty string if none exists.
            try {
              listPayload.filter_text = payload.getString("filter_text");
            } catch (JSONException ex) {
              listPayload.filter_text = "";
            }
            parsedRequest.payload = listPayload;
            return parsedRequest;
          case SEND_MESSAGE:
            Data.SendMessageRequest sendPayload = new Data.SendMessageRequest();
            sendPayload.recipient = payload.getString("recipient");
            sendPayload.message = payload.getString("message");
            parsedRequest.payload = sendPayload;
            return parsedRequest;
          case REQUEST_MESSAGES:
            parsedRequest.payload = payload.getInt("maximum_number");
            return parsedRequest;
          case DELETE_MESSAGES:
            parsedRequest.payload = payload.getJSONArray("message_ids").toList();
            return parsedRequest;
          default:
            // DELETE_ACCOUNT or others with no payload to parse
            return parsedRequest;
        }
      } catch (JSONException ex) {
        System.err.println("JSON parse error:");
        System.err.println(operation);
        System.err.println(ex.getMessage());
        throw new ParseException("Your JSON request did not include a required field.");
      }
    } catch (IOException ex) {
      throw new ParseException("Unexpected JSON parsing error.");
    }
  }

  // Output building

  // Standard JSON response format
  private byte[] wrapPayload(Operation operation, boolean success, JSONObject payload) {
    JSONObject response = new JSONObject();
    response.put("operation", operation.toString());
    response.put("success", success);
    if (payload != null) {
      response.put("payload", payload);
    }
    return (response.toString() + '\n').getBytes(StandardCharsets.UTF_8);
  }

  public byte[] generateLookupUserResponse(AccountLookupResponse internalResponse) {
    JSONObject response = new JSONObject();
    response.put("exists", internalResponse.exists);
    response.put("bcrypt_prefix", internalResponse.bcrypt_prefix);
    return wrapPayload(Operation.LOOKUP_USER, true, response);
  }

  public byte[] generateLoginResponse(boolean success, int unread_messages) {
    JSONObject response = new JSONObject();
    response.put("unread_messages", unread_messages);
    return wrapPayload(Operation.LOGIN, success, response);
  }

  public byte[] generateCreateAccountResponse(boolean success) {
    return wrapPayload(Operation.CREATE_ACCOUNT, success, null);
  }

  public byte[] generateListAccountsResponse(List<Account> accounts) {
    JSONObject response = new JSONObject();
    JSONArray jsonAccounts = new JSONArray();
    for (Account account : accounts) {
      JSONObject jsonAccount = new JSONObject();
      jsonAccount.put("id", account.id);
      jsonAccount.put("username", account.username);
      jsonAccounts.put(jsonAccount);
    }
    response.put("accounts", jsonAccounts);
    return wrapPayload(Operation.LIST_ACCOUNTS, true, response);
  }

  public byte[] generateSendMessageResponse(int message_id) {
    JSONObject response = new JSONObject();
    response.put("message_id", message_id);
    return wrapPayload(Operation.SEND_MESSAGE, true, response);
  }

  public byte[] generateRequestMessagesResponse(List<MessageResponse> messages) {
    JSONObject response = new JSONObject();
    JSONArray jsonMessages = new JSONArray();
    for (MessageResponse message : messages) {
      JSONObject jsonMessage = new JSONObject();
      jsonMessage.put("id", message.id);
      jsonMessage.put("sender", message.sender);
      jsonMessage.put("message", message.message);
      jsonMessages.put(jsonMessage);
    }
    response.put("messages", jsonMessages);
    return wrapPayload(Operation.REQUEST_MESSAGES, true, response);
  }

  public byte[] generateDeleteMessagesResponse(boolean success) {
    return wrapPayload(Operation.DELETE_MESSAGES, success, null);
  }

  public byte[] generateUnexpectedFailureResponse(Operation operation, String message) {
    JSONObject response = new JSONObject();
    response.put("operation", operation.toString());
    response.put("success", false);
    response.put("unexpected_failure", true);
    response.put("message", message);
    return (response.toString() + '\n').getBytes(StandardCharsets.UTF_8);
  }
}
