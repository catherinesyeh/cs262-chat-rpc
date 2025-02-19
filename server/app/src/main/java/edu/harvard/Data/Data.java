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

  // Multipart request/response types
  public static class AccountLookupResponse {
    public boolean exists;
    public String bcrypt_prefix;
  }

  public static class LoginCreateRequest {
    public String username;
    public String password_hash;
  }

  public static class ListAccountsRequest {
    public int maximum_number;
    public int offset_account_id;
    public String filter_text;
  }

  public static class SendMessageRequest {
    public String recipient;
    public String message;
  }

  public static class MessageResponse {
    public int id;
    public String sender;
    public String message;
  }
}
