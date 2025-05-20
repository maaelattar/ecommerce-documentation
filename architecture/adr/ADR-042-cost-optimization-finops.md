# ADR: Cost Optimization & FinOps

*   **Status:** Proposed
*   **Date:** 2025-05-12
*   **Deciders:** [Architecture Team, Finance]
*   **Consulted:** [DevOps, Product Owners]
*   **Informed:** [All Engineering Teams]

## Context and Problem Statement

Cloud costs can grow rapidly with scale. Without proactive cost management, the platform risks overspending, budget overruns, and inefficient resource usage. A structured approach to cost optimization and FinOps is needed.

## Decision Drivers
*   Cost visibility and accountability
*   Sustainable growth and resource efficiency
*   Budget compliance and forecasting
*   Enabling business agility

## Considered Options

### Option 1: Implement FinOps Practices and Tooling
*   Description: Tag resources, use cloud-native cost monitoring, set budgets/alerts, and regularly review resource usage.
*   Pros:
    *   Improved cost visibility
    *   Enables chargeback/showback
    *   Supports proactive optimization
*   Cons:
    *   Requires process and tooling setup
    *   Ongoing effort for reviews

### Option 2: Ad-hoc Cost Management
*   Description: Monitor and optimize costs only when issues arise.
*   Pros:
    *   Minimal initial effort
    *   No new processes required
*   Cons:
    *   High risk of overspending
    *   Lack of accountability
    *   Harder to forecast and control costs

## Decision Outcome

**Chosen Option:** Implement FinOps Practices and Tooling

**Reasoning:**
A proactive, structured approach to cost management ensures sustainable growth, prevents budget overruns, and enables teams to make informed trade-offs. The benefits of visibility and control outweigh the setup and maintenance effort.

### Key FinOps Practices to Implement

#### 1. Resource Tagging Strategy

Effective resource tagging is fundamental to successful cost management and FinOps. It enables accurate cost allocation, granular reporting, automation, and targeted optimization efforts.

**A. Purpose of Tagging:**
*   **Cost Allocation & Tracking:** Assign costs to specific projects, teams, services, environments, or cost centers.
*   **Budgeting & Forecasting:** Provide data for accurate budget creation and forecasting.
*   **Security & Compliance:** Identify resources subject to specific security or compliance requirements.
*   **Automation:** Enable automated actions based on tags (e.g., automated start/stop, backup policies).
*   **Resource Grouping & Organization:** Logically group resources for management and reporting.

**B. Mandatory Tags:**
These tags MUST be applied to all provisionable AWS resources where tagging is supported.

*   `name`: (String) A human-readable name for the resource (e.g., `auth-service-prod-instance`, `product-db-staging`).
    *   *Value:* Descriptive name.
*   `environment`: (String) The operational environment of the resource.
    *   *Value:* `dev`, `staging`, `qa`, `uat`, `prod`, `shared-services`.
*   `service-identifier`: (String) A unique identifier for the microservice, application, or workload the resource belongs to. (e.g., `auth-service`, `product-catalog`, `order-processing`). This aligns with service discovery (ADR-015).
    *   *Value:* Standardized service name.
*   `team-owner`: (String) The development or operations team responsible for managing the resource.
    *   *Value:* Team name (e.g., `backend-platform-team`, `checkout-squad`).
*   `cost-center`: (String) The business unit or cost center to which the resource's costs should be attributed.
    *   *Value:* Alphanumeric cost center code provided by Finance.
*   `automation-excluded`: (Boolean) Indicates if a resource should be excluded from automated actions (e.g., scheduled shutdowns, automated patching). Default to `false`.
    *   *Value:* `true` or `false`.

**C. Recommended Tags:**
These tags provide additional valuable context and are highly recommended.

*   `project`: (String) The specific project or initiative the resource supports, if applicable.
    *   *Value:* Project name or code.
*   `version`: (String) The version of the application or service deployed on the resource.
    *   *Value:* Semantic version (e.g., `1.2.3`).
*   `data-sensitivity`: (String) Classification of data stored or processed by the resource.
    *   *Value:* `public`, `internal`, `confidential`, `highly-confidential`.
*   `backup-policy`: (String) Indicates the backup policy applied to the resource.
    *   *Value:* Policy name (e.g., `daily-7day-retention`, `none`).
*   `patch-group`: (String) The patch group the resource belongs to for automated patching.
    *   *Value:* Patch group identifier.

