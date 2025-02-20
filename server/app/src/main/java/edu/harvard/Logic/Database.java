package edu.harvard.Logic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.Message;

/*
 * Properly-synchronized in-memory datastore.
 * Methods are designed specifically to meet application needs.
 * Higher-level application logic will take place outside the database.
 */
public class Database {
  private Map<Integer, Account> accountMap;
  private Map<String, Integer> accountUsernameMap;
  private Map<Integer, Message> messageMap;

  // Optimization for getting unread messages
  private Map<Integer, ArrayList<Integer>> unreadMessagesPerAccount;

  // Session keys for currently logged in users.
  private Map<String, Integer> sessions;

  public Database() {
    accountMap = new HashMap<>();
    accountUsernameMap = new HashMap<>();
    messageMap = new HashMap<>();
    unreadMessagesPerAccount = new HashMap<>();
    sessions = new HashMap<>();
  }

  public synchronized Account lookupAccount(int id) {
    return accountMap.get(id);
  }

  public synchronized Account lookupAccountByUsername(String username) {
    return accountMap.get(accountUsernameMap.get(username));
  }

  public synchronized String createSession(int id) {
    String key = UUID.randomUUID().toString();
    sessions.put(key, id);
    return key;
  }

  public synchronized Integer getSession(String key) {
    return sessions.get(key);
  }

  /*
   * Verifies username is not taken. Returns account ID: 0 means failure.
   */
  public synchronized int createAccount(Account account) {
    if (accountUsernameMap.get(account.username) != null) {
      return 0;
    }
    Integer next_id = accountMap.size() == 0 ? 1 : Collections.max(accountMap.keySet()) + 1;
    account.id = next_id;
    accountMap.put(next_id, account);
    accountUsernameMap.put(account.username, next_id);
    return next_id;
  }

  public synchronized Collection<Account> getAllAccounts() {
    return accountMap.values();
  }

  /*
   * Adds a message to the database.
   * If message.read is false, also adds it to a user's unread list.
   */
  public synchronized int createMessage(Message message) {
    Integer next_id = messageMap.size() == 0 ? 1 : Collections.max(messageMap.keySet()) + 1;
    message.id = next_id;
    messageMap.put(next_id, message);
    if (!message.read) {
      List<Integer> unreads = unreadMessagesPerAccount.get(message.recipient_id);
      if (unreads != null) {
        unreads.add(next_id);
      } else {
        unreadMessagesPerAccount.put(message.recipient_id, new ArrayList<>(Arrays.asList(next_id)));
      }
    }
    return next_id;
  }

  public synchronized int getUnreadMessageCount(int user_id) {
    ArrayList<Integer> unreads = unreadMessagesPerAccount.get(user_id);
    if (unreads == null) {
      return 0;
    }
    return unreads.size();
  }

  public synchronized Message getMessage(int id) {
    return messageMap.get(id);
  }

  /*
   * Gets the first [number] unread messages for a user, and marks them as read
   */
  public synchronized List<Message> getUnreadMessages(int user_id, int number) {
    ArrayList<Message> list = new ArrayList<>(number);
    ArrayList<Integer> unreads = unreadMessagesPerAccount.get(user_id);
    if (unreads == null) {
      return list;
    }
    for (int i = 0; i < number; i++) {
      if (unreads.size() > 0) {
        int id = unreads.remove(0);
        Message m = messageMap.get(id);
        m.read = true;
        list.add(m);
      } else {
        break;
      }
    }
    return list;
  }

  /*
   * Verification that the user can delete this message must take place in
   * higher-level logic.
   */
  public synchronized void deleteMessage(int id) {
    Message m = messageMap.get(id);
    if (m != null) {
      // Integer cast ensures the correct variant of remove is used
      if (!m.read) {
        unreadMessagesPerAccount.get(m.recipient_id).remove((Integer) id);
      }
      messageMap.remove(id);
    }
  }

  /*
   * The username remains claimed.
   */
  public synchronized void deleteAccount(int id) {
    unreadMessagesPerAccount.remove(id);
    accountMap.remove(id);
  }
}
