package edu.harvard.Data;

import java.io.InputStream;
import java.util.List;

import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Data.MessageResponse;

/*
 * Generic protocol interface. This allows the JSON and wire protocols to be swapped easily.
 */
public interface Protocol {
  // Custom exceptions, caught in AppThread to generate failure responses
  public class ParseException extends Exception {
    public ParseException(String errorMessage) {
      super(errorMessage);
    }
  }

  public class HandleException extends Exception {
    public HandleException(String errorMessage) {
      super(errorMessage);
    }
  }

  public enum Operation {
    UNKNOWN(0),
    LOOKUP_USER(1),
    LOGIN(2),
    CREATE_ACCOUNT(3),
    LIST_ACCOUNTS(4),
    SEND_MESSAGE(5),
    REQUEST_MESSAGES(6),
    DELETE_MESSAGES(7),
    DELETE_ACCOUNT(8);

    private final int id;

    Operation(int id) {
      this.id = id;
    }

    int getId() {
      return id;
    }

    public static Operation codeToOperation(int operation_code) {
      switch (operation_code) {
        case 1:
          return Operation.LOOKUP_USER;
        case 2:
          return Operation.LOGIN;
        case 3:
          return Operation.CREATE_ACCOUNT;
        case 4:
          return Operation.LIST_ACCOUNTS;
        case 5:
          return Operation.SEND_MESSAGE;
        case 6:
          return Operation.REQUEST_MESSAGES;
        case 7:
          return Operation.DELETE_MESSAGES;
        case 8:
          return Operation.DELETE_ACCOUNT;
        default:
          return Operation.UNKNOWN;
      }
    }
  }

  /*
   * Contains an Operation enum code and an arbitrary payload.
   * Casting is required to transform the payload into its proper value -
   * this is needed because parseRequest must be called without knowing
   * what operation is being parsed! The Operation value can then be used
   * to correctly cast the payload and act on it.
   * 
   * Payload types:
   * LOOKUP_USER: String (username)
   * LOGIN: LoginCreateRequest
   * CREATE_ACCOUNT: LoginCreateRequest
   * LIST_ACCOUNTS: ListAccountsRequest
   * SEND_MESSAGE: SendMessageRequest
   * REQUEST_MESSAGES: int (maximum number)
   * DELETE_MESSAGES: List<int> (list of message IDs)
   * DELETE_ACCOUNT: null
   */
  public static class Request {
    public Operation operation;
    public Object payload;
  }

  // Input parsing
  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException;

  // Output building
  public byte[] generateLookupUserResponse(AccountLookupResponse internalResponse);

  public byte[] generateLoginResponse(boolean success, int unread_messages);

  public byte[] generateCreateAccountResponse(boolean success);

  public byte[] generateListAccountsResponse(List<Account> accounts);

  public byte[] generateSendMessageResponse(int message_id);

  public byte[] generateRequestMessagesResponse(List<MessageResponse> messages);

  public byte[] generateDeleteMessagesResponse(boolean success);

  public byte[] generateUnexpectedFailureResponse(Operation operation, String message);
}
