package edu.harvard.Data;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import static edu.harvard.Data.WireProtocol.loadStringToBuffer;

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
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class WireProtocolTest {
  InputStream streamFromBuffer(ByteBuffer buffer) {
    return new ByteArrayInputStream(buffer.array());
  }

  Request parse(int opcode, ByteBuffer request) throws Protocol.ParseException {
    return new JSONProtocol().parseRequest(opcode, streamFromBuffer(request));
  }

  Request parseValid(int opcode, ByteBuffer request) {
    try {
      return new WireProtocol().parseRequest(opcode, streamFromBuffer(request));
    } catch (Exception ex) {
      throw new RuntimeException("Unexpecting parsing exception!");
    }
  }

  private String getString(ByteBuffer buffer, int string_length) {
    int length;
    if (string_length == 4) {
      length = buffer.getInt();
    } else if (string_length == 2) {
      length = ((int) buffer.get() << 8) + buffer.get();
    } else {
      length = buffer.get();
    }
    if (length > 0) {
      byte[] str = new byte[length];
      buffer.get(str);
      return new String(str, StandardCharsets.UTF_8);
    } else {
      return "";
    }
  }

  @Test
  void invalidOpcode() {
    assertThrows(Protocol.ParseException.class, () -> parse(0, ByteBuffer.allocate(1)));
  }

  @Test
  void lookupUser() {
    ByteBuffer buffer = ByteBuffer.allocate(5);
    loadStringToBuffer(buffer, "june", 1);
    Request req = parseValid(Operation.LOOKUP_USER.getId(), buffer);
    assertEquals(req.operation, Operation.LOOKUP_USER);
    assertEquals(req.payload, "june");
  }

  @Test
  void login() {
    ByteBuffer buffer = ByteBuffer.allocate(20);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, "example", 1);
    Request req = parseValid(Operation.LOGIN.getId(), buffer);
    assertEquals(req.operation, Operation.LOGIN);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void create() {
    ByteBuffer buffer = ByteBuffer.allocate(20);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, "example", 1);
    Request req = parseValid(Operation.CREATE_ACCOUNT.getId(), buffer);
    assertEquals(req.operation, Operation.CREATE_ACCOUNT);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void list() {
    ByteBuffer buffer = ByteBuffer.allocate(6);
    buffer.put((byte) 10);
    buffer.putInt(0);
    buffer.put((byte) 0);
    Request req = parseValid(Operation.LIST_ACCOUNTS.getId(), buffer);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 0);
    assertEquals(payload.filter_text, "");
  }

  @Test
  void listWithFilter() {
    ByteBuffer buffer = ByteBuffer.allocate(10);
    buffer.put((byte) 10);
    buffer.putInt(10);
    loadStringToBuffer(buffer, "user", 1);
    Request req = parseValid(Operation.LIST_ACCOUNTS.getId(), buffer);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 10);
    assertEquals(payload.filter_text, "user");
  }

  @Test
  void send() {
    ByteBuffer buffer = ByteBuffer.allocate(11);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, "test", 2);
    Request req = parseValid(Operation.SEND_MESSAGE.getId(), buffer);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, "test");
  }

  @Test
  void sendLongMessage() {
    String longMessage = "1".repeat(50000);
    ByteBuffer buffer = ByteBuffer.allocate(50010);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, longMessage, 2);
    Request req = parseValid(Operation.SEND_MESSAGE.getId(), buffer);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, longMessage);
  }

  @Test
  void requestMessages() {
    ByteBuffer buffer = ByteBuffer.allocate(1);
    buffer.put((byte) 10);
    Request req = parseValid(Operation.REQUEST_MESSAGES.getId(), buffer);
    assertEquals(req.operation, Operation.REQUEST_MESSAGES);
    assertEquals(req.payload, 10);
  }

  @SuppressWarnings("unchecked")
  @Test
  void deleteMessages() {
    ByteBuffer buffer = ByteBuffer.allocate(25);
    buffer.put((byte) 6);
    buffer.putInt(1);
    buffer.putInt(2);
    buffer.putInt(3);
    buffer.putInt(4);
    buffer.putInt(55);
    buffer.putInt(812);
    Request req = parseValid(Operation.DELETE_MESSAGES.getId(), buffer);
    assertEquals(req.operation, Operation.DELETE_MESSAGES);
    assertIterableEquals((List<Integer>) req.payload, List.of(1, 2, 3, 4, 55, 812));
  }

  @Test
  void deleteAccount() {
    ByteBuffer buffer = ByteBuffer.allocate(1);
    Request req = parseValid(Operation.DELETE_MESSAGES.getId(), buffer);
    assertEquals(req.operation, Operation.DELETE_MESSAGES);
  }

  @Test
  void lookupUserResponse() {
    AccountLookupResponse response = new AccountLookupResponse();
    response.exists = true;
    response.bcrypt_prefix = "1".repeat(29);
    ByteBuffer buffer = ByteBuffer.wrap(new WireProtocol().generateLookupUserResponse(response));
    assertEquals(Operation.LOOKUP_USER.getId(), buffer.get());
    assertEquals(1, buffer.get());
    assertEquals('1', buffer.get());
    AccountLookupResponse response2 = new AccountLookupResponse();
    response2.exists = false;
    ByteBuffer buffer2 = ByteBuffer.wrap(new WireProtocol().generateLookupUserResponse(response2));
    assertEquals(Operation.LOOKUP_USER.getId(), buffer2.get());
    assertEquals(0, buffer2.get());
  }

  @Test
  void loginResponse() {
    ByteBuffer buffer = ByteBuffer.wrap(new WireProtocol().generateLoginResponse(true, 5));
    assertEquals(Operation.LOGIN.getId(), buffer.get());
    assertEquals(1, buffer.get());
    assertEquals(0, buffer.get());
    assertEquals(5, buffer.get());
    ByteBuffer buffer2 = ByteBuffer.wrap(new WireProtocol().generateLoginResponse(false, 0));
    assertEquals(Operation.LOGIN.getId(), buffer2.get());
    assertEquals(0, buffer2.get());
  }

  @Test
  void createAccountResponse() {
    ByteBuffer buffer = ByteBuffer.wrap(new WireProtocol().generateCreateAccountResponse(true));
    assertEquals(Operation.CREATE_ACCOUNT.getId(), buffer.get());
    assertEquals(1, buffer.get());
    ByteBuffer buffer2 = ByteBuffer.wrap(new WireProtocol().generateCreateAccountResponse(false));
    assertEquals(Operation.CREATE_ACCOUNT.getId(), buffer2.get());
    assertEquals(0, buffer2.get());
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
    ByteBuffer buffer = ByteBuffer.wrap(new WireProtocol().generateListAccountsResponse(list));
    assertEquals(Operation.LIST_ACCOUNTS.getId(), buffer.get());
    assertEquals(2, buffer.get());
    assertEquals(1, buffer.getInt());
    assertEquals("june", getString(buffer, 1));
    assertEquals(2, buffer.getInt());
    assertEquals("catherine", getString(buffer, 1));
  }

  @Test
  void sendMessageResponse() {
    ByteBuffer buffer = ByteBuffer.wrap(new WireProtocol().generateSendMessageResponse(999999));
    assertEquals(Operation.SEND_MESSAGE.getId(), buffer.get());
    assertEquals(1, buffer.get());
    assertEquals(999999, buffer.getInt());
  }

  @Test
  void requestMessagesResponse() {
    List<MessageResponse> list = new ArrayList<>(2);
    MessageResponse m1 = new MessageResponse();
    m1.id = 1;
    m1.sender = "june";
    m1.message = "Hi!";
    MessageResponse m2 = new MessageResponse();
    m2.id = 2;
    m2.sender = "catherine";
    m2.message = "hi".repeat(9999);
    list.add(m1);
    list.add(m2);
    ByteBuffer buffer = ByteBuffer.wrap(new WireProtocol().generateRequestMessagesResponse(list));
    assertEquals(Operation.REQUEST_MESSAGES.getId(), buffer.get());
    assertEquals(2, buffer.get());
    assertEquals(1, buffer.getInt());
    assertEquals("june", getString(buffer, 1));
    assertEquals("Hi!", getString(buffer, 2));
    assertEquals(2, buffer.getInt());
    assertEquals("catherine", getString(buffer, 1));
    assertEquals(m2.message, getString(buffer, 2));
  }

  @Test
  void deleteMessageResponse() {
    ByteBuffer buffer = ByteBuffer.wrap(new WireProtocol().generateDeleteMessagesResponse(true));
    assertEquals(Operation.DELETE_MESSAGES.getId(), buffer.get());
    assertEquals(1, buffer.get());
    ByteBuffer buffer2 = ByteBuffer.wrap(new WireProtocol().generateDeleteMessagesResponse(false));
    assertEquals(Operation.DELETE_MESSAGES.getId(), buffer2.get());
    assertEquals(0, buffer2.get());
  }

  @Test
  void unexpectedFailure() {
    ByteBuffer buffer = ByteBuffer
        .wrap(new WireProtocol().generateUnexpectedFailureResponse(Operation.LIST_ACCOUNTS, "example"));
    assertEquals(-1, buffer.get());
    assertEquals(Operation.LIST_ACCOUNTS.getId(), buffer.get());
    assertEquals("example", getString(buffer, 2));
  }
}