**D. Tagging Conventions:**
*   **Standardization:** All tag keys and values will be lowercase, using hyphens to separate words (e.g., `team-owner`, `cost-center`, `auth-service`). This simplifies querying, automation, and ensures consistency.
*   **Naming:** Use clear, concise, and descriptive names for tags.
*   **Restricted Values:** For tags with a predefined set of allowed values (e.g., `environment`, `data-sensitivity`), these values will be documented and their use enforced through policy or validation where possible.

**E. Tagging Enforcement & Governance:**
*   **Primary Enforcement:** Leverage AWS Service Control Policies (SCPs) at the AWS Organization level to enforce mandatory tags during resource creation for supported services (e.g., `tag:RequireTagKeys`, `tag:RequireTagValues`).
*   **Secondary Enforcement:** Implement AWS Config rules to detect non-compliant resources (missing or incorrect tags) and flag them for remediation. These rules can also trigger automated notifications or remediation actions.
*   **IaC Integration:** Tagging policies will be embedded within Infrastructure as Code (IaC) templates (e.g., Terraform, CloudFormation modules and providers). CI/CD pipelines will include steps to validate tags against the defined policy before deployment.
*   **Manual Tagging:** Discouraged for new resources but may be necessary for existing, untagged resources. A process for regular audit and remediation of manually tagged or non-compliant resources will be established.
*   **Governance:** The Cloud Governance Team (or a designated FinOps role/team, to be defined in ADR-XXX Organization and Roles) will be responsible for defining, maintaining, and evolving the tagging strategy, including approving new tags or changes to existing ones. Regular audits of tagging compliance and effectiveness will be performed. Documentation for the current tagging strategy, including allowed values for specific tags, will be maintained in a central location.

#### 2. Cloud-Native Cost Monitoring Tools & Setup

Leveraging AWS-native tools is essential for effective cost monitoring, analysis, and control. The following tools will be foundational to our FinOps practice:

**A. AWS Cost Explorer:**
*   **Purpose:** Visualize, understand, and manage AWS costs and usage over time. Enables ad-hoc analysis, identification of cost trends, and uncovering cost drivers.
*   **Key Reports & Views:**
    *   **Monthly Costs by Service:** Standard view to track spending across different AWS services.
    *   **Monthly Costs by Linked Account:** Useful in multi-account setups.
    *   **Daily Cost Trends:** Monitor for unexpected spikes.
    *   **Costs by Tags:** (Leveraging our Tagging Strategy - see section 1) Critical for allocating costs to services, teams, environments, and cost centers. Saved reports will be created for key tags like `service-identifier`, `team-owner`, and `cost-center`.
    *   **Reserved Instance (RI) / Savings Plans Utilization & Coverage Reports:** To ensure optimal use of commitment-based discounts.
*   **Rightsizing Recommendations:** Regularly review EC2 rightsizing recommendations within Cost Explorer to identify over-provisioned instances.
*   **Access:** Appropriate IAM permissions will be granted to relevant teams (Finance, DevOps, Engineering Leads) to access Cost Explorer and specific saved reports.

**B. AWS Budgets:**
*   **Purpose:** Set custom budgets to track costs against defined amounts and receive alerts when thresholds are breached or forecasted to be breached. Enables proactive cost control.
*   **Types of Budgets to Implement:**
    *   **Overall Monthly/Quarterly AWS Budget:** A high-level budget for total AWS spend.
    *   **Service-Specific Budgets:** For high-spend services (e.g., EC2, RDS, S3, Data Transfer) to monitor their individual growth.
    *   **Tag-Based Budgets:** Budgets based on key tags like `cost-center` or `service-identifier` to track spending for specific business units or applications.
    *   **RI/Savings Plans Utilization Budgets:** To alert if utilization drops below target thresholds (e.g., 90%).
*   **Alerting:**
    *   Configure alerts for both actual and forecasted budget overruns (e.g., at 50%, 75%, 90%, 100% of budget).
    *   Notifications will be sent to designated email distribution lists (e.g., `finops-alerts@example.com`, team-specific lists) and potentially integrated with chat applications (e.g., Slack).

