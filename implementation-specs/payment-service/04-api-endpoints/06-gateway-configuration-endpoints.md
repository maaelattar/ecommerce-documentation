# 06: Gateway Configuration Endpoints (Admin - Optional)

These endpoints are optional and would only be implemented if there's a requirement for administrators to manage certain aspects of payment gateway configurations dynamically through an API. **It is critical to note that highly sensitive credentials like API secret keys or webhook signing secrets SHOULD NOT be managed or exposed via these APIs.** Such secrets should be managed via secure deployment environment variables, Kubernetes Secrets, or a dedicated secrets management system (e.g., HashiCorp Vault).

If implemented, these endpoints would be strictly for administrative use with robust authentication and authorization.

## Potential Use Cases (Non-Sensitive Configurations)

*   Enabling or disabling a specific payment gateway for use by the platform.
*   Setting preferences for a gateway, such as default payment method types to offer.
*   Updating non-sensitive parameters like descriptive names, region-specific settings (if applicable), or perhaps thresholds for certain internal logic related to a gateway.
*   Managing lists of supported currencies or countries for a specific gateway if this needs to be dynamic beyond the gateway's own capabilities.

## Example Endpoints (Conceptual)

### 1. List Gateway Configurations

*   **Endpoint**: `GET /v1/admin/gateways/configurations`
*   **Purpose**: To retrieve a list of currently configured payment gateways and their non-sensitive settings.
*   **Authentication**: Required (Admin role).
*   **Success Response (200 OK)**:
    ```json
    {
      "data": [
        {
          "gatewayName": "STRIPE",
          "displayName": "Stripe Payments",
          "isEnabled": true,
          "supportedCurrencies": ["USD", "EUR", "GBP"],
          "defaultPaymentMethods": ["card"],
          "metadata": {
            "priority": 1
          }
        },
        {
          "gatewayName": "PAYPAL",
          "displayName": "PayPal Express Checkout",
          "isEnabled": false,
          "supportedCurrencies": ["USD", "EUR"],
          "metadata": {
            "priority": 2
          }
        }
      ]
    }
    ```

### 2. Get Specific Gateway Configuration

*   **Endpoint**: `GET /v1/admin/gateways/configurations/{gatewayName}`
*   **Purpose**: To retrieve the non-sensitive configuration for a specific payment gateway.
*   **Authentication**: Required (Admin role).
*   **Success Response (200 OK)**: (Similar to one object from the list response above).
*   **Error Responses**: `404 Not Found` if gateway config doesn't exist.

### 3. Update Gateway Configuration

*   **Endpoint**: `PUT /v1/admin/gateways/configurations/{gatewayName}`
*   **Purpose**: To update non-sensitive configuration parameters for a specific gateway.
*   **Authentication**: Required (Admin role).
*   **Request Body**:
    ```json
    {
      "displayName": "Stripe Credit Cards",
      "isEnabled": true,
      "supportedCurrencies": ["USD", "EUR", "GBP", "CAD"],
      "metadata": {
        "priority": 1,
        "contact": "finance-ops@example.com"
      }
    }
    ```
*   **Success Response (200 OK)**: Returns the updated gateway configuration object.
*   **Error Responses**: `400 Bad Request` (validation errors), `404 Not Found`.

## Security and Design Considerations

*   **Strictly Non-Sensitive Data**: Reiterate that API keys, webhook secrets, passwords, or any other sensitive credentials must **never** be part of these API request/response payloads or be manageable through these endpoints.
*   **Admin Only**: Access must be tightly restricted to highly privileged administrative roles.
*   **Audit Logging**: All changes made through these endpoints must be meticulously audited (who changed what, when, old value, new value).
*   **Impact Assessment**: Changes to gateway configurations can have significant impacts on payment processing. Clear validation and potentially a review process might be needed before changes take effect.
*   **Alternative**: Often, such configurations are managed via deployment configuration files or environment variables and updated through a standard deployment process, which can be more controlled and auditable than dynamic API-based changes for infrastructure-level settings.
*   **Restart Requirement**: If changes made via these APIs require an application restart to take effect (e.g., if gateway clients are initialized at startup), this needs to be clearly understood and managed.

**Conclusion**: While these endpoints *could* offer some operational flexibility for non-sensitive settings, the benefits must be weighed against the complexity and potential risks. Managing most gateway configurations as part of the deployment artifacts is often a safer and more robust approach. If implemented, the scope must be very narrowly defined to exclude any sensitive information.
