package edu.harvard.Logic;

import org.junit.jupiter.api.Test;

import edu.harvard.Chat.Account;
import edu.harvard.Chat.AccountLookupResponse;
import edu.harvard.Chat.ListAccountsRequest;
import edu.harvard.Chat.LoginCreateRequest;
import edu.harvard.Chat.LoginCreateResponse;
import edu.harvard.Chat.ChatMessage;
import edu.harvard.Chat.SendMessageRequest;
import edu.harvard.Logic.OperationHandler.HandleException;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Arrays;
import java.util.List;

public class OperationHandlerTest {
  @Test
  void operationTest() {
    try {
      Database db = new Database();
      OperationHandler handler = new OperationHandler(db);
      // Create two accounts
      LoginCreateRequest u1 = LoginCreateRequest.newBuilder().setUsername("june")
          .setPasswordHash("passwordpasswordpasswordpasswordpasswordpasswordpassword").build();
      LoginCreateRequest u2 = LoginCreateRequest.newBuilder().setUsername("catherine")
          .setPasswordHash("password2passwordpasswordpasswordpasswordpasswordpassword").build();
      assertEquals(1, handler.lookupSession(handler.createAccount(u1).getSessionKey()));
      assertEquals(2, handler.lookupSession(handler.createAccount(u2).getSessionKey()));
      // Log into one
      AccountLookupResponse lookup = handler.lookupAccount("june");
      assertEquals(true, lookup.getExists());
      assertEquals(29, lookup.getBcryptPrefix().length());
      LoginCreateResponse login = handler.login(u1);
      assertEquals(true, login.getSuccess());
      assertEquals(0, login.getUnreadMessages());
      assertTrue(login.getSessionKey().length() > 0);
      assertEquals(1, handler.lookupSession(login.getSessionKey()));
      // List accounts
      ListAccountsRequest listRequest1 = ListAccountsRequest.newBuilder().setMaximumNumber(1).setOffsetAccountId(0)
          .setFilterText("").build();
      List<Account> accountList = handler.listAccounts(listRequest1).getAccountsList();
      assertEquals(accountList.get(0).getUsername(), u1.getUsername());
      assertEquals(1, accountList.size());
      ListAccountsRequest listRequest2 = ListAccountsRequest.newBuilder().setMaximumNumber(1).setOffsetAccountId(1)
          .setFilterText("").build();
      List<Account> accountList2 = handler.listAccounts(listRequest2).getAccountsList();
      assertEquals(accountList2.get(0).getUsername(), u2.getUsername());
      ListAccountsRequest listRequest3 = ListAccountsRequest.newBuilder().setMaximumNumber(1).setOffsetAccountId(1)
          .setFilterText("c").build();
      List<Account> accountList3 = handler.listAccounts(listRequest3).getAccountsList();
      assertEquals(accountList3.get(0).getUsername(), u2.getUsername());
      // Send a message
      SendMessageRequest msg = SendMessageRequest.newBuilder().setRecipient("catherine").setMessage("Hi!").build();
      assertEquals(1, handler.sendMessage(1, msg));
      SendMessageRequest msg2 = SendMessageRequest.newBuilder().setRecipient("june").setMessage("Hi!").build();
      assertThrows(HandleException.class, () -> handler.sendMessage(1, msg2));
      SendMessageRequest msg3 = SendMessageRequest.newBuilder().setRecipient("unknown").setMessage("Hi!").build();
      assertThrows(HandleException.class, () -> handler.sendMessage(1, msg3));
      // Receive a message
      LoginCreateResponse login2 = handler.login(u2);
      assertEquals(1, login2.getUnreadMessages());
      ChatMessage m = handler.requestMessages(2, 5).getMessagesList().get(0);
      assertEquals(1, m.getId());
      assertEquals("june", m.getSender());
      assertEquals(msg.getMessage(), m.getMessage());
      // Delete it
      assertEquals(true, handler.deleteMessages(2, Arrays.asList(1)));
      // Send another message
      assertEquals(1, handler.sendMessage(1, msg));
      // Delete it
      assertEquals(false, handler.deleteMessages(3, Arrays.asList(1)));
      assertEquals(true, handler.deleteMessages(1, Arrays.asList(1)));
      // Verify that this worked
      assertEquals(0, handler.requestMessages(2, 5).getMessagesList().size());
      // Delete an account
      handler.deleteAccount(1);
    } catch (HandleException e) {
      throw new RuntimeException(e.getMessage());
    }
  }
}
