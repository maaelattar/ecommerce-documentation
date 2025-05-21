# 09: Banking and Settlement Systems Integration

The Payment Service itself typically **does not directly integrate** with banking systems for the purpose of settling funds or managing bank accounts. This complex and highly regulated area is primarily handled by the external payment gateways (e.g., Stripe, PayPal, Adyen) that the Payment Service uses.

## Role of Payment Gateways in Settlement

1.  **Fund Collection**: When the Payment Service processes a successful payment via a gateway, the gateway collects the funds from the customer's bank (via card networks, ACH, etc.).
2.  **Merchant Account**: The e-commerce business maintains a merchant account with the payment gateway (or an acquiring bank facilitated by the gateway).
3.  **Settlement to Merchant Bank Account**: The payment gateway aggregates funds collected from multiple transactions and, after deducting its fees, periodically settles (transfers) these funds into the e-commerce company's designated business bank account.
    *   Settlement frequency (e.g., daily, weekly, monthly) and procedures are defined by the agreement with the payment gateway.
4.  **Reporting by Gateway**: Payment gateways provide detailed reports (often via a dashboard and API) on:
    *   Individual transactions processed.
    *   Fees deducted.
    *   Settlement batches (payouts) made to the merchant's bank account.
    *   Chargebacks and disputes.

## Payment Service Role in Facilitating Reconciliation

While the Payment Service doesn't handle the bank transfers, the data it records is **crucial for the e-commerce company's finance team to perform reconciliation**:

1.  **Transaction Data Source**: The Payment Service (its database and event stream) provides a comprehensive record of all successful payments, refunds, and their amounts as processed by the platform.
    *   This includes `paymentId`, `orderId`, `gatewayTransactionId`, `amount`, `currency`, `timestamp`.
2.  **Matching Records**: The finance team uses data from the Payment Service to reconcile against:
    *   Settlement reports provided by the payment gateways.
    *   Bank statements showing incoming deposits from gateways.
3.  **Identifying Discrepancies**: This reconciliation helps identify:
    *   Missing transactions.
    *   Discrepancies in amounts.
    *   Timing differences between transaction processing and settlement.
    *   Correctness of gateway fees.
    *   Unresolved chargebacks or refunds affecting settlement amounts.

## Integration Points (Indirect)

*   **Reporting/Analytics Service (Consumer of Payment Data)**: As detailed in `05-reporting-analytics-integration.md`, the Reporting/Analytics service consumes data from the Payment Service. This analytical data store is often the source used by finance teams (via BI tools or direct queries) for reconciliation tasks.
*   **Finance Systems/ERPs**: The reconciled data, or raw data from the analytical store, may be fed into the company's financial accounting systems or ERP (Enterprise Resource Planning) software.

## No Direct API Calls to Banks by Payment Service

*   The Payment Service **does not** make API calls to banking systems for initiating payouts or checking bank balances. This is outside its scope and handled by the gateways and internal finance processes.
*   Exposing banking credentials or direct bank API access to the Payment Service would significantly increase its security risk and compliance burden (e.g., potentially bringing more of the system into PCI DSS scope or other financial regulations).

**Conclusion**: The integration with banking and settlement systems is an indirect one, facilitated by the data captured and made available by the Payment Service. The actual movement of funds and direct bank interactions are managed by the payment gateways and the company's finance department. The Payment Service plays a vital role by providing the accurate, detailed transaction records needed for these financial operations and reconciliation processes.
