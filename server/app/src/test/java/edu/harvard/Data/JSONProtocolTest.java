package edu.harvard.Data;

import org.json.JSONObject;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Data.ListAccountsRequest;
import edu.harvard.Data.Data.LoginCreateRequest;
import edu.harvard.Data.Data.MessageResponse;
import edu.harvard.Data.Data.SendMessageRequest;
import edu.harvard.Data.Protocol.Operation;
import edu.harvard.Data.Protocol.Request;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class JSONProtocolTest {
  InputStream streamFromString(String string) {
    return new ByteArrayInputStream(string.substring(1).getBytes(StandardCharsets.UTF_8));
  }

  Request parse(String json) throws Protocol.ParseException {
    return new JSONProtocol().parseRequest(123, streamFromString(json));
  }

  Request parseValid(String json) {
    try {
      return new JSONProtocol().parseRequest(123, streamFromString(json));
    } catch (Exception ex) {
      throw new RuntimeException("Unexpecting parsing exception!");
    }
  }

  JSONObject parseResponse(byte[] response) {
    return new JSONObject(new String(response, StandardCharsets.UTF_8));
  }

  @Test
  void invalidJson() {
    assertThrows(Protocol.ParseException.class, () -> parse("invalid"));
  }

  @Test
  void noOperationCode() {
    assertThrows(Protocol.ParseException.class, () -> parse("{}"));
  }

  @Test
  void noPayloadWhereRequired() {
    String json = "{\"operation\":\"LOOKUP_USER\"}";
    assertThrows(Protocol.ParseException.class, () -> parse(json));
  }

  @Test
  void noRequiredField() {
    String json = "{\"operation\":\"LOOKUP_USER\", \"payload\": {}}";
    assertThrows(Protocol.ParseException.class, () -> parse(json));
  }

  @Test
  void wrongTypeRequiredField() {
    String json = "{\"operation\":\"LOOKUP_USER\", \"payload\": {\"username\": 1}}";
    assertThrows(Protocol.ParseException.class, () -> parse(json));
  }

  @Test
  void lookupUser() {
    String json = "{\"operation\":\"LOOKUP_USER\", \"payload\": {\"username\": \"june\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LOOKUP_USER);
    assertEquals(req.payload, "june");
  }

  @Test
  void login() {
    String json = "{\"operation\":\"LOGIN\", \"payload\": {\"username\": \"june\", \"password_hash\": \"example\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LOGIN);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void create() {
    String json = "{\"operation\":\"CREATE_ACCOUNT\", \"payload\": {\"username\": \"june\", \"password_hash\": \"example\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.CREATE_ACCOUNT);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void list() {
    String json = "{\"operation\":\"LIST_ACCOUNTS\", \"payload\": {\"maximum_number\": 10, \"offset_account_id\": 0}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 0);
    assertEquals(payload.filter_text, "");
  }

  @Test
  void listWithFilter() {
    String json = "{\"operation\":\"LIST_ACCOUNTS\", \"payload\": {\"maximum_number\": 10, \"offset_account_id\": 10, \"filter_text\": \"user\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 10);
    assertEquals(payload.filter_text, "user");
  }

  @Test
  void send() {
    String json = "{\"operation\":\"SEND_MESSAGE\", \"payload\": {\"recipient\": \"june\", \"message\": \"test\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, "test");
  }

  @Test
  void sendLongMessage() {
    String longMessage = "1".repeat(50000);
    String json = "{\"operation\":\"SEND_MESSAGE\", \"payload\": {\"recipient\": \"june\", \"message\": \""
        + longMessage + "\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, longMessage);
  }

  @Test
  void requestMessages() {
    String json = "{\"operation\":\"REQUEST_MESSAGES\", \"payload\": {\"maximum_number\": 10}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.REQUEST_MESSAGES);
    assertEquals(req.payload, 10);
  }

  @SuppressWarnings("unchecked")
  @Test
  void deleteMessages() {
    String json = "{\"operation\":\"DELETE_MESSAGES\", \"payload\": {\"message_ids\": [1,2,3,4,55,812]}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.DELETE_MESSAGES);
    assertIterableEquals((List<Integer>) req.payload, List.of(1, 2, 3, 4, 55, 812));
  }

  @Test
  void deleteAccount() {
    String json = "{\"operation\":\"DELETE_ACCOUNT\"}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.DELETE_ACCOUNT);
  }

  @Test
  void lookupUserResponse() {
    AccountLookupResponse response = new AccountLookupResponse();
    response.exists = true;
    response.bcrypt_prefix = "1".repeat(29);
    JSONObject obj = parseResponse(new JSONProtocol().generateLookupUserResponse(response));
    assertEquals(obj.get("operation"), Operation.LOOKUP_USER.toString());
    assertEquals(obj.get("success"), true);
    JSONObject payload = obj.getJSONObject("payload");
    assertEquals(payload.get("exists"), true);
    assertEquals(payload.get("bcrypt_prefix"), response.bcrypt_prefix);
    AccountLookupResponse response2 = new AccountLookupResponse();
    response.exists = false;
    JSONObject obj2 = parseResponse(new JSONProtocol().generateLookupUserResponse(response2));
    JSONObject payload2 = obj2.getJSONObject("payload");
    assertEquals(payload2.get("exists"), false);
  }

  @Test
  void loginResponse() {
    JSONObject obj = parseResponse(new JSONProtocol().generateLoginResponse(true, 5));
    assertEquals(obj.get("operation"), Operation.LOGIN.toString());
    assertEquals(obj.get("success"), true);
    JSONObject payload = obj.getJSONObject("payload");
    assertEquals(payload.get("unread_messages"), 5);
    JSONObject obj2 = parseResponse(new JSONProtocol().generateLoginResponse(false, 0));
    assertEquals(obj2.get("success"), false);
  }

  @Test
  void createAccountResponse() {
    JSONObject obj = parseResponse(new JSONProtocol().generateCreateAccountResponse(true));
    assertEquals(obj.get("operation"), Operation.CREATE_ACCOUNT.toString());
    assertEquals(obj.get("success"), true);
    JSONObject obj2 = parseResponse(new JSONProtocol().generateCreateAccountResponse(false));
    assertEquals(obj2.get("success"), false);
  }

  @Test
  void listAccountsResponse() {
    List<Account> list = new ArrayList<>(2);
    Account a1 = new Account();
    a1.id = 1;
    a1.username = "june";
    Account a2 = new Account();
    a2.id = 2;
    a2.username = "catherine";
    list.add(a1);
    list.add(a2);
    JSONObject obj = parseResponse(new JSONProtocol().generateListAccountsResponse(list));
    assertEquals(obj.get("operation"), Operation.LIST_ACCOUNTS.toString());
    assertEquals(obj.get("success"), true);
    JSONObject payload = obj.getJSONObject("payload");
    assertEquals(payload.getJSONArray("accounts").getJSONObject(0).get("id"), 1);
    assertEquals(payload.getJSONArray("accounts").getJSONObject(1).get("username"), a2.username);
  }

  @Test
  void sendMessageResponse() {
    JSONObject obj = parseResponse(new JSONProtocol().generateSendMessageResponse(5));
    assertEquals(obj.get("operation"), Operation.SEND_MESSAGE.toString());
    assertEquals(obj.get("success"), true);
    JSONObject payload = obj.getJSONObject("payload");
    assertEquals(payload.get("message_id"), 5);
  }

  @Test
  void requestMessagesResponse() {
    List<MessageResponse> list = new ArrayList<>(2);
    MessageResponse m1 = new MessageResponse();
    m1.id = 1;
    m1.sender = "june";
    m1.message = "Hi!";
    MessageResponse m2 = new MessageResponse();
    m2.id = 1;
    m2.sender = "catherine";
    m2.message = "Hello!";
    list.add(m1);
    list.add(m2);
    JSONObject obj = parseResponse(new JSONProtocol().generateRequestMessagesResponse(list));
    assertEquals(obj.get("operation"), Operation.REQUEST_MESSAGES.toString());
    assertEquals(obj.get("success"), true);
    JSONObject payload = obj.getJSONObject("payload");
    assertEquals(payload.getJSONArray("messages").getJSONObject(0).get("id"), 1);
    assertEquals(payload.getJSONArray("messages").getJSONObject(0).get("message"), m1.message);
    assertEquals(payload.getJSONArray("messages").getJSONObject(1).get("sender"), m2.sender);
    assertEquals(payload.getJSONArray("messages").getJSONObject(1).get("message"), m2.message);
  }

  @Test
  void deleteMessageResponse() {
    JSONObject obj = parseResponse(new JSONProtocol().generateDeleteMessagesResponse(true));
    assertEquals(obj.get("operation"), Operation.DELETE_MESSAGES.toString());
    assertEquals(obj.get("success"), true);
    JSONObject obj2 = parseResponse(new JSONProtocol().generateDeleteMessagesResponse(false));
    assertEquals(obj2.get("success"), false);
  }

  @Test
  void unexpectedFailure() {
    JSONObject obj = parseResponse(
        new JSONProtocol().generateUnexpectedFailureResponse(Operation.LIST_ACCOUNTS, "example"));
    assertEquals(obj.get("operation"), Operation.LIST_ACCOUNTS.toString());
    assertEquals(obj.get("success"), false);
    assertEquals(obj.get("unexpected_failure"), true);
    assertEquals(obj.get("message"), "example");
  }
}