**C. AWS Cost and Usage Report (CUR):**
*   **Purpose:** Provides the most comprehensive set of cost and usage data. Serves as the single source of truth for detailed analysis, and can be integrated with business intelligence (BI) tools.
*   **Setup:**
    *   CUR will be configured to deliver hourly or daily reports to a designated S3 bucket in Parquet or CSV format.
    *   Resource IDs and User-Defined Cost Allocation Tags (from our Tagging Strategy) will be included in the report.
*   **Data Analysis:**
    *   **Amazon Athena:** Use Athena to query CUR data directly in S3 for custom analysis and reporting.
    *   **Amazon QuickSight (or other BI tools):** Ingest CUR data into QuickSight or a preferred BI tool to create advanced dashboards and visualizations, potentially correlating cost data with business or operational metrics.
*   **Data Retention:** CUR data in S3 will be managed with appropriate lifecycle policies.

**D. General Practices:**
*   **Regular Review:** Establish a cadence for reviewing reports from Cost Explorer, status of Budgets, and insights from CUR analysis (to be detailed in "Cost Review Cadence & Stakeholders" section).
*   **Training:** Provide training to relevant personnel on how to use these AWS cost management tools effectively.
*   **Automation:** Explore opportunities to automate the generation of specific reports or the response to certain budget alerts.

#### 3. Initial Optimization Techniques to Focus On

While comprehensive cost optimization is an ongoing process, the following techniques will be prioritized initially to achieve quick wins and establish good practices:

**A. Rightsizing Resources:**
*   **Description:** Regularly analyze resource utilization (e.g., EC2 instances, RDS instances, EBS volumes) using tools like AWS Cost Explorer's rightsizing recommendations, AWS Compute Optimizer, or CloudWatch metrics. Adjust instance types and sizes to match actual workload demands, avoiding over-provisioning.
*   **Focus Areas:** EC2 instances, RDS instances, ElastiCache nodes, OpenSearch/Elasticsearch domains.

**B. Identifying and Eliminating Idle/Unused Resources:**
*   **Description:** Implement processes to detect and decommission resources that are no longer needed. This includes:
    *   Unattached EBS volumes.
    *   Idle load balancers.
    *   Unused Elastic IP addresses.
    *   Old snapshots or AMIs.
    *   Empty S3 buckets (unless intentionally kept).
    *   Lingering resources in development or test environments.
*   **Tools:** AWS Trusted Advisor (Idle Load Balancers, Unassociated Elastic IPs), custom scripts, Cost Explorer (filtering for zero-traffic resources).

**C. Implementing Storage Tiering:**
*   **Description:** Utilize appropriate storage tiers based on access frequency and performance requirements to reduce costs.
    *   **Amazon S3:** Transition data to S3 Intelligent-Tiering, S3 Standard-Infrequent Access (S3 Standard-IA), S3 One Zone-IA, S3 Glacier Instant Retrieval, S3 Glacier Flexible Retrieval, or S3 Glacier Deep Archive based on data lifecycle policies.
    *   **Amazon EBS:** Use appropriate volume types (e.g., gp3 for general purpose, io2 Block Express for high performance, sc1/st1 for throughput-intensive cold storage).
*   **Focus:** Application logs, backups, historical data, media assets.

**D. Leveraging Commitment-Based Discounts (Reserved Instances & Savings Plans):**
*   **Description:** For stable, predictable workloads, utilize AWS Reserved Instances (RIs) for services like EC2 and RDS, and Savings Plans (Compute, EC2 Instance, SageMaker) to achieve significant discounts compared to on-demand pricing.
*   **Strategy:** Start with shorter-term commitments (e.g., 1-year, no upfront) for a portion of the baseline workload, gradually increasing commitment as confidence in workload predictability grows. Regularly analyze utilization and coverage reports in AWS Cost Explorer.

**E. Scheduling Non-Production Resources:**
*   **Description:** Automatically stop or scale down non-production resources (e.g., development, staging, QA environments) during non-business hours (evenings, weekends) to reduce costs.
*   **Tools:** AWS Instance Scheduler, custom Lambda functions, or third-party tools. Tags (e.g., `environment`, `schedule-on-off`) will be used to identify target resources.

**F. Optimizing Data Transfer Costs:**
*   **Description:** Analyze data transfer patterns to identify and reduce unnecessary costs.
    *   Minimize data transfer across AWS Regions or Availability Zones where possible.
    *   Utilize Amazon CloudFront (CDN) to cache content closer to users and reduce data transfer out (DTO) costs from origin servers (e.g., S3, EC2).
    *   Compress data before transfer.
