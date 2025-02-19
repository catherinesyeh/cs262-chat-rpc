package edu.harvard.Logic;

import org.junit.jupiter.api.Test;

import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Data.ListAccountsRequest;
import edu.harvard.Data.Data.LoginCreateRequest;
import edu.harvard.Data.Data.MessageResponse;
import edu.harvard.Data.Data.SendMessageRequest;
import edu.harvard.Data.Protocol.HandleException;
import edu.harvard.Logic.OperationHandler.LoginResponse;

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
      LoginCreateRequest u1 = new LoginCreateRequest();
      u1.username = "june";
      u1.password_hash = "passwordpasswordpasswordpasswordpasswordpasswordpassword";
      LoginCreateRequest u2 = new LoginCreateRequest();
      u2.username = "catherine";
      u2.password_hash = "password2passwordpasswordpasswordpasswordpasswordpassword";
      assertEquals(1, handler.createAccount(u1));
      assertEquals(2, handler.createAccount(u2));
      // Log into one
      AccountLookupResponse lookup = handler.lookupAccount("june");
      assertEquals(true, lookup.exists);
      assertEquals(29, lookup.bcrypt_prefix.length());
      LoginResponse login = handler.login(u1);
      assertEquals(true, login.success);
      assertEquals(1, login.account_id);
      assertEquals(0, login.unread_messages);
      // List accounts
      ListAccountsRequest listRequest1 = new ListAccountsRequest();
      listRequest1.maximum_number = 1;
      listRequest1.offset_account_id = 0;
      listRequest1.filter_text = "";
      List<Account> accountList = handler.listAccounts(listRequest1);
      assertEquals(accountList.get(0).username, u1.username);
      assertEquals(1, accountList.size());
      ListAccountsRequest listRequest2 = new ListAccountsRequest();
      listRequest2.maximum_number = 1;
      listRequest2.offset_account_id = 1;
      listRequest2.filter_text = "";
      List<Account> accountList2 = handler.listAccounts(listRequest2);
      assertEquals(accountList2.get(0).username, u2.username);
      ListAccountsRequest listRequest3 = new ListAccountsRequest();
      listRequest3.maximum_number = 1;
      listRequest3.offset_account_id = 0;
      listRequest3.filter_text = "c";
      List<Account> accountList3 = handler.listAccounts(listRequest3);
      assertEquals(accountList3.get(0).username, u2.username);
      // Send a message
      SendMessageRequest msg = new SendMessageRequest();
      msg.recipient = "catherine";
      msg.message = "Hi!";
      assertEquals(1, handler.sendMessage(1, msg));
      SendMessageRequest msg2 = new SendMessageRequest();
      msg2.recipient = "june";
      msg2.message = "Hi!";
      assertThrows(HandleException.class, () -> handler.sendMessage(1, msg2));
      SendMessageRequest msg3 = new SendMessageRequest();
      msg3.recipient = "unknown";
      msg3.message = "Hi!";
      assertThrows(HandleException.class, () -> handler.sendMessage(1, msg3));
      // Receive a message
      LoginResponse login2 = handler.login(u2);
      assertEquals(1, login2.unread_messages);
      MessageResponse m = handler.requestMessages(2, 5).get(0);
      assertEquals(1, m.id);
      assertEquals("june", m.sender);
      assertEquals(msg.message, m.message);
      // Delete it
      assertEquals(true, handler.deleteMessages(2, Arrays.asList(1)));
      // Send another message
      assertEquals(1, handler.sendMessage(1, msg));
      // Delete it
      assertEquals(false, handler.deleteMessages(3, Arrays.asList(1)));
      assertEquals(true, handler.deleteMessages(1, Arrays.asList(1)));
      // Verify that this worked
      assertEquals(0, handler.requestMessages(2, 5).size());
      // Delete an account
      handler.deleteAccount(1);
    } catch (HandleException e) {
      throw new RuntimeException(e.getMessage());
    }
  }
}
