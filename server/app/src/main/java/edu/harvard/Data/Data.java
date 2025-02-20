package edu.harvard.Data;

public class Data {
  // Internal data types (stored in database)
  public static class Account {
    public int id;
    public String username;
    public String password_hash;
    public String client_bcrypt_prefix;
  }

  public static class Message {
    public int id;
    public int sender_id;
    public int recipient_id;
    public String message;
    public boolean read;
  }
}
