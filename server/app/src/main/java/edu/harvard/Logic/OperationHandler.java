package edu.harvard.Logic;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import at.favre.lib.crypto.bcrypt.BCrypt;
import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.Message;
import edu.harvard.Chat;
import edu.harvard.Chat.AccountLookupResponse;
import edu.harvard.Chat.LoginCreateRequest;
import edu.harvard.Chat.LoginCreateResponse;
import edu.harvard.Chat.RequestMessagesResponse;
import edu.harvard.Chat.ListAccountsRequest;
import edu.harvard.Chat.ListAccountsResponse;
import edu.harvard.Chat.ChatMessage;
import edu.harvard.Chat.SendMessageRequest;

/*
 * Higher-level logic for all operations.
 */
public class OperationHandler {
  // Custom exception, caught in AppThread to generate failure responses
  public class HandleException extends Exception {
    public HandleException(String errorMessage) {
      super(errorMessage);
    }
  }

  private Database db;

  public OperationHandler(Database db) {
    this.db = db;
  }

  public Integer lookupSession(String key) {
    return db.getSession(key);
  }

  public AccountLookupResponse lookupAccount(String username) {
    AccountLookupResponse.Builder response = AccountLookupResponse.newBuilder();
    Account account = db.lookupAccountByUsername(username);
    if (account == null) {
      response.setExists(false);
      return response.build();
    }
    response.setExists(true);
    response.setBcryptPrefix(account.client_bcrypt_prefix);
    return response.build();
  }

  public LoginCreateResponse createAccount(LoginCreateRequest request) throws HandleException {
    Account account = new Account();
    try {
      account.client_bcrypt_prefix = request.getPasswordHash().substring(0, 29);
    } catch (Exception e) {
      throw new HandleException("Invalid password hash!");
    }
    account.username = request.getUsername();
    account.password_hash = BCrypt.withDefaults().hashToString(12, request.getPasswordHash().toCharArray());
    int id = db.createAccount(account);
    if (id != 0) {
      String key = db.createSession(account.id);
      return LoginCreateResponse.newBuilder().setSuccess(true).setUnreadMessages(0).setSessionKey(key).build();
    } else {
      return LoginCreateResponse.newBuilder().setSuccess(false).build();
    }
  }

  public LoginCreateResponse login(LoginCreateRequest request) {
    LoginCreateResponse.Builder response = LoginCreateResponse.newBuilder();
    // Get account
    Account account = db.lookupAccountByUsername(request.getUsername());
    if (account == null) {
      response.setSuccess(false);
      return response.build();
    }
    BCrypt.Result result = BCrypt.verifyer().verify(request.getPasswordHash().toCharArray(), account.password_hash);
    if (!result.verified) {
      response.setSuccess(false);
      return response.build();
    }
    String key = db.createSession(account.id);
    int unreadCount = db.getUnreadMessageCount(account.id);
    response.setSuccess(true);
    response.setUnreadMessages(unreadCount);
    response.setSessionKey(key);
    return response.build();
  }

  public ListAccountsResponse listAccounts(ListAccountsRequest request) {
    ArrayList<Account> list = new ArrayList<>(request.getMaximumNumber());
    Collection<Account> allAccounts = db.getAllAccounts();
    for (Account account : allAccounts) {
      boolean include = true;
      if (account.id <= request.getOffsetAccountId()) {
        include = false;
      }
      if (!account.username.contains(request.getFilterText())) {
        include = false;
      }
      if (include) {
        list.add(account);
      }
      if (list.size() >= request.getMaximumNumber()) {
        break;
      }
    }
    List<Chat.Account> responseList = new ArrayList<>(list.size());
    for (Account a : list) {
      responseList.add(Chat.Account.newBuilder().setId(a.id).setUsername(a.username).build());
    }
    return ListAccountsResponse.newBuilder().addAllAccounts(responseList).build();
  }

  public int sendMessage(int sender_id, SendMessageRequest request) throws HandleException {
    // Look up sender
    Account sender = db.lookupAccount(sender_id);
    if (sender == null) {
      throw new HandleException("Sender does not exist!");
    }
    // Look up recipient
    Account account = db.lookupAccountByUsername(request.getRecipient());
    if (account == null) {
      throw new HandleException("Recipient does not exist!");
    }
    if (account.id == sender_id) {
      throw new HandleException("You cannot message yourself!");
    }
    // Build Message
    Message m = new Message();
    m.message = request.getMessage();
    m.recipient_id = account.id;
    m.sender_id = sender_id;
    m.read = false;
    int id = db.createMessage(m);
    return id;
  }

  public RequestMessagesResponse requestMessages(int user_id, int maximum_number) {
    List<Message> unreadMessages = db.getUnreadMessages(user_id, maximum_number);
    ArrayList<ChatMessage> responseMessages = new ArrayList<>(unreadMessages.size());
    for (Message message : unreadMessages) {
      ChatMessage.Builder messageResponse = ChatMessage.newBuilder();
      messageResponse.setId(message.id);
      messageResponse.setMessage(message.message);
      messageResponse.setSender(db.lookupAccount(message.sender_id).username);
      responseMessages.add(messageResponse.build());
    }
    return RequestMessagesResponse.newBuilder().addAllMessages(responseMessages).build();
  }

  // returns success boolean
  public boolean deleteMessages(int user_id, List<Integer> ids) {
    for (Integer i : ids) {
      Message m = db.getMessage(i);
      if (m.recipient_id != user_id && m.sender_id != user_id) {
        return false;
      }
      db.deleteMessage(i);
    }
    return true;
  }

  public void deleteAccount(int user_id) {
    db.deleteAccount(user_id);
  }
}