*   **Tools:** AWS Cost Explorer (filter by usage type group "Data Transfer"), S3/CloudFront access logs.

**G. Database Optimization:**
*   **Description:** Regularly review database performance and costs.
    *   Ensure appropriate instance sizing (as per rightsizing).
    *   Optimize queries and indexing to improve efficiency and potentially reduce the need for larger instances.
    *   Evaluate options like Aurora Serverless v2 for intermittent or unpredictable workloads.
    *   Implement appropriate backup and retention policies to manage storage costs.

#### 4. Process for Budget Setting and Alerting

A structured process for setting budgets and managing alerts is crucial for proactive cost management and accountability.

**A. Budget Planning and Definition:**
*   **Inputs & Collaboration:**
    *   Budgets will be planned collaboratively, involving Finance, Engineering Leads, Product Owners, and the Cloud Governance/FinOps team.
    *   Inputs will include:
        *   Historical spending patterns (from AWS Cost Explorer and CUR).
        *   Business forecasts and strategic initiatives (e.g., new product launches, expected user growth).
        *   Planned infrastructure changes or new service deployments.
        *   Resource utilization forecasts.
*   **Granularity & Scope:**
    *   **Overall AWS Budget:** An organization-wide budget set (e.g., quarterly or annually) by Finance in consultation with key stakeholders.
    *   **Team/Cost Center Budgets:** Budgets will be established for individual teams or cost centers, aligned with their anticipated resource consumption. This will heavily leverage the `cost-center` and `team-owner` tags.
    *   **Project/Service Budgets:** For significant projects or specific high-cost services, dedicated budgets may be created using relevant tags (e.g., `project`, `service-identifier`).
*   **Budget Cycle:** Budgets will typically be set on a quarterly basis, with a review and potential adjustment monthly. An annual high-level forecast will also be maintained.

**B. Budget Implementation in AWS Budgets:**
*   **Tool:** AWS Budgets will be the primary tool for implementing and tracking these defined financial limits.
*   **Configuration:**
    *   Budgets will be configured with clear names, periods (monthly, quarterly, annually), and budgeted amounts.
    *   Filters will be applied based on linked accounts, services, and, critically, cost allocation tags (`cost-center`, `team-owner`, `project`, `service-identifier`).
    *   Both **cost budgets** (tracking actual spend) and **usage budgets** (tracking specific resource consumption, e.g., EC2 hours, S3 storage) will be utilized where appropriate.
    *   **RI/Savings Plan utilization and coverage budgets** will also be configured to monitor commitment efficiency.

**C. Alerting Strategy:**
*   **Thresholds:**
    *   Alerts will be configured for both **actual** and **forecasted** costs exceeding budget thresholds.
    *   Standard thresholds will be set at 50%, 75%, 90%, and 100% of the budgeted amount. Additional thresholds may be configured based on specific needs.
*   **Notification Channels:**
    *   Alerts will be sent via email to designated distribution lists (e.g., `finops-alerts@example.com`, `team-X-budget-alerts@example.com`).
    *   Integration with a centralized messaging platform (e.g., Slack channel like `#finops-alerts`) will be implemented for broader visibility and quicker response.
*   **Recipients & Escalation:**
    *   **Team/Cost Center Budget Alerts:** Primarily sent to the respective team lead/manager and relevant engineering staff.
    *   **Project/Service Budget Alerts:** Sent to the project owner and key technical contributors.
    *   **Overall AWS Budget Alerts:** Sent to Finance, Head of Engineering, and Cloud Governance/FinOps team.
    *   An escalation path will be defined if budget thresholds are repeatedly breached or if critical alerts are not acknowledged.

**D. Budget Review and Adjustment:**
*   **Cadence:**
    *   A formal budget vs. actuals review will occur monthly for team/cost center and project/service budgets.
    *   The overall AWS budget will be reviewed quarterly by senior leadership.
*   **Process:**
    *   The Cloud Governance/FinOps team will prepare and distribute budget performance reports using AWS Cost Explorer and AWS Budgets data.
    *   Review meetings will involve discussing variances, understanding root causes (e.g., unexpected usage, new initiatives, efficiency gains), and identifying corrective actions or necessary budget adjustments.
*   **Budget Adjustments:**
    *   Requests for budget adjustments must be justified and will follow a defined approval process, typically involving the budget owner, Finance, and the Cloud Governance/FinOps team.
    *   Adjustments will be reflected in AWS Budgets promptly.

