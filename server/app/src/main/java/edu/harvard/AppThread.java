package edu.harvard;

import java.io.IOException;
import java.net.Socket;
import java.util.List;

import edu.harvard.Data.JSONProtocol;
import edu.harvard.Data.Protocol;
import edu.harvard.Data.WireProtocol;
import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.ListAccountsRequest;
import edu.harvard.Data.Data.LoginCreateRequest;
import edu.harvard.Data.Data.MessageResponse;
import edu.harvard.Data.Data.SendMessageRequest;
import edu.harvard.Data.Protocol.Operation;
import edu.harvard.Data.Protocol.Request;
import edu.harvard.Logic.Database;
import edu.harvard.Logic.OperationHandler;
import edu.harvard.Logic.OperationHandler.LoginResponse;

public class AppThread extends Thread {
  private Socket socket = null;
  private Database db = null;
  private int logged_in_account = 0;

  public AppThread(Socket socket, Database db) {
    super("AppThread");
    this.socket = socket;
    this.db = db;
  }

  // returns true if the client is not logged in
  private boolean validateLogin(Protocol protocol, Operation operation) throws IOException {
    if (logged_in_account == 0) {
      socket.getOutputStream().write(protocol.generateUnexpectedFailureResponse(operation, "You are not logged in!"));
      return true;
    }
    return false;
  }

  public void run() {
    System.out.println("New connection from " + socket.getInetAddress().toString());
    while (true) {
      int firstByte = 0;
      Protocol protocol = null;
      try {
        // Choose a protocol layer: JSON or wire
        firstByte = socket.getInputStream().read();
        if (firstByte == -1) {
          socket.close();
          break;
        }

        if (firstByte == 123) {
          // First byte is {, parse as JSON request
          protocol = new JSONProtocol();
        } else {
          protocol = new WireProtocol();
        }

        // Parse the request
        Request request;
        try {
          request = protocol.parseRequest(firstByte, socket.getInputStream());
        } catch (Protocol.ParseException e) {
          socket.getOutputStream()
              .write(protocol.generateUnexpectedFailureResponse(Operation.UNKNOWN, e.getMessage()));
          continue;
        }

        // Handle the request
        synchronized (socket) {
          try {
            OperationHandler handler = new OperationHandler(db);
            switch (request.operation) {
              case LOOKUP_USER:
                continue;
              case LOGIN:
                LoginResponse loginResponse = handler.login((LoginCreateRequest) request.payload);
                if (loginResponse.success) {
                  this.logged_in_account = loginResponse.account_id;
                  Database.SocketWithProtocol sp = new Database.SocketWithProtocol();
                  sp.socket = socket;
                  sp.protocol = protocol;
                  db.registerSocket(loginResponse.account_id, sp);
                }
                socket.getOutputStream()
                    .write(protocol.generateLoginResponse(loginResponse.success, loginResponse.unread_messages));
                continue;
              case CREATE_ACCOUNT:
                int id = handler.createAccount((LoginCreateRequest) request.payload);
                if (id != 0) {
                  this.logged_in_account = id;
                  Database.SocketWithProtocol sp = new Database.SocketWithProtocol();
                  sp.socket = socket;
                  sp.protocol = protocol;
                  db.registerSocket(id, sp);
                }
                socket.getOutputStream()
                    .write(protocol.generateCreateAccountResponse(id != 0));
                continue;
              case LIST_ACCOUNTS:
                if (validateLogin(protocol, request.operation)) {
                  continue;
                }
                List<Account> accounts = handler.listAccounts((ListAccountsRequest) request.payload);
                socket.getOutputStream()
                    .write(protocol.generateListAccountsResponse(accounts));
                continue;
              case SEND_MESSAGE:
                if (validateLogin(protocol, request.operation)) {
                  continue;
                }
                int message_id = handler.sendMessage(logged_in_account, (SendMessageRequest) request.payload);
                socket.getOutputStream()
                    .write(protocol.generateSendMessageResponse(message_id));
                continue;
              case REQUEST_MESSAGES:
                if (validateLogin(protocol, request.operation)) {
                  continue;
                }
                List<MessageResponse> messages = handler.requestMessages(logged_in_account, (int) request.payload);
                socket.getOutputStream()
                    .write(protocol.generateRequestMessagesResponse(messages));
                continue;
              case DELETE_MESSAGES:
                if (validateLogin(protocol, request.operation)) {
                  continue;
                }
                @SuppressWarnings("unchecked")
                boolean success = handler.deleteMessages(logged_in_account, (List<Integer>) request.payload);
                socket.getOutputStream()
                    .write(protocol.generateDeleteMessagesResponse(success));
                continue;
              case DELETE_ACCOUNT:
                if (validateLogin(protocol, request.operation)) {
                  continue;
                }
                handler.deleteAccount(logged_in_account);
                socket.close();
                return;
              default:
                throw new Protocol.HandleException("Operation not implemented: " + request.operation.toString());
            }
          } catch (Protocol.HandleException e) {
            socket.getOutputStream()
                .write(protocol.generateUnexpectedFailureResponse(request.operation, e.getMessage()));
            continue;
          }
        }
      } catch (IOException e) {
        try {
          socket.close();
        } catch (IOException e2) {
        }
        System.err.println("Unexpected I/O error in main thread:");
        if (protocol != null) {
          protocol.generateUnexpectedFailureResponse(Operation.codeToOperation(firstByte),
              "Unexpected error in handling request!");
        }
        e.printStackTrace();
        break;
      }
    }
  }
}
