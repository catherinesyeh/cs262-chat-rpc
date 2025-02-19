package edu.harvard.Logic;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import edu.harvard.Data.Data;

public class DatabaseTest {
  Data.Message buildMessage(int sender_id, int recipient_id, boolean read, String message) {
    Data.Message m = new Data.Message();
    m.sender_id = sender_id;
    m.recipient_id = recipient_id;
    m.read = read;
    m.message = message;
    return m;
  }

  @Test
  void accountOperationsWork() {
    Data.Account a1 = new Data.Account();
    a1.username = "june";
    a1.password_hash = "test1";
    Data.Account a2 = new Data.Account();
    a2.username = "catherine";
    a2.password_hash = "test2";

    Database db = new Database();
    assertEquals(1, db.createAccount(a1));
    // duplicate should not work
    assertEquals(0, db.createAccount(a1));
    assertEquals(db.getAllAccounts().size(), 1);
    assertNull(db.lookupAccountByUsername(a2.username));
    assertEquals(db.lookupAccount(1).username, a1.username);
    assertEquals(db.lookupAccount(1).password_hash, a1.password_hash);
    assertEquals(db.lookupAccount(1).id, 1);
    assertEquals(2, db.createAccount(a2));
    assertEquals(db.getAllAccounts().size(), 2);
    assertEquals(db.lookupAccountByUsername(a2.username).username, a2.username);
    assertEquals(db.lookupAccount(2).username, a2.username);
    assertEquals(db.getUnreadMessages(2, 10).size(), 0);
    db.deleteAccount(1);
    assertEquals(db.getAllAccounts().size(), 1);
    assertEquals(db.getAllAccounts().iterator().next().username, a2.username);
    // be sure username stays claimed, but that lookups don't work
    assertEquals(0, db.createAccount(a1));
    assertNull(db.lookupAccountByUsername("june"));
  }

  @Test
  void messageOperationsWork() {
    Data.Account a1 = new Data.Account();
    a1.username = "june";
    a1.password_hash = "test1";
    Data.Account a2 = new Data.Account();
    a2.username = "catherine";
    a2.password_hash = "test2";
    // Create the same message a lot so we can send it repeatedly
    Data.Message m1 = buildMessage(1, 2, false, "message!");
    Data.Message m2 = buildMessage(1, 2, false, "message!");
    Data.Message m3 = buildMessage(1, 2, false, "message!");
    Data.Message m4 = buildMessage(1, 2, false, "message!");
    Data.Message m5 = buildMessage(1, 2, false, "message!");
    Data.Message m6 = buildMessage(1, 2, false, "message!");
    Data.Message m7 = buildMessage(1, 2, false, "message!");
    Data.Message m8 = buildMessage(1, 2, false, "message!");
    Data.Message m9 = buildMessage(1, 2, true, "message!");

    Database db = new Database();
    assertEquals(1, db.createAccount(a1));
    assertEquals(2, db.createAccount(a2));
    // Send message once
    db.createMessage(m1);
    assertEquals(db.getUnreadMessages(2, 1).getFirst().message, m1.message);
    assertEquals(db.getUnreadMessages(2, 1).size(), 0);
    assertEquals(db.getUnreadMessages(1, 1).size(), 0);
    // Send message repeatedly
    db.createMessage(m2);
    db.createMessage(m3);
    db.createMessage(m4);
    db.createMessage(m5);
    db.createMessage(m6);
    db.createMessage(m7);
    assertEquals(db.getUnreadMessageCount(2), 6);
    assertEquals(db.getUnreadMessages(2, 1).size(), 1);
    assertEquals(db.getUnreadMessages(2, 3).size(), 3);
    assertEquals(db.getUnreadMessages(2, 10).size(), 2);
    assertEquals(db.getUnreadMessages(2, 10).size(), 0);
    // Test delete
    db.createMessage(m8);
    db.deleteMessage(8);
    assertEquals(db.getUnreadMessages(2, 10).size(), 0);
    // Test already-read message
    int id = db.createMessage(m9);
    assertEquals(db.getUnreadMessages(2, 10).size(), 0);
    assertNotNull(db.getMessage(id));
  }

}