#### 5. Cost Review Cadence & Stakeholders

Establishing a regular cadence for cost reviews with defined stakeholders is critical for maintaining cost awareness, driving accountability, and ensuring continuous optimization.

**A. Daily/Weekly Operational Check-ins (DevOps/Engineering Teams):**
*   **Cadence:** Daily or as-needed for specific services; weekly for broader team operational reviews.
*   **Stakeholders:** Engineering Leads, DevOps Team, relevant SREs or senior engineers.
*   **Purpose:**
    *   Monitor for immediate cost anomalies or unexpected spikes in service usage (using AWS Cost Explorer daily trends, CloudWatch alarms, or specific service dashboards).
    *   Review alerts from AWS Budgets for specific services or projects.
    *   Discuss any recent deployments or changes that might have cost implications.
    *   Quickly identify and address any operational issues leading to cost inefficiencies.
*   **Outputs:** Immediate remediation actions, JIRA tickets for follow-up optimization tasks.

**B. Monthly Team/Cost Center Budget Review:**
*   **Cadence:** Monthly.
*   **Stakeholders:** Team Leads/Managers, Product Owners, representatives from the Cloud Governance/FinOps team, key engineers from the team.
*   **Purpose:**
    *   Review actual spend against the team's/cost center's budget for the previous month (using reports from AWS Budgets and Cost Explorer).
    *   Analyze significant variances and understand their drivers.
    *   Discuss upcoming initiatives and their potential cost impact.
    *   Identify and prioritize cost optimization opportunities within the team's scope.
    *   Review progress on previously identified optimization tasks.
*   **Outputs:** Action items for cost optimization, updates to forecasts, potential budget adjustment requests.

**C. Monthly FinOps Working Group Meeting:**
*   **Cadence:** Monthly.
*   **Stakeholders:** Cloud Governance/FinOps Team lead, representatives from Finance, key Engineering Leads (representing different domains), Product Management representatives.
*   **Purpose:**
    *   Review overall AWS spend trends and performance against the global budget.
    *   Discuss cross-cutting optimization opportunities and challenges.
    *   Review the effectiveness of existing FinOps processes (tagging, budgeting, reporting).
    *   Share best practices and learnings across teams.
    *   Prioritize larger optimization initiatives or tooling changes.
    *   Review RI/Savings Plan utilization and coverage, and plan for future purchases or modifications.
*   **Outputs:** Recommendations for process improvements, strategic optimization initiatives, updates to RI/SP strategy, reports for senior leadership.

**D. Quarterly Business Review (QBR) - Cost Management Focus:**
*   **Cadence:** Quarterly.
*   **Stakeholders:** Senior Leadership (Head of Engineering, CTO, CFO), Finance leadership, Cloud Governance/FinOps Team lead, key Engineering Directors/VPs.
*   **Purpose:**
    *   Review overall cloud spend for the quarter against strategic business objectives and annual budget.
    *   Assess the financial impact of major projects or product lines.
    *   Evaluate the ROI of cloud investments.
    *   Discuss long-term cost trends and forecasting.
    *   Make strategic decisions regarding cloud investment, major architectural changes for cost, or significant FinOps process changes.
*   **Outputs:** Strategic directives for cost management, approval for major optimization projects or budget realignments.

**E. Action Item Tracking:**
*   All identified optimization opportunities, issues, and action items from these reviews will be tracked in a centralized system (e.g., JIRA project dedicated to FinOps/Cost Optimization) with assigned owners and due dates. Progress will be monitored in subsequent review meetings.

### Positive Consequences
*   Improved cost visibility and accountability
*   Reduced waste and unnecessary spend
*   Better forecasting and planning

### Negative Consequences (and Mitigations)
*   Ongoing process overhead (Mitigation: Automate reporting and reviews)
*   Requires cultural change (Mitigation: Provide training and incentives)

### Neutral Consequences
*   May require changes to resource provisioning workflows

## Links (Optional)
*   https://www.finops.org/
*   https://aws.amazon.com/dlm/
*   https://cloud.google.com/billing

## Future Considerations (Optional)
*   Integrate cost data with business KPIs
*   Expand automation for cost optimization

## Rejection Criteria (Optional)
*   If FinOps overhead exceeds benefits, reconsider or simplify approach
