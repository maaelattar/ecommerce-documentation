# 03: `TransactionManagementService`

The `TransactionManagementService` is responsible for creating, updating, and managing the lifecycle of `Transaction` entities. It acts as a specialized repository or data access service with added business logic to ensure that all payment operations are accurately recorded and auditable.

## Responsibilities

1.  **Transaction Creation**: 
    *   Provides methods to create new `Transaction` records associated with a parent `Payment`.
    *   Ensures all required fields are populated (e.g., `paymentId`, `type`, `amount`, `currency`, initial `status`).
    *   Examples:
        *   `createAuthorizationTransaction(payment: Payment, amount: number, gatewayDetails?: object): Promise<Transaction>`
        *   `createCaptureTransaction(payment: Payment, authorizationTransaction: Transaction, amount: number, gatewayDetails?: object): Promise<Transaction>`
        *   `createSaleTransaction(payment: Payment, amount: number, gatewayDetails?: object): Promise<Transaction>`
        *   `createRefundTransactionRecord(payment: Payment, refund: Refund, amount: number, gatewayDetails?: object): Promise<Transaction>` (Note: This is for the `Transaction` of type `REFUND`, distinct from the `Refund` entity itself).

2.  **Transaction Updates**: 
    *   Provides methods to update the status and details of existing `Transaction` records based on gateway responses or other events.
    *   Example: `updateTransactionStatus(transactionId: string, newStatus: TransactionStatus, gatewayResponse?: object): Promise<Transaction>`
    *   Updates fields like `gatewayTransactionId`, `status`, `gatewayResponseCode`, `gatewayResponseMessage`, `processedAt`.

3.  **Data Integrity**: 
    *   Ensures consistency between `Transaction` records and their parent `Payment` (e.g., sum of successful captures should reconcile with payment amount).
    *   May include logic to prevent invalid state transitions for a transaction.

4.  **Querying Transactions**: 
    *   Offers methods to retrieve transaction history for a specific payment.
    *   Example: `getTransactionsForPayment(paymentId: string): Promise<Transaction[]>`
    *   May provide methods for more complex queries if needed (e.g., finding all failed authorization attempts in the last hour).

5.  **Linking Related Transactions**: 
    *   Manages the `parentTransactionId` field to link related transactions (e.g., ensuring a `CAPTURE` transaction correctly references its preceding `AUTHORIZATION` transaction).

## Interactions with Other Services

*   **`PaymentProcessingService`**: This is the primary consumer. It calls the `TransactionManagementService` to record the outcome of various stages in the payment processing flow.
*   **`RefundService`**: Uses this service to create `Transaction` records of type `REFUND` when a refund is processed.
*   **`WebhookHandlerService`**: May use this service to update transaction statuses based on asynchronous notifications from payment gateways (e.g., if a pending capture is confirmed or a refund is settled).
*   **Database (via ORM)**: Directly interacts with the database to persist and retrieve `Transaction` entities using TypeORM.

## Key Operations (Conceptual)

*   `recordNewTransaction(details: { paymentId: string; type: TransactionType; amount: number; currency: string; status: TransactionStatus; gatewayTransactionId?: string; gatewayResponse?: object; parentTransactionId?: string; }): Promise<Transaction>`
*   `updateTransactionDetails(transactionId: string, updates: { status?: TransactionStatus; gatewayTransactionId?: string; gatewayResponseCode?: string; gatewayResponseMessage?: string; processedAt?: Date; }): Promise<Transaction>`
*   `findTransactionById(transactionId: string): Promise<Transaction | null>`
*   `findTransactionsByPaymentId(paymentId: string): Promise<Transaction[]>`
*   `findTransactionByGatewayId(gateway: string, gatewayTransactionId: string): Promise<Transaction | null>` (Useful for webhook processing)

## Design Considerations

*   **Atomicity**: When creating a transaction record as part of a larger operation (e.g., processing a payment), this service's methods should be called within the same database transaction to ensure atomicity. For example, if a payment intent is successfully created at the gateway, both the `Payment` entity update and the new `Transaction` record creation should succeed or fail together.
*   **Audit Trail**: This service is fundamental to maintaining a detailed and accurate audit trail of all payment operations.
*   **Error Logging**: Should ensure that any errors from the gateway or processor are accurately logged within the `Transaction` record itself (e.g., in `gatewayResponseMessage`, `processorResponseMessage`).
*   **Clarity of Purpose**: This service should focus solely on the `Transaction` entity and its lifecycle. Broader payment orchestration logic resides in `PaymentProcessingService`.

The `TransactionManagementService` ensures that every step and outcome in the payment lifecycle is meticulously recorded, which is vital for financial accuracy, operational visibility, and resolving disputes.
